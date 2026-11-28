// CONTROLS - explore-mode camera (system id "controls", update order 5).
//
// Orbit camera around a focus point or a followed entity.  All camera math is in GLOBAL world
// coordinates (camera.position + the overridden camera.lookAt), so it is correct with the floating
// origin 400 km north of Oahu.  In doc mode it never touches the camera.  In explore mode it is
// HANDS-OFF until the user gives input or focus()/follow()/setState() is called: a camera placed by
// app.setCamera / app.lookAtEntity (URL parameters, the screenshot tool, "Explore from here") is kept
// bit-exact, and the orbit state is derived from it lazily at the first input.
//
// Public API (app.getSystem('controls')):
//   focus(idOrPoint, { dist, az, el, fov, follow, immediate, duration })   fly to an entity id or a global point
//   follow(id | null, { frame: 'heading' | 'world', dist, az, el, immediate })
//   setFollowFrame('heading' | 'world')        getState() -> plain object        setState(state, { immediate })
// Events emitted on app.events:
//   'camera-user'  { source: 'pointer' | 'wheel' | 'key' | 'touch' }  the user took control of the camera
//   'camera-follow' { id | null, frame }                               follow target changed
//   'view-click'   { x, y, pointerType }                               click / tap on the 3D view without dragging
//   'view-pick'    { id, x, y }                                        double-click picked an entity (it is being focused)
import * as THREE from 'three';
import { clamp, ease, angleDiff } from '../../core/math.js';
import { ui, Projector, pickEntity, entityHeading } from './state.js';
import { isTypingTarget } from './dom.js';

// ---- tunables ---------------------------------------------------------------------------------
const TUNE = {
  minDist: 3, maxDist: 150000,          // dolly range (m)
  minFov: 8, maxFov: 80, fovStep: 4,    // degrees
  rotate: 0.28,                         // deg per px of drag
  wheel: 0.0016,                        // log-distance per wheel pixel
  dollyDamp: 11, rotDamp: 6.5, panDamp: 7, flyDamp: 7, fovDamp: 9, headingDamp: 3.2,  // 1/s (frame-rate independent)
  flySpeed: 0.85, flyFast: 4, flyMin: 6, // fly speed = max(flyMin, dist * flySpeed) m/s, x flyFast with shift
  clearance: 2,                         // metres kept above terrain / sea
  flyTo: 1.2,                           // seconds for an eased fly-to
  clickPx: 6, clickMs: 450,
  attractRate: 1.4,                     // deg/s slow orbit behind the opening card
};

const DEG = Math.PI / 180;
const _v = new THREE.Vector3(), _v2 = new THREE.Vector3(), _v3 = new THREE.Vector3(), _dir = new THREE.Vector3();
const _q = new THREE.Quaternion();

const S = {
  app: null,
  proj: new Projector(),
  passive: true,                 // true: the camera belongs to whoever placed it; state not yet derived
  target: new THREE.Vector3(),   // focus point (global); when following: the entity position is used instead
  lift: 0,                       // height of the focus point above terrain / sea (free focus only)
  logDist: Math.log(3000), logDistGoal: Math.log(3000),
  az: 135, el: 15,               // camera bearing from the target (deg true; relative to the entity heading in the heading frame) / elevation
  fov: 35, fovGoal: 35,
  followId: null, followFrame: 'heading', followOffset: new THREE.Vector3(), heading: 0, headingValid: false,
  vAz: 0, vEl: 0, vPan: new THREE.Vector3(), vFly: new THREE.Vector3(),
  trans: null,                   // decaying offset from the previous pose: { u, dur, dTarget, dLog, dAz, dEl, dFov, bump }
  dirty: false,
  user: false,
  lastPos: new THREE.Vector3(NaN, NaN, NaN), lastQuat: new THREE.Quaternion(), lastFov: NaN, lastSim: 0,
  // input accumulators (filled by event handlers, consumed once per frame)
  in: { rotX: 0, rotY: 0, panX: 0, panY: 0, zoom: 0, pinch: 0, source: null },
  keys: new Set(),
  pointers: new Map(),
  drag: null,                    // { mode: 'rotate' | 'pan' | 'touch2', x0, y0, t0, moved, lastDist, lastCx, lastCy }
  handlers: [],
};

const groundAt = (x, z) => Math.max(S.app.height.at(x, z), 0);
const dist = () => Math.exp(S.logDist);

function entity(id) { return id ? S.app.registry.get(id) : null; }

/** Resolve the focus point for the current sim time. */
function resolveTarget(out) {
  const e = entity(S.followId);
  if (e) {
    try { e.getPosition(S.app.time.sim, out); out.add(S.followOffset); return out; } catch (err) { /* fall through to the free target */ }
  }
  return out.copy(S.target);
}
function worldAz() { return S.followId && S.followFrame === 'heading' && S.headingValid ? S.az + S.heading : S.az; }

/** Derive the orbit state from the camera as it is right now (pose is preserved exactly). */
function adopt() {
  const app = S.app, cam = app.camera;
  S.proj.update(app);
  const fwd = S.proj.fwd, p = cam.position;
  let t = 0;
  // 1. an entity near the centre of the view makes the natural pivot
  const centre = pickEntity(app, S.proj, S.proj.w / 2, S.proj.h / 2, { radius: Math.min(S.proj.w, S.proj.h) * 0.06, filter: (e) => e.kind !== 'place' });
  if (centre) { centre.getPosition(app.time.sim, _v); t = _v.sub(p).dot(fwd); }
  // 2. otherwise the terrain / sea under the centre of the view
  if (!(t > 1)) t = groundHit(p, fwd) || 0;
  // 3. otherwise a point ahead, scaled by the height above ground
  if (!(t > 1)) t = clamp((p.y - groundAt(p.x, p.z)) * 4, 150, 6000);
  t = clamp(t, TUNE.minDist, TUNE.maxDist);
  S.target.copy(p).addScaledVector(fwd, t);
  S.lift = Math.max(0, S.target.y - groundAt(S.target.x, S.target.z));
  S.logDist = S.logDistGoal = Math.log(t);
  S.az = (Math.atan2(-fwd.x, fwd.z) / DEG + 360) % 360;
  S.el = Math.asin(clamp(-fwd.y, -1, 1)) / DEG;
  S.fov = S.fovGoal = cam.fov;
  S.followId = null; S.followOffset.set(0, 0, 0); S.headingValid = false;
  S.vAz = S.vEl = 0; S.vPan.set(0, 0, 0); S.vFly.set(0, 0, 0);
  S.trans = null;
  S.passive = false;
}

/** Distance along a ray to the terrain / sea surface, or 0 when it never comes down (coarse march, no raycast). */
function groundHit(o, d) {
  let t = 0;
  for (let i = 0; i < 72; i++) {
    const x = o.x + d.x * t, y = o.y + d.y * t, z = o.z + d.z * t;
    const h = y - groundAt(x, z);
    if (h < 0.75) return Math.max(t, 0.01);
    if (t > 300000) return 0;
    // conservative step: full height when looking down steeply, a fraction of it over rolling ground
    t += Math.max(1.5, h * (d.y < -0.05 ? Math.min(1 / -d.y, 3) * 0.6 : 0.8));
    if (d.y >= 0 && h > 6000) return 0;
  }
  return d.y < -0.002 ? Math.min(o.y / -d.y, 300000) : 0;
}

/** Current rendered pose (target, distance, world azimuth, elevation, fov) including a running transition. */
function pose(out) {
  resolveTarget(out.target);
  out.az = worldAz(); out.el = S.el; out.log = S.logDist; out.fov = S.fov;
  const tr = S.trans;
  if (tr) {
    const e = ease.inOutCubic(clamp(tr.u, 0, 1)), k = 1 - e;
    out.target.addScaledVector(tr.dTarget, k);
    out.log += tr.dLog * k + tr.bump * Math.sin(Math.PI * e);
    out.az += tr.dAz * k; out.el += tr.dEl * k; out.fov += tr.dFov * k;
  }
  return out;
}
const _pose = { target: new THREE.Vector3(), az: 0, el: 0, log: 0, fov: 35 };
const _old = { target: new THREE.Vector3(), az: 0, el: 0, log: 0, fov: 35 };

function writeCamera() {
  const app = S.app, cam = app.camera, p = pose(_pose);
  const d = Math.exp(clamp(p.log, Math.log(TUNE.minDist), Math.log(TUNE.maxDist * 4)));
  const a = p.az * DEG, e = clamp(p.el, -88, 89.2) * DEG;
  _v.set(p.target.x + Math.sin(a) * Math.cos(e) * d, p.target.y + Math.sin(e) * d, p.target.z - Math.cos(a) * Math.cos(e) * d);
  const floor = groundAt(_v.x, _v.z) + TUNE.clearance;
  if (_v.y < floor) _v.y = floor;
  cam.position.copy(_v);
  cam.up.set(0, 1, 0);
  cam.lookAt(p.target);
  const fov = clamp(p.fov, TUNE.minFov, TUNE.maxFov);
  if (cam.fov !== fov) { cam.fov = fov; cam.updateProjectionMatrix(); }
  S.lastPos.copy(cam.position); S.lastQuat.copy(cam.quaternion); S.lastFov = cam.fov;
}

/** Start an eased transition from the pose that is on screen now to the state that has just been set. */
function beginTransition(old, duration) {
  if (ui.instant || duration <= 0) { S.trans = null; return; }
  S.trans = null;
  const now = pose(_pose);
  const travel = old.target.distanceTo(now.target);
  const dTarget = old.target.clone().sub(now.target);
  const far = Math.max(Math.exp(old.log), Math.exp(now.log));
  S.trans = {
    u: 0, dur: duration, dTarget,
    dLog: old.log - now.log, dAz: angleDiff(now.az, old.az), dEl: old.el - now.el, dFov: old.fov - now.fov,
    bump: travel > far * 1.5 ? Math.min(Math.log((travel * 0.7) / far), 6) : 0,   // pull back on long hops, like a map fly-to
  };
}

function takeUserControl(source) {
  if (!S.user) { S.user = true; S.app.events.emit('camera-user', { source }); }
  ui.attract = false;
}

function defaultView(e) {
  const r = e.length ? e.length / 2 : (e.radius || 30);
  if (e.kind === 'ship') return { dist: clamp(r * 5.5, 90, 4500), el: 13 };
  if (e.kind === 'aircraft') return { dist: clamp(r * 7, 28, 260), el: 9 };
  if (e.kind === 'person') return { dist: clamp(r * 8, 6, 40), el: 8 };
  if (e.kind === 'group') return { dist: clamp(r * 4, 200, 30000), el: 22 };
  return { dist: clamp(r * 9, 500, 9000), el: 28 };
}

// ---- public API ---------------------------------------------------------------------------------
function focus(idOrPoint, opts = {}) {
  const app = S.app;
  if (!app) return false;
  if (app.time.mode !== 'explore') app.setMode('explore');
  if (S.passive) adopt();
  pose(_old); _old.target = _old.target.clone();
  const old = { target: _old.target, az: _old.az, el: _old.el, log: _old.log, fov: _old.fov };
  const keepAz = worldAz();
  let view = null;
  if (typeof idOrPoint === 'string') {
    const e = entity(idOrPoint);
    if (!e) { console.warn(`[controls] focus: unknown entity ${idOrPoint}`); return false; }
    view = defaultView(e);
    try { e.getPosition(app.time.sim, _v); } catch (err) { return false; }
    if (opts.follow) {
      S.followId = e.id; S.followOffset.set(0, 0, 0);
      if (opts.frame === 'world' || opts.frame === 'heading') S.followFrame = opts.frame;
      const h = entityHeading(e, app.time.sim);
      S.headingValid = h != null; S.heading = h || 0;
      S.az = S.followFrame === 'heading' && S.headingValid ? keepAz - S.heading : keepAz;
      // a chase view from the quarter looks best when the user has not chosen an angle
      if (opts.az == null && S.followFrame === 'heading' && S.headingValid && e.kind === 'aircraft') S.az = 205;
    } else {
      S.followId = null; S.followOffset.set(0, 0, 0); S.az = keepAz;
      S.target.copy(_v); S.lift = Math.max(0, _v.y - groundAt(_v.x, _v.z));
    }
  } else {
    const p = Array.isArray(idOrPoint) ? _v.set(idOrPoint[0], idOrPoint[1], idOrPoint[2]) : _v.copy(idOrPoint);
    S.followId = null; S.followOffset.set(0, 0, 0); S.az = keepAz;
    const g = groundAt(p.x, p.z);
    S.target.set(p.x, Math.max(p.y, g), p.z); S.lift = Math.max(0, p.y - g);
  }
  if (opts.dist != null) S.logDist = Math.log(clamp(opts.dist, TUNE.minDist, TUNE.maxDist));
  else if (view) S.logDist = Math.log(view.dist);
  S.logDistGoal = S.logDist;
  if (opts.az != null) S.az = S.followId && S.followFrame === 'heading' && S.headingValid && opts.azWorld ? opts.az - S.heading : opts.az;
  if (opts.el != null) S.el = opts.el; else if (view) S.el = view.el;
  if (opts.fov != null) S.fov = S.fovGoal = clamp(opts.fov, TUNE.minFov, TUNE.maxFov);
  S.vAz = S.vEl = 0; S.vPan.set(0, 0, 0); S.vFly.set(0, 0, 0);
  S.user = false; S.dirty = true;
  beginTransition(old, opts.immediate ? 0 : (opts.duration != null ? opts.duration : TUNE.flyTo));
  app.events.emit('camera-follow', { id: S.followId, frame: S.followFrame });
  return true;
}

function follow(id, opts = {}) {
  const app = S.app;
  if (!app) return false;
  if (id) return focus(id, { ...opts, follow: true });
  if (!S.followId) return true;
  if (S.passive) adopt();
  // release: keep the current view, freeze the focus point where the entity is now
  const az = worldAz();
  resolveTarget(_v);
  S.followId = null; S.followOffset.set(0, 0, 0); S.az = az;
  S.target.copy(_v); S.lift = Math.max(0, _v.y - groundAt(_v.x, _v.z));
  S.dirty = true;
  app.events.emit('camera-follow', { id: null, frame: S.followFrame });
  return true;
}

function setFollowFrame(frame) {
  if (frame !== 'heading' && frame !== 'world') return;
  if (frame === S.followFrame) return;
  const az = worldAz();
  S.followFrame = frame;
  S.az = S.followId && frame === 'heading' && S.headingValid ? az - S.heading : az;
  S.dirty = true;
  S.app.events.emit('camera-follow', { id: S.followId, frame });
}

function getState() {
  if (S.passive && S.app) adopt();
  resolveTarget(_v);
  return {
    target: [_v.x, _v.y, _v.z], dist: dist(), az: (worldAz() % 360 + 360) % 360, el: S.el, fov: S.fov,
    followId: S.followId, followFrame: S.followFrame, passive: false,
  };
}

function setState(st = {}, opts = {}) {
  const app = S.app;
  if (!app) return;
  if (S.passive) adopt();
  pose(_old); const old = { target: _old.target.clone(), az: _old.az, el: _old.el, log: _old.log, fov: _old.fov };
  if (st.followFrame === 'heading' || st.followFrame === 'world') S.followFrame = st.followFrame;
  if ('followId' in st) {
    const e = entity(st.followId);
    S.followId = e ? e.id : null; S.followOffset.set(0, 0, 0);
    if (e) { const h = entityHeading(e, app.time.sim); S.headingValid = h != null; S.heading = h || 0; }
  }
  if (st.target && !S.followId) {
    S.target.set(st.target[0], st.target[1], st.target[2]);
    S.lift = Math.max(0, S.target.y - groundAt(S.target.x, S.target.z));
  }
  if (st.dist != null) S.logDist = S.logDistGoal = Math.log(clamp(st.dist, TUNE.minDist, TUNE.maxDist));
  if (st.az != null) S.az = S.followId && S.followFrame === 'heading' && S.headingValid ? st.az - S.heading : st.az;
  if (st.el != null) S.el = clamp(st.el, -85, 89);
  if (st.fov != null) S.fov = S.fovGoal = clamp(st.fov, TUNE.minFov, TUNE.maxFov);
  S.vAz = S.vEl = 0; S.vPan.set(0, 0, 0); S.vFly.set(0, 0, 0);
  S.user = false; S.dirty = true;
  beginTransition(old, opts.immediate === false ? TUNE.flyTo : 0);
}

// ---- input ---------------------------------------------------------------------------------------
function listen(target, type, fn, opts) { target.addEventListener(type, fn, opts); S.handlers.push([target, type, fn, opts]); }
const exploring = () => S.app && S.app.time.mode === 'explore' && !ui.modal;

function onPointerDown(e) {
  if (!exploring()) return;
  const c = S.app.canvas;
  try { c.setPointerCapture(e.pointerId); } catch (err) { /* synthetic events */ }
  S.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (S.pointers.size === 1) {
    const pan = e.button === 2 || e.button === 1 || (e.button === 0 && (e.shiftKey || e.ctrlKey || e.metaKey));
    S.drag = { mode: pan ? 'pan' : 'rotate', x0: e.clientX, y0: e.clientY, t0: e.timeStamp, moved: 0, type: e.pointerType };
  } else if (S.pointers.size === 2) {
    const [a, b] = [...S.pointers.values()];
    S.drag = { mode: 'touch2', moved: 99, lastDist: Math.hypot(a.x - b.x, a.y - b.y), lastCx: (a.x + b.x) / 2, lastCy: (a.y + b.y) / 2, type: e.pointerType };
  }
  if (e.pointerType !== 'touch') e.preventDefault();
}
function onPointerMove(e) {
  const p = S.pointers.get(e.pointerId);
  if (!p || !S.drag) return;
  const dx = e.clientX - p.x, dy = e.clientY - p.y;
  p.x = e.clientX; p.y = e.clientY;
  const d = S.drag, inp = S.in;
  if (d.mode === 'touch2' && S.pointers.size >= 2) {
    const [a, b] = [...S.pointers.values()];
    const nd = Math.hypot(a.x - b.x, a.y - b.y), cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
    if (d.lastDist > 0 && nd > 0) inp.pinch += Math.log(d.lastDist / nd);
    inp.panX += cx - d.lastCx; inp.panY += cy - d.lastCy;
    d.lastDist = nd; d.lastCx = cx; d.lastCy = cy;
    inp.source = 'touch';
    return;
  }
  d.moved += Math.abs(dx) + Math.abs(dy);
  if (d.moved < TUNE.clickPx) return;
  if (d.mode === 'rotate') { inp.rotX += dx; inp.rotY += dy; } else { inp.panX += dx; inp.panY += dy; }
  inp.source = e.pointerType === 'touch' ? 'touch' : 'pointer';
}
function onPointerUp(e) {
  const had = S.pointers.delete(e.pointerId);
  try { S.app.canvas.releasePointerCapture(e.pointerId); } catch (err) { /* ignore */ }
  const d = S.drag;
  if (!had || !d) return;
  if (S.pointers.size === 0) {
    if (e.type === 'pointerup' && d.mode !== 'touch2' && d.moved < TUNE.clickPx && e.timeStamp - d.t0 < TUNE.clickMs && e.button !== 2) {
      const r = S.app.canvas.getBoundingClientRect();
      S.app.events.emit('view-click', { x: e.clientX - r.left, y: e.clientY - r.top, pointerType: e.pointerType });
    }
    S.drag = null;
  } else if (S.pointers.size === 1) {
    const [a] = [...S.pointers.values()];
    S.drag = { mode: 'rotate', x0: a.x, y0: a.y, t0: e.timeStamp, moved: 99, type: e.pointerType };
  }
}
function onWheel(e) {
  if (!exploring()) return;
  e.preventDefault();
  const unit = e.deltaMode === 1 ? 32 : e.deltaMode === 2 ? 600 : 1;
  S.in.zoom += clamp(e.deltaY * unit, -600, 600) * (e.ctrlKey ? 3 : 1);
  S.in.source = 'wheel';
}
function onDblClick(e) {
  if (!exploring()) return;
  const app = S.app, r = app.canvas.getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  S.proj.update(app);
  const hit = pickEntity(app, S.proj, x, y, { radius: 34 });
  if (hit) {
    focus(hit.id, { follow: hit.kind === 'aircraft' });
    app.events.emit('view-pick', { id: hit.id, x, y });
  } else {
    const d = S.proj.ray(x, y, _dir), t = groundHit(app.camera.position, d);
    if (t > 0) { _v2.copy(app.camera.position).addScaledVector(d, t); focus(_v2.clone(), {}); }
  }
  takeUserControl('pointer'); S.user = true;
}
const FLY_KEYS = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyQ', 'KeyE', 'ArrowUp', 'ArrowDown']);
function onKeyDown(e) {
  if (!exploring() || isTypingTarget(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;
  if (FLY_KEYS.has(e.code)) { S.keys.add(e.code); e.preventDefault(); return; }
  if (e.code === 'BracketLeft' || e.code === 'BracketRight') {
    if (S.passive) adopt();
    S.fovGoal = clamp(S.fovGoal + (e.code === 'BracketLeft' ? -TUNE.fovStep : TUNE.fovStep), TUNE.minFov, TUNE.maxFov);
    takeUserControl('key'); e.preventDefault();
  } else if (e.code === 'KeyV' && S.followId) {
    setFollowFrame(S.followFrame === 'heading' ? 'world' : 'heading'); e.preventDefault();
  }
}
function onKeyUp(e) { S.keys.delete(e.code); }

// ---- per-frame ------------------------------------------------------------------------------------
function update(app) {
  if (app.time.mode !== 'explore') {       // the director owns the camera
    S.passive = true; S.trans = null; S.keys.clear();
    S.in.rotX = S.in.rotY = S.in.panX = S.in.panY = S.in.zoom = S.in.pinch = 0; S.in.source = null;
    return;
  }
  const cam = app.camera, dt = app.time.dt, inp = S.in;
  // someone else placed the camera (setCamera / lookAtEntity / the director's last frame): hands off
  if (!S.passive && (!cam.position.equals(S.lastPos) || !cam.quaternion.equals(S.lastQuat) || cam.fov !== S.lastFov)) {
    S.passive = true; S.trans = null; S.followId = null; S.dirty = false;
  }
  const flying = S.keys.size > 0 && !ui.modal;
  const hasInput = inp.rotX || inp.rotY || inp.panX || inp.panY || inp.zoom || inp.pinch || flying;
  if (S.passive) {
    if (!hasInput && !ui.attract) return;
    adopt();
  }
  if (hasInput) takeUserControl(flying && !inp.source ? 'key' : inp.source || 'pointer');

  const d = dist();
  const following = !!S.followId && !!entity(S.followId);
  if (S.followId && !following) { S.followId = null; }

  // ---- rotate (direct while dragging, inertia afterwards) ----
  if (inp.rotX || inp.rotY) {
    const da = inp.rotX * TUNE.rotate, de = inp.rotY * TUNE.rotate;
    S.az += da; S.el += de;
    if (dt > 0) { const k = 1 - Math.exp(-30 * dt); S.vAz += (da / dt - S.vAz) * k; S.vEl += (de / dt - S.vEl) * k; }
  } else if (!(S.drag && S.drag.mode === 'rotate')) {
    S.az += S.vAz * dt; S.el += S.vEl * dt;
    const k = Math.exp(-TUNE.rotDamp * dt); S.vAz *= k; S.vEl *= k;
  } else { const k = Math.exp(-20 * dt); S.vAz *= k; S.vEl *= k; }   // holding still: no fling on release
  if (ui.attract) S.az += TUNE.attractRate * dt;
  S.el = clamp(S.el, following || S.lift > 1 ? -85 : 0.5, 89);

  // ---- dolly (exponential, smoothed in log space) ----
  if (inp.zoom || inp.pinch) S.logDistGoal = clamp(S.logDistGoal + inp.zoom * TUNE.wheel + inp.pinch, Math.log(TUNE.minDist), Math.log(TUNE.maxDist));
  S.logDist += (S.logDistGoal - S.logDist) * (1 - Math.exp(-TUNE.dollyDamp * dt));
  if (ui.instant) S.logDist = S.logDistGoal;
  S.fov += (S.fovGoal - S.fov) * (ui.instant ? 1 : 1 - Math.exp(-TUNE.fovDamp * dt));

  // ---- pan + fly: move the focus point ----
  const a = worldAz() * DEG;
  // camera-right and camera-forward on the horizontal plane (camera sits at bearing `a` from the target)
  const rx = -Math.cos(a), rz = -Math.sin(a);           // right
  const fx = -Math.sin(a), fz = Math.cos(a);            // forward (from the camera toward the target)
  const mpp = (2 * d * Math.tan((S.fov * DEG) / 2)) / Math.max(1, S.proj.h || app.canvas.clientHeight || 720); // metres per pixel at the focus
  const move = _v3.set(0, 0, 0);
  if (inp.panX || inp.panY) {
    const s = Math.sin(clamp(S.el, 0, 90) * DEG);
    const ground = s > 0.26;                             // steeper than ~15 deg: drag the ground; flatter: drag in the screen plane
    const px = -inp.panX * mpp, py = inp.panY * mpp;
    move.x += rx * px; move.z += rz * px;
    if (ground) { const g = py / Math.max(s, 0.26); move.x += fx * g; move.z += fz * g; } else move.y += py;
    if (dt > 0) { const k = 1 - Math.exp(-30 * dt); S.vPan.x += (move.x / dt - S.vPan.x) * k; S.vPan.y += (move.y / dt - S.vPan.y) * k; S.vPan.z += (move.z / dt - S.vPan.z) * k; }
  } else if (!S.drag) {
    move.addScaledVector(S.vPan, dt);
    S.vPan.multiplyScalar(Math.exp(-TUNE.panDamp * dt));
  } else S.vPan.multiplyScalar(Math.exp(-20 * dt));

  // keyboard fly (velocity eased toward the commanded one)
  const K = S.keys;
  const cf = (K.has('KeyW') || K.has('ArrowUp') ? 1 : 0) - (K.has('KeyS') || K.has('ArrowDown') ? 1 : 0);
  const cr = (K.has('KeyD') ? 1 : 0) - (K.has('KeyA') ? 1 : 0);
  const cu = (K.has('KeyE') ? 1 : 0) - (K.has('KeyQ') ? 1 : 0);
  const speed = Math.max(TUNE.flyMin, d * TUNE.flySpeed) * (K.has('ShiftLeft') || K.has('ShiftRight') || S.shift ? TUNE.flyFast : 1);
  _v2.set((fx * cf + rx * cr) * speed, cu * speed * 0.6, (fz * cf + rz * cr) * speed);
  S.vFly.lerp(_v2, 1 - Math.exp(-TUNE.flyDamp * dt));
  if (S.vFly.lengthSq() > 1e-6) move.addScaledVector(S.vFly, dt);

  if (move.lengthSq() > 0) {
    if (following && flying) follow(null);               // flying away releases the followed entity
    if (S.followId) S.followOffset.add(move);
    else {
      S.target.x += move.x; S.target.z += move.z;
      S.lift = Math.max(0, S.lift + move.y);
    }
  }
  if (!S.followId) S.target.y = groundAt(S.target.x, S.target.z) + S.lift;

  // ---- followed entity heading (smoothed; snapped after a time jump) ----
  if (S.followId) {
    const h = entityHeading(entity(S.followId), app.time.sim);
    const jumped = Math.abs(app.time.sim - S.lastSim) > Math.max(3, Math.abs(app.time.simRate) * 0.5);
    if (h == null) { /* keep the last heading */ } else if (!S.headingValid || jumped || ui.instant) {
      if (!S.headingValid && S.followFrame === 'heading') S.az -= h;
      S.heading = h; S.headingValid = true;
    } else S.heading += angleDiff(S.heading, h) * (1 - Math.exp(-TUNE.headingDamp * dt));
  }
  S.lastSim = app.time.sim;

  // ---- transition ----
  if (S.trans) { S.trans.u += dt / S.trans.dur; if (S.trans.u >= 1) S.trans = null; }

  inp.rotX = inp.rotY = inp.panX = inp.panY = inp.zoom = inp.pinch = 0; inp.source = null;
  S.dirty = false;
  writeCamera();
}

export default {
  id: 'controls',
  order: 5,
  tune: TUNE,
  async init(app) {
    S.app = app;
    ui.instant = ui.instant || app.params.bool('manual');
    const c = app.canvas;
    listen(c, 'pointerdown', onPointerDown);
    listen(c, 'pointermove', onPointerMove);
    listen(c, 'pointerup', onPointerUp);
    listen(c, 'pointercancel', onPointerUp);
    listen(c, 'wheel', onWheel, { passive: false });
    listen(c, 'dblclick', onDblClick);
    listen(c, 'contextmenu', (e) => e.preventDefault());
    listen(window, 'keydown', (e) => { S.shift = e.shiftKey; onKeyDown(e); });
    listen(window, 'keyup', (e) => { S.shift = e.shiftKey; onKeyUp(e); });
    listen(window, 'blur', () => { S.keys.clear(); S.shift = false; });
    S.offMode = app.events.on('mode', () => { S.passive = true; S.trans = null; S.followId = null; S.keys.clear(); });
  },
  update,
  focus, follow, setFollowFrame, getState, setState,
  /** true while the camera is animating by itself (fly-to or inertia) */
  get busy() { return !!S.trans; },
  get followId() { return S.followId; },
  get followFrame() { return S.followFrame; },
  dispose() {
    for (const [t, type, fn, opts] of S.handlers) t.removeEventListener(type, fn, opts);
    S.handlers.length = 0;
    if (S.offMode) S.offMode();
  },
};
