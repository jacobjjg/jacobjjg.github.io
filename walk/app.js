(function () {
  'use strict';
  const { StepDetector, RouteTracker, distanceAt, splits, calories, strideFromHeight, toGpx } = window.WalkCore;
  const $ = (id) => document.getElementById(id);
  const L = window.L;

  /* ---------- settings ---------- */
  const store = {
    get(key, fallback) {
      try {
        const v = localStorage.getItem(key);
        return v == null ? fallback : JSON.parse(v);
      } catch (e) {
        return fallback;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch (e) { /* storage full or blocked: tracking still works */ }
    },
    del(key) {
      try {
        localStorage.removeItem(key);
      } catch (e) { /* ignore */ }
    },
  };

  const settings = Object.assign(
    { units: /^en-(US|GB|LR|MM)/.test(navigator.language || '') ? 'mi' : 'km', height: 170, weight: 70, stride: null, awake: true },
    store.get('walk.settings', {})
  );
  const saveSettings = () => store.set('walk.settings', settings);
  const strideM = () => (settings.stride ? settings.stride / 100 : strideFromHeight(settings.height));
  const unit = () =>
    settings.units === 'mi'
      ? { m: 1609.344, d: 'mi', speed: 'mph', h: 'ft', hM: 0.3048 }
      : { m: 1000, d: 'km', speed: 'km/h', h: 'm', hM: 1 };

  /* ---------- formatting ---------- */
  const pad = (n) => String(n).padStart(2, '0');
  function fmtDur(ms) {
    const s = Math.max(0, Math.floor(ms / 1000));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    return h ? `${h}:${pad(m)}:${pad(s % 60)}` : `${pad(m)}:${pad(s % 60)}`;
  }
  const fmtDist = (m) => (m / unit().m).toFixed(2);
  function fmtPace(metresPerSec) {
    if (!(metresPerSec > 0.25)) return '–:––';
    const sec = Math.round(unit().m / metresPerSec);
    return `${Math.floor(sec / 60)}:${pad(sec % 60)}`;
  }
  const fmtSpeed = (mps) => ((mps * 3600) / unit().m).toFixed(1);
  const fmtInt = (n) => Math.round(n).toLocaleString();
  const fmtDate = (t) =>
    new Date(t).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }) +
    ' · ' +
    new Date(t).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });

  /* ---------- small UI helpers ---------- */
  let toastTimer;
  function toast(msg, ms = 3500) {
    const el = $('toast');
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (el.hidden = true), ms);
  }
  function banner(msg) {
    $('banner').textContent = msg || '';
    $('banner').hidden = !msg;
  }
  function ask(title, body, okLabel, danger) {
    return new Promise((resolve) => {
      const dlg = $('ask');
      $('askTitle').textContent = title;
      $('askBody').textContent = body;
      $('askOk').textContent = okLabel || 'OK';
      $('askOk').className = 'btn ' + (danger ? 'danger' : 'primary');
      const done = (v) => {
        $('askOk').onclick = $('askCancel').onclick = dlg.oncancel = null;
        dlg.close();
        resolve(v);
      };
      $('askOk').onclick = () => done(true);
      $('askCancel').onclick = () => done(false);
      dlg.oncancel = (e) => {
        e.preventDefault();
        done(false);
      };
      dlg.showModal();
    });
  }
  function download(name, text, mime) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: mime }));
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  }

  /* ---------- saved walks (IndexedDB) ---------- */
  const db = (() => {
    let opening;
    const open = () =>
      opening ||
      (opening = new Promise((res, rej) => {
        const r = indexedDB.open('walk-tracker', 1);
        r.onupgradeneeded = () => r.result.createObjectStore('walks', { keyPath: 'id' });
        r.onsuccess = () => res(r.result);
        r.onerror = () => rej(r.error);
      }));
    const run = async (mode, fn) => {
      const d = await open();
      return new Promise((res, rej) => {
        const tx = d.transaction('walks', mode);
        const rq = fn(tx.objectStore('walks'));
        tx.oncomplete = () => res(rq.result);
        tx.onerror = tx.onabort = () => rej(tx.error);
      });
    };
    return {
      all: () => run('readonly', (s) => s.getAll()),
      put: (w) => run('readwrite', (s) => s.put(w)),
      del: (id) => run('readwrite', (s) => s.delete(id)),
      clear: () => run('readwrite', (s) => s.clear()),
    };
  })();

  /* ---------- live map ---------- */
  const TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  const ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
  let map, me, meRing, liveLines = [], follow = true;

  function initMap() {
    if (!L) return;
    map = L.map('map', { zoomControl: false, attributionControl: true }).setView([20, 0], 2);
    L.tileLayer(TILES, { maxZoom: 19, attribution: ATTR }).addTo(map);
    map.on('dragstart', () => {
      follow = false;
      $('recenter').hidden = false;
    });
    $('recenter').onclick = () => {
      follow = true;
      $('recenter').hidden = true;
      if (lastFix) map.setView([lastFix.lat, lastFix.lon], Math.max(map.getZoom(), 17));
    };
  }
  function showPosition(fix) {
    if (!map) return;
    const ll = [fix.lat, fix.lon];
    if (!me) {
      meRing = L.circle(ll, { radius: fix.acc || 0, stroke: false, fillColor: '#1a8cff', fillOpacity: 0.15 }).addTo(map);
      me = L.circleMarker(ll, { radius: 8, color: '#fff', weight: 3, fillColor: '#1a8cff', fillOpacity: 1 }).addTo(map);
      map.setView(ll, 17);
    } else {
      me.setLatLng(ll);
      meRing.setLatLng(ll).setRadius(fix.acc || 0);
      if (follow) map.panTo(ll, { animate: true });
    }
  }
  function drawLive(points) {
    if (!map) return;
    liveLines.forEach((l) => l.remove());
    liveLines = [];
    for (const seg of segments(points)) {
      liveLines.push(L.polyline(seg, { color: '#1a8cff', weight: 5, opacity: 0.9 }).addTo(map));
    }
    liveSeg = points.length ? points[points.length - 1][5] : -1;
  }
  let liveSeg = -1;
  function extendLive(p) {
    if (!map) return;
    if (p[5] !== liveSeg || !liveLines.length) {
      liveLines.push(L.polyline([], { color: '#1a8cff', weight: 5, opacity: 0.9 }).addTo(map));
      liveSeg = p[5];
    }
    liveLines[liveLines.length - 1].addLatLng([p[0], p[1]]);
  }
  function segments(points) {
    const out = [];
    let seg = null;
    for (const p of points) {
      if (p[5] !== seg) {
        seg = p[5];
        out.push([]);
      }
      out[out.length - 1].push([p[0], p[1]]);
    }
    return out;
  }

  /* ---------- sensors ---------- */
  let S = null; // the walk in progress
  let lastFix = null;
  let watchId = null;
  let wakeLock = null;

  function startGps() {
    if (watchId != null || !navigator.geolocation) {
      if (!navigator.geolocation) banner('This browser has no GPS support, so distance and the map are unavailable.');
      return;
    }
    $('gps').textContent = 'Finding GPS…';
    watchId = navigator.geolocation.watchPosition(onFix, onGpsError, {
      enableHighAccuracy: true,
      maximumAge: 0,
      timeout: 30000,
    });
  }
  function onFix(pos) {
    const c = pos.coords;
    const fix = { lat: c.latitude, lon: c.longitude, acc: c.accuracy, alt: c.altitude, altAcc: c.altitudeAccuracy, t: Date.now() };
    lastFix = fix;
    banner('');
    const acc = Math.round(fix.acc);
    const el = $('gps');
    el.dataset.q = acc <= 12 ? 'good' : acc <= 35 ? 'ok' : 'bad';
    el.textContent = `GPS ±${settings.units === 'mi' ? Math.round(acc / 0.3048) + ' ft' : acc + ' m'}`;
    showPosition(fix);
    if (S && S.state === 'running') {
      if (S.tracker.add(fix, movingHint()) === 'point') {
        extendLive(S.tracker.points[S.tracker.points.length - 1]);
        render();
      }
    }
  }
  function onGpsError(err) {
    $('gps').dataset.q = 'bad';
    if (err.code === 1) {
      $('gps').textContent = 'GPS blocked';
      banner('Location permission is off. Allow location for this site in your browser settings to track distance and route.');
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    } else {
      $('gps').textContent = 'No GPS signal';
    }
  }

  /** true/false when the step sensor is live, null when we can't tell. */
  function movingHint() {
    const now = Date.now();
    if (!S || !S.motionSeen || !S.lastMotionAt || now - S.lastMotionAt > 2000) return null;
    return now - S.lastStepAt < 5000;
  }

  function onMotion(e) {
    const a = e.accelerationIncludingGravity;
    if (!S || S.state !== 'running' || !a || a.x == null) return;
    const now = Date.now();
    S.motionSeen = true;
    // A silence in the sensor stream means the page was suspended; remember
    // it so steps for the distance covered meanwhile can be filled in.
    if (S.lastMotionAt && now - S.lastMotionAt > 5000) S.gaps.push([S.lastMotionAt, now]);
    S.lastMotionAt = now;
    const n = S.det.push(e.timeStamp, a.x, a.y, a.z);
    if (n) {
      S.lastStepAt = now;
      for (let i = 0; i < n; i++) S.stepTimes.push(now);
    }
  }
  async function enableMotion() {
    if (typeof DeviceMotionEvent === 'undefined') return;
    try {
      if (typeof DeviceMotionEvent.requestPermission === 'function') {
        if ((await DeviceMotionEvent.requestPermission()) !== 'granted') {
          toast('Motion access denied: steps will be estimated from distance.');
        }
      }
    } catch (e) { /* not in a user gesture, or unsupported */ }
  }
  window.addEventListener('devicemotion', onMotion);

  async function holdWake() {
    if (!settings.awake || !('wakeLock' in navigator) || !S || S.state !== 'running') return;
    try {
      wakeLock = await navigator.wakeLock.request('screen');
    } catch (e) { /* low battery or not visible */ }
  }
  function dropWake() {
    if (wakeLock) wakeLock.release().catch(() => {});
    wakeLock = null;
  }

  /* ---------- the walk in progress ---------- */
  const activeMs = () => (S ? S.activeMs + (S.state === 'running' ? Date.now() - S.resumedAt : 0) : 0);

  function stepInfo() {
    const dist = S.tracker.distance;
    const stride = strideM();
    if (!S.motionSeen) return { steps: Math.round(dist / stride), est: true };
    let gapDist = 0;
    for (const [a, b] of S.gaps) gapDist += S.tracker.distanceAt(b) - S.tracker.distanceAt(a);
    const counted = S.det.steps;
    const measured = counted > 100 && dist - gapDist > 80 ? Math.min(1.2, Math.max(0.4, (dist - gapDist) / counted)) : stride;
    return { steps: counted + Math.round(gapDist / measured), est: false };
  }

  function newSession(saved) {
    const det = new StepDetector();
    if (saved) det.steps = saved.detSteps || 0;
    return {
      id: saved ? saved.id : Date.now(),
      start: saved ? saved.start : Date.now(),
      activeMs: saved ? saved.activeMs : 0,
      resumedAt: Date.now(),
      state: saved ? 'paused' : 'running',
      tracker: new RouteTracker(saved),
      det,
      motionSeen: saved ? !!saved.motionSeen : false,
      gaps: saved ? saved.gaps || [] : [],
      lastMotionAt: null,
      lastStepAt: 0,
      stepTimes: [],
    };
  }
  function snapshot() {
    if (!S) return;
    store.set('walk.active', {
      id: S.id,
      start: S.start,
      activeMs: activeMs(),
      detSteps: S.det.steps,
      motionSeen: S.motionSeen,
      gaps: S.gaps,
      points: S.tracker.points,
      distance: S.tracker.distance,
      gain: S.tracker.gain,
      loss: S.tracker.loss,
    });
  }

  async function start() {
    await enableMotion();
    S = newSession();
    follow = true;
    $('recenter').hidden = true;
    drawLive([]);
    startGps();
    holdWake();
    setControls();
    render();
  }
  function pause() {
    S.activeMs = activeMs();
    S.state = 'paused';
    S.tracker.breakSegment();
    S.det.reset();
    S.lastMotionAt = null;
    dropWake();
    snapshot();
    setControls();
    render();
  }
  function resume() {
    enableMotion();
    S.resumedAt = Date.now();
    S.state = 'running';
    startGps();
    holdWake();
    setControls();
    render();
  }
  async function finish() {
    const info = stepInfo();
    const dist = S.tracker.distance;
    if (dist < 10 && info.steps < 10) {
      if (!(await ask('Discard this walk?', 'Nothing has been recorded yet.', 'Discard', true))) return;
      endSession();
      return;
    }
    if (!(await ask('Finish walk?', `${fmtDist(dist)} ${unit().d} in ${fmtDur(activeMs())}.`, 'Finish'))) return;
    const ms = activeMs();
    const walk = {
      id: S.id,
      start: S.start,
      end: Date.now(),
      activeMs: ms,
      distance: Math.round(dist * 10) / 10,
      steps: info.steps,
      stepsEstimated: info.est,
      gain: Math.round(S.tracker.gain),
      loss: Math.round(S.tracker.loss),
      kcal: Math.round(calories(settings.weight, ms, dist)),
      points: S.tracker.points,
    };
    try {
      await db.put(walk);
    } catch (e) {
      toast('Could not save the walk: storage is unavailable.');
      return;
    }
    endSession();
    openDetail(walk);
  }
  function endSession() {
    S = null;
    $('toast').hidden = true;
    store.del('walk.active');
    dropWake();
    drawLive([]);
    setControls();
    render();
  }

  function setControls() {
    $('btnStart').hidden = !!S;
    $('btnPause').hidden = $('btnFinish').hidden = !S;
    if (S) {
      $('btnPause').textContent = S.state === 'running' ? 'Pause' : 'Resume';
      $('btnPause').className = 'btn' + (S.state === 'running' ? '' : ' primary');
    }
  }

  function render() {
    const u = unit();
    $('distLbl').textContent = u.d;
    $('paceLbl').textContent = `pace /${u.d}`;
    $('avgPaceLbl').textContent = `avg /${u.d}`;
    $('speedLbl').textContent = u.speed;
    $('gainLbl').textContent = `climb ${u.h}`;
    if (!S) {
      $('dist').textContent = '0.00';
      $('time').textContent = '00:00';
      $('steps').textContent = '0';
      $('stepsLbl').textContent = 'steps';
      $('pace').textContent = $('avgPace').textContent = '–:––';
      $('speed').textContent = '0.0';
      $('kcal').textContent = $('cadence').textContent = $('gain').textContent = '0';
      return;
    }
    const now = Date.now();
    const ms = activeMs();
    const dist = S.tracker.distance;
    const info = stepInfo();

    let speed = 0;
    if (S.state === 'running') {
      const from = Math.max(now - 30000, S.resumedAt);
      const span = (now - from) / 1000;
      if (span >= 5) speed = (dist - S.tracker.distanceAt(from)) / span;
    }
    const avg = dist > 20 && ms > 0 ? dist / (ms / 1000) : 0;

    while (S.stepTimes.length && now - S.stepTimes[0] > 20000) S.stepTimes.shift();
    const cadence = info.est || S.state !== 'running' ? (ms > 30000 ? info.steps / (ms / 60000) : 0) : S.stepTimes.length * 3;

    $('dist').textContent = fmtDist(dist);
    $('time').textContent = fmtDur(ms);
    $('steps').textContent = fmtInt(info.steps);
    $('stepsLbl').textContent = info.est ? 'steps (est.)' : 'steps';
    $('pace').textContent = fmtPace(speed);
    $('avgPace').textContent = fmtPace(avg);
    $('speed').textContent = fmtSpeed(speed);
    $('kcal').textContent = fmtInt(calories(settings.weight, ms, dist));
    $('cadence').textContent = fmtInt(cadence);
    $('gain').textContent = fmtInt(S.tracker.gain / u.hM);
  }

  /* ---------- history ---------- */
  function routeSvg(points) {
    if (points.length < 2) return '<svg viewBox="0 0 64 64"></svg>';
    const step = Math.max(1, Math.floor(points.length / 80));
    const k = Math.cos((points[0][0] * Math.PI) / 180);
    const pts = points.filter((_, i) => i % step === 0 || i === points.length - 1).map((p) => [p[1] * k, -p[0]]);
    const xs = pts.map((p) => p[0]);
    const ys = pts.map((p) => p[1]);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const w = Math.max(...xs) - minX;
    const h = Math.max(...ys) - minY;
    const sc = 44 / Math.max(w, h, 1e-9);
    const ox = (64 - w * sc) / 2;
    const oy = (64 - h * sc) / 2;
    const d = pts.map((p) => `${(ox + (p[0] - minX) * sc).toFixed(1)},${(oy + (p[1] - minY) * sc).toFixed(1)}`).join(' ');
    return `<svg viewBox="0 0 64 64"><polyline points="${d}"/></svg>`;
  }
  const statCell = (num, lbl) => `<div class="stat"><div class="num">${num}</div><div class="lbl">${lbl}</div></div>`;

  async function renderHistory() {
    let walks = [];
    try {
      walks = (await db.all()).sort((a, b) => b.start - a.start);
    } catch (e) {
      $('walkList').innerHTML = '<div class="empty">Saved walks are unavailable in this browser mode.</div>';
      return;
    }
    const u = unit();
    const sum = (list, key) => list.reduce((n, w) => n + (w[key] || 0), 0);
    const week = walks.filter((w) => w.start > Date.now() - 7 * 864e5);
    $('totals').innerHTML = walks.length
      ? '<h2>Last 7 days</h2>' +
        statCell(fmtDist(sum(week, 'distance')), u.d) +
        statCell(fmtInt(sum(week, 'steps')), 'steps') +
        statCell(week.length, week.length === 1 ? 'walk' : 'walks') +
        '<h2>All time</h2>' +
        statCell(fmtDist(sum(walks, 'distance')), u.d) +
        statCell(fmtInt(sum(walks, 'steps')), 'steps') +
        statCell(fmtDur(sum(walks, 'activeMs')), 'time')
      : '';
    const list = $('walkList');
    list.innerHTML = walks.length ? '' : '<div class="empty">No walks yet. Your finished walks will show up here.</div>';
    for (const w of walks) {
      const b = document.createElement('button');
      b.className = 'walk';
      b.innerHTML =
        routeSvg(w.points) +
        `<div><div class="main">${fmtDist(w.distance)} ${u.d} · ${fmtDur(w.activeMs)}</div>` +
        `<div class="meta">${fmtInt(w.steps)} steps · ${fmtDate(w.start)}</div></div>`;
      b.onclick = () => openDetail(w);
      list.appendChild(b);
    }
  }

  let detailMap, detailLayer, detailWalk;
  function openDetail(w) {
    detailWalk = w;
    const u = unit();
    const secs = w.activeMs / 1000;
    const avg = w.distance > 20 && secs > 0 ? w.distance / secs : 0;
    $('detailTitle').textContent = `${fmtDist(w.distance)} ${u.d} walk`;
    $('detailSub').textContent = fmtDate(w.start);
    $('detailStats').innerHTML =
      statCell(fmtDist(w.distance), u.d) +
      statCell(fmtDur(w.activeMs), 'time') +
      statCell(fmtInt(w.steps), w.stepsEstimated ? 'steps (est.)' : 'steps') +
      statCell(fmtPace(avg), `avg /${u.d}`) +
      statCell(fmtSpeed(avg), u.speed) +
      statCell(fmtInt(w.kcal), 'kcal') +
      statCell(fmtInt(w.gain / u.hM), `climb ${u.h}`) +
      statCell(secs > 30 ? fmtInt(w.steps / (secs / 60)) : '0', 'steps/min') +
      statCell(
        w.steps > 20 && w.distance > 20
          ? settings.units === 'mi'
            ? (w.distance / w.steps / 0.0254).toFixed(0) + ' in'
            : ((w.distance / w.steps) * 100).toFixed(0) + ' cm'
          : '–',
        'stride'
      );

    const sp = splits(w.points, u.m);
    if (sp.length) {
      const slow = Math.max(...sp);
      $('detailSplits').innerHTML =
        `<table class="splits"><tr><th>${u.d}</th><th></th><th>Time</th></tr>` +
        sp
          .map(
            (ms, i) =>
              `<tr><td>${i + 1}</td><td class="barcell"><div class="bar" style="width:${Math.round((ms / slow) * 100)}%"></div></td><td>${fmtDur(ms)}</td></tr>`
          )
          .join('') +
        '</table>';
    } else {
      $('detailSplits').innerHTML = '';
    }

    $('detail').hidden = false;
    if (!L) return;
    if (!detailMap) {
      detailMap = L.map('detailMap', { zoomControl: false });
      L.tileLayer(TILES, { maxZoom: 19, attribution: ATTR }).addTo(detailMap);
      detailLayer = L.featureGroup().addTo(detailMap);
    }
    detailLayer.clearLayers();
    detailMap.invalidateSize();
    for (const seg of segments(w.points)) L.polyline(seg, { color: '#1a8cff', weight: 5 }).addTo(detailLayer);
    if (w.points.length) {
      const a = w.points[0];
      const z = w.points[w.points.length - 1];
      const dot = (p, fill) => L.circleMarker([p[0], p[1]], { radius: 7, color: '#fff', weight: 3, fillColor: fill, fillOpacity: 1 }).addTo(detailLayer);
      dot(a, '#12a150');
      dot(z, '#d13b2e');
      detailMap.fitBounds(detailLayer.getBounds(), { padding: [24, 24], maxZoom: 18 });
    } else {
      detailMap.setView(lastFix ? [lastFix.lat, lastFix.lon] : [20, 0], lastFix ? 15 : 2);
    }
  }
  $('detailBack').onclick = () => {
    $('detail').hidden = true;
    renderHistory();
  };
  $('btnGpx').onclick = () => {
    const stamp = new Date(detailWalk.start).toISOString().slice(0, 16).replace(/[T:]/g, '-');
    download(`walk-${stamp}.gpx`, toGpx(detailWalk), 'application/gpx+xml');
  };
  $('btnDelete').onclick = async () => {
    if (!(await ask('Delete this walk?', 'This cannot be undone.', 'Delete', true))) return;
    await db.del(detailWalk.id);
    $('detail').hidden = true;
    renderHistory();
  };

  /* ---------- settings ---------- */
  function fillSettings() {
    const imp = settings.units === 'mi';
    $('setUnits').value = settings.units;
    $('heightLbl').textContent = imp ? 'Height (inches)' : 'Height (cm)';
    $('weightLbl').textContent = imp ? 'Weight (lb)' : 'Weight (kg)';
    $('strideLbl').textContent = imp ? 'Stride length (inches)' : 'Stride length (cm)';
    const r1 = (n) => Math.round(n * 10) / 10;
    $('setHeight').value = r1(imp ? settings.height / 2.54 : settings.height);
    $('setWeight').value = r1(imp ? settings.weight / 0.45359237 : settings.weight);
    $('setStride').value = settings.stride ? r1(imp ? settings.stride / 2.54 : settings.stride) : '';
    $('setAwake').checked = settings.awake;
  }
  function readSettings() {
    const imp = settings.units === 'mi';
    const num = (id) => parseFloat($(id).value);
    const h = num('setHeight');
    const w = num('setWeight');
    const s = num('setStride');
    if (h > 0) settings.height = imp ? h * 2.54 : h;
    if (w > 0) settings.weight = imp ? w * 0.45359237 : w;
    settings.stride = s > 0 ? (imp ? s * 2.54 : s) : null;
    settings.awake = $('setAwake').checked;
    saveSettings();
    render();
  }
  $('setUnits').onchange = () => {
    settings.units = $('setUnits').value;
    saveSettings();
    fillSettings();
    render();
  };
  for (const id of ['setHeight', 'setWeight', 'setStride', 'setAwake']) $(id).onchange = readSettings;
  $('btnExportAll').onclick = async () => {
    const walks = await db.all();
    if (!walks.length) return toast('No walks to export yet.');
    download('walks.json', JSON.stringify(walks), 'application/json');
  };
  $('btnDeleteAll').onclick = async () => {
    if (!(await ask('Delete all walks?', 'Every saved walk on this device will be removed. This cannot be undone.', 'Delete all', true))) return;
    await db.clear();
    toast('All walks deleted.');
  };

  /* ---------- navigation & lifecycle ---------- */
  document.querySelectorAll('.tabs button').forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll('.tabs button').forEach((x) => x.classList.toggle('active', x === b));
      document.querySelectorAll('.view').forEach((v) => v.classList.toggle('active', v.id === 'view-' + b.dataset.view));
      if (b.dataset.view === 'history') renderHistory();
      if (b.dataset.view === 'settings') fillSettings();
      if (b.dataset.view === 'track' && map) map.invalidateSize();
    };
  });

  $('btnStart').onclick = start;
  $('btnPause').onclick = () => (S.state === 'running' ? pause() : resume());
  $('btnFinish').onclick = finish;

  let hiddenAt = 0;
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      hiddenAt = Date.now();
      snapshot();
    } else {
      holdWake();
      if (S && S.state === 'running' && hiddenAt && Date.now() - hiddenAt > 15000) {
        toast('Tracking is limited while the app is in the background. Keep it open for best accuracy.', 6000);
      }
      render();
    }
  });
  window.addEventListener('pagehide', snapshot);
  setInterval(() => {
    if (S) render();
  }, 500);
  setInterval(() => {
    if (S && S.state === 'running') snapshot();
  }, 10000);

  initMap();
  const saved = store.get('walk.active', null);
  if (saved && saved.id) {
    S = newSession(saved);
    drawLive(S.tracker.points);
    startGps();
    toast('Recovered your unfinished walk. Resume or finish it.', 6000);
  } else if (navigator.permissions && navigator.permissions.query) {
    // Warm up GPS early when we already have permission, without prompting.
    navigator.permissions
      .query({ name: 'geolocation' })
      .then((p) => p.state === 'granted' && startGps())
      .catch(() => {});
  }
  setControls();
  render();

  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }

  window.__walk = { get session() { return S; } }; // for debugging from the console
})();
