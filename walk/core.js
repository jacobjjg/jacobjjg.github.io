/* Pure tracking logic: no DOM, so it can be unit-tested in Node. */
(function (root) {
  'use strict';

  const EARTH_R = 6371008.8;
  const rad = (d) => (d * Math.PI) / 180;

  function haversine(lat1, lon1, lat2, lon2) {
    const dLat = rad(lat2 - lat1);
    const dLon = rad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 2 * EARTH_R * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  /**
   * Counts steps from raw accelerometer samples (m/s², gravity included).
   *
   * The magnitude of the acceleration vector is used so phone orientation
   * doesn't matter. Gravity is removed with a slow high-pass, jitter with a
   * fast low-pass, and each remaining peak that is big enough, far enough from
   * the previous one, and separated from it by a dip counts as a candidate.
   * Candidates only become steps once several arrive in a steady rhythm, which
   * is what keeps picking the phone up or shifting it from adding steps.
   */
  class StepDetector {
    constructor() {
      this.steps = 0;
      this.reset();
    }

    /** Clears filter state but keeps the step total. */
    reset() {
      this.lastT = null;
      this.gravity = 0;
      this.s0 = 0;
      this.s1 = 0;
      this.t1 = 0;
      this.lastPeakT = -Infinity;
      this.wentLow = true;
      this.peakAvg = 1.5;
      this.run = 0;
      this.confirmed = false;
    }

    /** Feed one sample; returns how many steps it added (usually 0 or 1). */
    push(t, x, y, z) {
      const mag = Math.hypot(x, y, z);
      if (!Number.isFinite(mag)) return 0;
      if (this.lastT === null) {
        this.lastT = t;
        this.gravity = mag;
        this.t1 = t;
        return 0;
      }
      const dt = (t - this.lastT) / 1000;
      if (dt <= 0) return 0;
      this.lastT = t;
      if (dt > 0.5) {
        // Sensor stream was interrupted; old filter state is meaningless.
        const steps = this.steps;
        this.reset();
        this.steps = steps;
        this.lastT = t;
        this.gravity = mag;
        this.t1 = t;
        return 0;
      }

      this.gravity += (dt / (1.0 + dt)) * (mag - this.gravity);
      const s = this.s1 + (dt / (0.05 + dt)) * (mag - this.gravity - this.s1);

      const thr = Math.max(0.7, 0.35 * this.peakAvg);
      let added = 0;

      // s1 is a local maximum if it rose from s0 and s did not exceed it.
      if (this.s1 > this.s0 && this.s1 >= s && this.s1 > thr && this.wentLow) {
        const gap = this.t1 - this.lastPeakT;
        if (gap >= 250) {
          if (gap > 2000) {
            this.run = 0;
            this.confirmed = false;
            this.peakAvg = 1.5;
          }
          this.lastPeakT = this.t1;
          this.wentLow = false;
          this.peakAvg = 0.8 * this.peakAvg + 0.2 * this.s1;
          this.run++;
          if (this.confirmed) {
            added = 1;
          } else if (this.run >= 6) {
            this.confirmed = true;
            added = this.run;
          }
        }
      }
      if (s < -0.2 * thr) this.wentLow = true;

      this.s0 = this.s1;
      this.s1 = s;
      this.t1 = t;
      this.steps += added;
      return added;
    }
  }

  const MAX_ACCURACY = 35; // metres; worse fixes are ignored
  const ANCHOR_ACCURACY = 25; // first point of a segment should be decent
  const MAX_SPEED = 8; // m/s; faster than this on foot is a GPS jump
  const WALK_Q = 3; // m/s; how fast a walker's position can plausibly change

  /**
   * Turns a stream of GPS fixes into a route and a distance.
   * Points are stored as [lat, lon, timeMs, cumulativeMetres, altitude|null, segment].
   */
  class RouteTracker {
    constructor(saved) {
      this.points = [];
      this.distance = 0;
      this.gain = 0;
      this.loss = 0;
      this.segment = 0;
      this.anchor = null; // last accepted fix in the current segment
      this.weak = 0;
      this.altSmooth = null;
      this.altRef = null;
      if (saved) {
        this.points = saved.points || [];
        this.distance = saved.distance || 0;
        this.gain = saved.gain || 0;
        this.loss = saved.loss || 0;
        const last = this.points[this.points.length - 1];
        this.segment = last ? last[5] + 1 : 0;
      }
    }

    /** Start a new segment (after a pause) so the gap adds no distance. */
    breakSegment() {
      if (this.anchor) this.segment++;
      this.anchor = null;
      this.weak = 0;
      this.altSmooth = null;
      this.altRef = null;
    }

    /**
     * @param fix {lat, lon, acc, alt, altAcc, t}
     * @param moving true/false if a step sensor knows, null if unknown
     * @returns 'point' | 'weak' | 'jump' | 'still'
     */
    add(fix, moving) {
      const acc = fix.acc;
      if (acc == null || !(acc <= MAX_ACCURACY)) {
        this.weak++;
        return 'weak';
      }
      if (!this.anchor) {
        if (acc > ANCHOR_ACCURACY && this.weak < 6) {
          this.weak++;
          return 'weak';
        }
        this.klat = fix.lat;
        this.klon = fix.lon;
        this.kvar = acc * acc;
        this.kt = fix.t;
        this._accept(fix, 0);
        return 'point';
      }
      const a = this.anchor;
      const dt = (fix.t - a.t) / 1000;
      const kdt = (fix.t - this.kt) / 1000;
      if (kdt <= 0) return 'still';
      const raw = haversine(this.klat, this.klon, fix.lat, fix.lon);
      if (raw > acc && raw / kdt > MAX_SPEED) return 'jump';

      // Kalman-smooth the position: trust each fix in proportion to its
      // reported accuracy, so second-to-second jitter doesn't become distance.
      this.kvar += kdt * WALK_Q * WALK_Q;
      const k = this.kvar / (this.kvar + acc * acc);
      this.klat += k * (fix.lat - this.klat);
      this.klon += k * (fix.lon - this.klon);
      this.kvar *= 1 - k;
      this.kt = fix.t;

      // Movement must clearly exceed the noise. While the step sensor says
      // we're standing still, demand much more so GPS drift isn't counted.
      const d = haversine(a.lat, a.lon, this.klat, this.klon);
      let need = Math.max(5, 0.5 * Math.min(acc, a.acc));
      if (moving === false) need = Math.max(15, acc);
      if (d < need || dt <= 0) return 'still';

      this._accept({ ...fix, lat: this.klat, lon: this.klon }, d);
      return 'point';
    }

    _accept(fix, d) {
      this.distance += d;
      let alt = null;
      if (fix.alt != null && Number.isFinite(fix.alt) && (fix.altAcc == null || fix.altAcc <= 20)) {
        this.altSmooth = this.altSmooth == null ? fix.alt : this.altSmooth + 0.3 * (fix.alt - this.altSmooth);
        alt = Math.round(this.altSmooth * 10) / 10;
        if (this.altRef == null) this.altRef = this.altSmooth;
        const diff = this.altSmooth - this.altRef;
        if (diff >= 3) {
          this.gain += diff;
          this.altRef = this.altSmooth;
        } else if (diff <= -3) {
          this.loss -= diff;
          this.altRef = this.altSmooth;
        }
      }
      this.anchor = { lat: fix.lat, lon: fix.lon, acc: fix.acc, t: fix.t };
      this.points.push([
        Math.round(fix.lat * 1e6) / 1e6,
        Math.round(fix.lon * 1e6) / 1e6,
        Math.round(fix.t),
        Math.round(this.distance * 10) / 10,
        alt,
        this.segment,
      ]);
    }

    /** Cumulative distance at wall-clock time t (linear interpolation). */
    distanceAt(t) {
      return distanceAt(this.points, t, this.distance);
    }
  }

  function distanceAt(points, t, total) {
    const n = points.length;
    if (!n || t <= points[0][2]) return 0;
    if (t >= points[n - 1][2]) return total == null ? points[n - 1][3] : total;
    let lo = 0;
    let hi = n - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (points[mid][2] <= t) lo = mid;
      else hi = mid;
    }
    const a = points[lo];
    const b = points[hi];
    const f = b[2] === a[2] ? 0 : (t - a[2]) / (b[2] - a[2]);
    return a[3] + f * (b[3] - a[3]);
  }

  /** Time for each full unit of distance, skipping paused gaps between segments. */
  function splits(points, unitMetres) {
    const out = [];
    let elapsed = 0;
    let lastMark = 0;
    let next = unitMetres;
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1];
      const b = points[i];
      if (a[5] !== b[5]) continue;
      const dt = b[2] - a[2];
      const dd = b[3] - a[3];
      while (dd > 0 && b[3] >= next) {
        const at = elapsed + (dt * (next - a[3])) / dd;
        out.push(at - lastMark);
        lastMark = at;
        next += unitMetres;
      }
      elapsed += dt;
    }
    return out;
  }

  /** ACSM walking equation: gross kcal for a body mass, active time and distance. */
  function calories(weightKg, activeMs, metres) {
    const minutes = activeMs / 60000;
    return (weightKg / 200) * (3.5 * minutes + 0.1 * metres);
  }

  function strideFromHeight(heightCm) {
    return (heightCm * 0.414) / 100;
  }

  function toGpx(walk) {
    const esc = (s) => String(s).replace(/[<>&"]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c]));
    const segs = [];
    let cur = null;
    let seg = null;
    for (const p of walk.points) {
      if (p[5] !== seg) {
        seg = p[5];
        cur = [];
        segs.push(cur);
      }
      cur.push(
        `      <trkpt lat="${p[0]}" lon="${p[1]}">` +
          (p[4] != null ? `<ele>${p[4]}</ele>` : '') +
          `<time>${new Date(p[2]).toISOString()}</time></trkpt>`
      );
    }
    return (
      '<?xml version="1.0" encoding="UTF-8"?>\n' +
      '<gpx version="1.1" creator="Walk Tracker" xmlns="http://www.topografix.com/GPX/1/1">\n' +
      `  <metadata><time>${new Date(walk.start).toISOString()}</time></metadata>\n` +
      `  <trk>\n    <name>${esc(walk.name || 'Walk')}</name>\n    <type>walking</type>\n` +
      segs.map((s) => `    <trkseg>\n${s.join('\n')}\n    </trkseg>\n`).join('') +
      '  </trk>\n</gpx>\n'
    );
  }

  const api = { haversine, StepDetector, RouteTracker, distanceAt, splits, calories, strideFromHeight, toGpx };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.WalkCore = api;
})(typeof self !== 'undefined' ? self : this);
