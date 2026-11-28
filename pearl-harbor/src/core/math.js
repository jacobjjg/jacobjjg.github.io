// Small math toolkit shared by every system.  Everything here is deterministic (no Math.random).
import * as THREE from 'three';

export const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
export const saturate = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
export const lerp = (a, b, t) => a + (b - a) * t;
export const invLerp = (a, b, x) => (b === a ? 0 : (x - a) / (b - a));
export const remap = (x, a, b, c, d) => c + (d - c) * saturate(invLerp(a, b, x));
export const smoothstep = (a, b, x) => { const t = saturate(invLerp(a, b, x)); return t * t * (3 - 2 * t); };
export const smootherstep = (a, b, x) => { const t = saturate(invLerp(a, b, x)); return t * t * t * (t * (t * 6 - 15) + 10); };
export const mod = (a, n) => ((a % n) + n) % n;
/** shortest signed angular difference b - a in degrees, in (-180, 180]. */
export const angleDiff = (a, b) => { let d = mod(b - a + 180, 360) - 180; return d === -180 ? 180 : d; };
export const lerpAngle = (a, b, t) => a + angleDiff(a, b) * t;
/** frame-rate independent exponential approach. */
export const damp = (current, target, lambda, dt) => lerp(current, target, 1 - Math.exp(-lambda * dt));

export const ease = {
  linear: (t) => t,
  inQuad: (t) => t * t,
  outQuad: (t) => t * (2 - t),
  inOutQuad: (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
  inCubic: (t) => t * t * t,
  outCubic: (t) => 1 - Math.pow(1 - t, 3),
  inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
  outExpo: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inOutQuint: (t) => (t < 0.5 ? 16 * t ** 5 : 1 - Math.pow(-2 * t + 2, 5) / 2),
};

// ---- deterministic randomness ------------------------------------------------------------
/** 32-bit string hash (FNV-1a). */
export function hashString(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193); }
  return h >>> 0;
}
/** mulberry32 PRNG -> function returning floats in [0,1).  Seed with a number or a string. */
export function rng(seed) {
  let a = typeof seed === 'string' ? hashString(seed) : (seed >>> 0);
  const f = () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  f.range = (lo, hi) => lo + (hi - lo) * f();
  f.int = (lo, hi) => Math.floor(lo + (hi - lo + 1) * f());
  f.pick = (arr) => arr[Math.floor(f() * arr.length)];
  f.sign = () => (f() < 0.5 ? -1 : 1);
  f.gauss = () => { let u = 0; for (let i = 0; i < 6; i++) u += f(); return (u - 3) / 1.0; }; // ~N(0, 0.71)
  return f;
}
/** stateless hash -> [0,1) from up to three integers. */
export function hash3(x, y = 0, z = 0) {
  let h = Math.imul(x | 0, 374761393) ^ Math.imul(y | 0, 668265263) ^ Math.imul(z | 0, 2147483647);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

// ---- keyframe track ---------------------------------------------------------------------
/**
 * Track: time-keyed values with interpolation.  Values may be numbers or equal-length arrays.
 *   const list = new Track([[T('07:56'), 0], [T('08:08'), 150]], 'smooth');   list.at(t)
 * modes: 'linear' | 'smooth' (smoothstep between keys) | 'step' (hold previous key)
 * Clamps outside the key range.
 */
export class Track {
  constructor(keys = [], mode = 'linear') {
    this.mode = mode;
    this.keys = keys.map((k) => (Array.isArray(k) ? { t: k[0], v: k[1] } : k)).sort((a, b) => a.t - b.t);
    this._i = 0;
    this._isArr = this.keys.length > 0 && Array.isArray(this.keys[0].v);
    this._out = this._isArr ? new Array(this.keys[0].v.length) : null;
  }
  get start() { return this.keys.length ? this.keys[0].t : 0; }
  get end() { return this.keys.length ? this.keys[this.keys.length - 1].t : 0; }
  _find(t) {
    const k = this.keys; let i = this._i;
    if (i >= k.length - 1) i = Math.max(0, k.length - 2);
    if (k[i].t <= t && t < k[i + 1].t) return i;
    let lo = 0, hi = k.length - 2;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (k[mid].t <= t) lo = mid; else hi = mid - 1; }
    return (this._i = lo);
  }
  at(t, out) {
    const k = this.keys;
    if (k.length === 0) return 0;
    if (k.length === 1 || t <= k[0].t) return this._copy(k[0].v, out);
    if (t >= k[k.length - 1].t) return this._copy(k[k.length - 1].v, out);
    const i = this._find(t), a = k[i], b = k[i + 1];
    if (this.mode === 'step') return this._copy(a.v, out);
    let u = (t - a.t) / (b.t - a.t);
    if (this.mode === 'smooth') u = u * u * (3 - 2 * u);
    if (!this._isArr) return a.v + (b.v - a.v) * u;
    const o = out || this._out;
    for (let j = 0; j < a.v.length; j++) o[j] = a.v[j] + (b.v[j] - a.v[j]) * u;
    return o;
  }
  _copy(v, out) {
    if (!this._isArr) return v;
    const o = out || this._out;
    for (let j = 0; j < v.length; j++) o[j] = v[j];
    return o;
  }
}

// ---- timed path -------------------------------------------------------------------------
/**
 * TimedPath: a smooth C1 curve through time-stamped 3D waypoints (cubic Hermite with
 * finite-difference tangents, so it passes through every waypoint exactly at its time and
 * never overshoots wildly on uneven spacing).  Deterministic and random-access in time.
 *
 *   const path = new TimedPath([{ t: 0, p: new THREE.Vector3(...) }, { t: 10, p: ... }, ...]);
 *   path.position(t, out)   path.velocity(t, out)   path.start / path.end
 *
 * Optional per-waypoint `v` (THREE.Vector3, m/s) pins the velocity there (e.g. a level release).
 * Outside [start, end] the path clamps to the end points (velocity zero) unless `extrapolate`.
 */
export class TimedPath {
  constructor(points, { extrapolate = false } = {}) {
    this.extrapolate = extrapolate;
    this.pts = points.slice().sort((a, b) => a.t - b.t);
    const n = this.pts.length;
    this.tan = new Array(n);
    for (let i = 0; i < n; i++) {
      const P = this.pts[i];
      if (P.v) { this.tan[i] = P.v.clone(); continue; }
      const a = this.pts[Math.max(0, i - 1)], b = this.pts[Math.min(n - 1, i + 1)];
      const dt = b.t - a.t;
      const m = new THREE.Vector3();
      if (dt > 1e-9) {
        if (i > 0 && i < n - 1) {
          // non-uniform Catmull-Rom (weighted average of the two segment velocities)
          const d0 = P.t - a.t, d1 = b.t - P.t;
          const v0 = new THREE.Vector3().subVectors(P.p, a.p).divideScalar(Math.max(d0, 1e-9));
          const v1 = new THREE.Vector3().subVectors(b.p, P.p).divideScalar(Math.max(d1, 1e-9));
          m.copy(v0).multiplyScalar(d1 / (d0 + d1)).addScaledVector(v1, d0 / (d0 + d1));
        } else {
          m.subVectors(b.p, a.p).divideScalar(dt);
        }
      }
      this.tan[i] = m;
    }
    this._i = 0;
  }
  get start() { return this.pts[0].t; }
  get end() { return this.pts[this.pts.length - 1].t; }
  _seg(t) {
    const p = this.pts; let i = this._i;
    if (i > p.length - 2) i = p.length - 2;
    if (i >= 0 && p[i].t <= t && t <= p[i + 1].t) return i;
    let lo = 0, hi = p.length - 2;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (p[mid].t <= t) lo = mid; else hi = mid - 1; }
    return (this._i = lo);
  }
  position(t, out = new THREE.Vector3()) {
    const p = this.pts, n = p.length;
    if (n === 1) return out.copy(p[0].p);
    if (t <= p[0].t) return this.extrapolate ? out.copy(p[0].p).addScaledVector(this.tan[0], t - p[0].t) : out.copy(p[0].p);
    if (t >= p[n - 1].t) return this.extrapolate ? out.copy(p[n - 1].p).addScaledVector(this.tan[n - 1], t - p[n - 1].t) : out.copy(p[n - 1].p);
    const i = this._seg(t), a = p[i], b = p[i + 1], h = b.t - a.t, u = (t - a.t) / h;
    const u2 = u * u, u3 = u2 * u;
    const h00 = 2 * u3 - 3 * u2 + 1, h10 = u3 - 2 * u2 + u, h01 = -2 * u3 + 3 * u2, h11 = u3 - u2;
    const m0 = this.tan[i], m1 = this.tan[i + 1];
    return out.set(
      h00 * a.p.x + h10 * h * m0.x + h01 * b.p.x + h11 * h * m1.x,
      h00 * a.p.y + h10 * h * m0.y + h01 * b.p.y + h11 * h * m1.y,
      h00 * a.p.z + h10 * h * m0.z + h01 * b.p.z + h11 * h * m1.z,
    );
  }
  velocity(t, out = new THREE.Vector3()) {
    const p = this.pts, n = p.length;
    if (n === 1) return out.set(0, 0, 0);
    if (t <= p[0].t) return this.extrapolate ? out.copy(this.tan[0]) : out.set(0, 0, 0);
    if (t >= p[n - 1].t) return this.extrapolate ? out.copy(this.tan[n - 1]) : out.set(0, 0, 0);
    const i = this._seg(t), a = p[i], b = p[i + 1], h = b.t - a.t, u = (t - a.t) / h;
    const u2 = u * u;
    const d00 = (6 * u2 - 6 * u) / h, d10 = 3 * u2 - 4 * u + 1, d01 = (-6 * u2 + 6 * u) / h, d11 = 3 * u2 - 2 * u;
    const m0 = this.tan[i], m1 = this.tan[i + 1];
    return out.set(
      d00 * a.p.x + d10 * m0.x + d01 * b.p.x + d11 * m1.x,
      d00 * a.p.y + d10 * m0.y + d01 * b.p.y + d11 * m1.y,
      d00 * a.p.z + d10 * m0.z + d01 * b.p.z + d11 * m1.z,
    );
  }
  /** acceleration by central difference (m/s^2) - used for bank angle. */
  acceleration(t, out = new THREE.Vector3(), h = 0.25) {
    const a = _v1, b = _v2;
    this.velocity(t - h, a); this.velocity(t + h, b);
    return out.subVectors(b, a).divideScalar(2 * h);
  }
}
const _v1 = new THREE.Vector3(), _v2 = new THREE.Vector3();

// ---- orientation helpers ----------------------------------------------------------------
const _f = new THREE.Vector3(), _r = new THREE.Vector3(), _u = new THREE.Vector3(), _m = new THREE.Matrix4();
/**
 * Quaternion for a model whose nose is local -Z and up is +Y, given a world forward direction
 * and a bank angle in radians (positive = right wing down).  Forward need not be normalised.
 */
export function quatFromForward(forward, bankRad = 0, out = new THREE.Quaternion()) {
  _f.copy(forward);
  if (_f.lengthSq() < 1e-12) _f.set(0, 0, -1);
  _f.normalize();
  _r.set(-_f.z, 0, _f.x); // right = forward x up(0,1,0) -> (fz*0 - fy*0 ...) simplified for level right vector
  if (_r.lengthSq() < 1e-10) _r.set(1, 0, 0);
  _r.normalize();
  _u.crossVectors(_r, _f);              // up = right x forward
  if (bankRad !== 0) {
    const c = Math.cos(bankRad), s = Math.sin(bankRad);
    // rotate right/up about forward: right wing goes down for positive bank
    const rx = _r.x * c - _u.x * s, ry = _r.y * c - _u.y * s, rz = _r.z * c - _u.z * s;
    _u.set(_u.x * c + _r.x * s, _u.y * c + _r.y * s, _u.z * c + _r.z * s);
    _r.set(rx, ry, rz);
  }
  _m.makeBasis(_r, _u, _f.clone().negate()); // columns: +X right, +Y up, +Z = -forward
  return out.setFromRotationMatrix(_m);
}

/** coordinated-turn bank angle (rad, + = right wing down) from velocity and acceleration vectors. */
export function bankFromAccel(vel, acc, maxBankRad = 1.2) {
  const speed2 = vel.x * vel.x + vel.z * vel.z;
  if (speed2 < 1) return 0;
  // lateral acceleration to the right of the velocity vector (world XZ): right = (-vz, vx)/|v|
  const inv = 1 / Math.sqrt(speed2);
  const lat = (acc.x * (-vel.z) + acc.z * vel.x) * inv;
  return clamp(Math.atan2(lat, 9.81), -maxBankRad, maxBankRad);
}
