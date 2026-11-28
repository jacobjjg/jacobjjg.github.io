// Shared UI state (module singleton used by hud.js and controls.js) + persisted settings +
// the frame-exact screen projector and entity picking used by labels, cards and controls.
import * as THREE from 'three';

/** Volatile UI state shared between the HUD and the camera controls. */
export const ui = {
  clock: 0,            // real seconds of UI time (sum of app.time.dt) - used for auto-hide, never for the 3D scene
  modal: false,        // an overlay owns the keyboard / pointer (opening card, help sheet)
  attract: false,      // opening card is up: controls slowly orbit the establishing view
  hidden: false,       // "H": all UI hidden
  instant: false,      // manual / capture mode: no fades (deterministic screenshots)
  selectedId: null,    // entity shown on the info card
  em: 14,              // base UI unit in CSS px (mirrors --ph-em)
  vw: 1280, vh: 720,
  lastActivity: -1e9,  // ui.clock of the last pointer / key activity
};

// ---- persisted settings ----------------------------------------------------------------------
const KEY = 'ph.settings.v1';
const TIERS = ['low', 'medium', 'high', 'ultra'];
const DEFAULTS = { sound: true, voice: true, subtitles: true, labels: true, map: true, quality: 'auto' };

function readStore() {
  try { const raw = window.localStorage.getItem(KEY); return raw ? JSON.parse(raw) : {}; } catch (e) { return {}; }
}
function writeStore(obj) {
  try { window.localStorage.setItem(KEY, JSON.stringify(obj)); } catch (e) { /* private mode / storage disabled: settings last for the session */ }
}

// A stored quality choice is applied by adding ?q= before the heavy systems initialise (this module is
// imported while main.js is still importing systems).  Never in dev / test URLs.
(function applyStoredQuality() {
  try {
    const p = new URLSearchParams(window.location.search);
    if (p.has('q')) return;
    for (const k of ['dev', 'sys', 't', 'cam', 'look', 'scene', 'manual', 'capture']) if (p.has(k)) return;
    const q = readStore().quality;
    if (q && TIERS.includes(q)) { p.set('q', q); window.location.replace(`${window.location.pathname}?${p}${window.location.hash}`); }
  } catch (e) { /* ignore */ }
})();

export class Settings {
  constructor(app) {
    this.app = app;
    const stored = readStore();
    this.values = { ...DEFAULTS };
    for (const k in DEFAULTS) if (typeof stored[k] === typeof DEFAULTS[k]) this.values[k] = stored[k];
    if (this.values.quality !== 'auto' && !TIERS.includes(this.values.quality)) this.values.quality = 'auto';
    this.listeners = new Set();
  }
  get(k) { return this.values[k]; }
  set(k, v) {
    if (!(k in DEFAULTS) || this.values[k] === v) return;
    this.values[k] = v;
    writeStore(this.values);
    this.emit();
  }
  toggle(k) { this.set(k, !this.values[k]); return this.values[k]; }
  /** { sound, voice, subtitles, labels, map } - the payload of the 'settings' event. */
  snapshot() { const { sound, voice, subtitles, labels, map } = this.values; return { sound, voice, subtitles, labels, map }; }
  emit() {
    const snap = this.snapshot();
    this.app.events.emit('settings', snap);
    for (const fn of this.listeners) fn(snap);
  }
  /** Persist a quality choice and reload with ?q= ('auto' removes the parameter). */
  setQuality(q) {
    this.values.quality = q === 'auto' || TIERS.includes(q) ? q : 'auto';
    writeStore(this.values);
    try {
      const p = new URLSearchParams(window.location.search);
      if (this.values.quality === 'auto') p.delete('q'); else p.set('q', this.values.quality);
      const qs = p.toString();
      window.location.assign(`${window.location.pathname}${qs ? '?' + qs : ''}${window.location.hash}`);
    } catch (e) { /* ignore */ }
  }
}

// ---- projector --------------------------------------------------------------------------------
const _q = new THREE.Quaternion();
const _v = new THREE.Vector3();

/**
 * Projects GLOBAL points to CSS pixels straight from camera.position / quaternion / fov, in double
 * precision and without depending on matrixWorld (which is one frame old when systems update).
 * Same result as app.project() on the frame that is about to be rendered.
 */
export class Projector {
  constructor() {
    this.cam = new THREE.Vector3();
    this.right = new THREE.Vector3(); this.up = new THREE.Vector3(); this.fwd = new THREE.Vector3();
    this.w = 1; this.h = 1; this.fx = 1; this.fy = 1; this.tanY = 1; this.tanX = 1;
  }
  update(app) {
    const c = app.camera;
    this.cam.copy(c.position);
    _q.copy(c.quaternion);
    this.right.set(1, 0, 0).applyQuaternion(_q);
    this.up.set(0, 1, 0).applyQuaternion(_q);
    this.fwd.set(0, 0, -1).applyQuaternion(_q);
    this.w = app.canvas.clientWidth || window.innerWidth;
    this.h = app.canvas.clientHeight || window.innerHeight;
    this.tanY = Math.tan((c.fov * Math.PI / 180) / 2) / (c.zoom || 1);
    this.tanX = this.tanY * (this.w / this.h);
    this.fy = (this.h / 2) / this.tanY;   // pixels per metre at 1 m depth
    this.fx = this.fy;
    return this;
  }
  /** out = { x, y (CSS px), depth (m along the view axis), visible } */
  project(p, out) {
    _v.set(p.x - this.cam.x, p.y - this.cam.y, p.z - this.cam.z);
    const d = _v.dot(this.fwd);
    out.depth = d;
    if (d <= 0.05) { out.x = -1e5; out.y = -1e5; out.visible = false; return out; }
    out.x = this.w / 2 + (_v.dot(this.right) / d) * this.fx;
    out.y = this.h / 2 - (_v.dot(this.up) / d) * this.fy;
    out.visible = out.x >= -0.05 * this.w && out.x <= 1.05 * this.w && out.y >= -0.05 * this.h && out.y <= 1.05 * this.h;
    return out;
  }
  /** Unit direction (global) of the view ray through CSS pixel (x, y). */
  ray(x, y, out = new THREE.Vector3()) {
    const nx = (x - this.w / 2) / this.fx, ny = -(y - this.h / 2) / this.fy;
    return out.copy(this.fwd).addScaledVector(this.right, nx).addScaledVector(this.up, ny).normalize();
  }
}

// ---- picking ----------------------------------------------------------------------------------
const _p = new THREE.Vector3();
const _o = { x: 0, y: 0, depth: 0, visible: false };

/**
 * Nearest projected entity to CSS pixel (x, y) within `radius` px (measured from the entity's projected
 * disc, so big ships are easy to hit).  Uses registry positions only - no raycasting.
 * opts: { radius = 30, filter(entity) }
 */
export function pickEntity(app, proj, x, y, opts = {}) {
  const radius = opts.radius || 30, t = app.time.sim;
  let best = null, bestScore = Infinity;
  for (const e of app.registry.byId.values()) {
    if (opts.filter && !opts.filter(e)) continue;
    try {
      if (e.isActive && !e.isActive(t)) continue;
      e.getPosition(t, _p);
    } catch (err) { continue; }
    proj.project(_p, _o);
    if (_o.depth <= 0.05) continue;
    const disc = e.kind === 'place' ? 14 : Math.min(70, Math.max(6, (e.radius || 10) * proj.fy / _o.depth));
    const d = Math.hypot(_o.x - x, _o.y - y) - disc;
    if (d > radius) continue;
    // inside several discs: prefer vehicles and people over places, then the nearer one
    const kindBias = e.kind === 'place' ? 18 : e.kind === 'group' ? 10 : 0;
    const score = Math.max(d, -10) + kindBias + Math.min(8, _o.depth * 2e-4);
    if (score < bestScore) { bestScore = score; best = e; }
  }
  return best;
}

/** Compass heading (deg true) of an entity at time t from its quaternion or velocity; null when unknown. */
const _f = new THREE.Vector3(), _eq = new THREE.Quaternion();
export function entityHeading(e, t) {
  try {
    if (e.getQuaternion) {
      e.getQuaternion(t, _eq);
      _f.set(0, 0, -1).applyQuaternion(_eq);
      if (Math.abs(_f.x) + Math.abs(_f.z) > 1e-4) return (Math.atan2(_f.x, -_f.z) * 180 / Math.PI + 360) % 360;
    }
    if (e.getVelocity) {
      e.getVelocity(t, _f);
      if (_f.x * _f.x + _f.z * _f.z > 0.04) return (Math.atan2(_f.x, -_f.z) * 180 / Math.PI + 360) % 360;
    }
    if (typeof e.state === 'function') { const s = e.state(t); if (s && Number.isFinite(s.heading)) return s.heading; }
  } catch (err) { /* fall through */ }
  return null;
}
