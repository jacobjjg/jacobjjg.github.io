// Event emitter, entity registry, URL params, quality tiers.
import * as THREE from 'three';
import { toWorld } from './geo.js';

export class Emitter {
  constructor() { this._l = new Map(); }
  on(type, fn) { if (!this._l.has(type)) this._l.set(type, new Set()); this._l.get(type).add(fn); return () => this.off(type, fn); }
  off(type, fn) { this._l.get(type)?.delete(fn); }
  emit(type, payload) {
    const s = this._l.get(type);
    if (s) for (const fn of [...s]) { try { fn(payload); } catch (e) { console.error(`[event ${type}]`, e); } }
  }
}

/**
 * ENTITY - anything the camera, labels, audio or UI may refer to by id.
 * Required shape (plain object, duck-typed):
 *   {
 *     id: 'arizona',                 // unique, lowercase snake_case
 *     kind: 'ship' | 'aircraft' | 'place' | 'person' | 'group',
 *     side: 'us' | 'jp' | 'civ' | null,
 *     name: 'USS Arizona (BB-39)',   // display name
 *     getPosition(t, out) -> out,    // world position (metres) at sim time t; must be a pure function of t
 *     // optional:
 *     getQuaternion(t, out) -> out,  // model orientation at t
 *     getVelocity(t, out) -> out,    // m/s
 *     isActive(t) -> bool,           // exists / should be shown at t (default true)
 *     radius: Number,                // approximate size in metres (for framing)
 *     info: { ... }                  // free-form facts for info cards
 *   }
 */
export class Registry {
  constructor() { this.byId = new Map(); this.byKind = new Map(); }
  add(entity) {
    if (!entity || !entity.id) throw new Error('entity needs an id');
    if (this.byId.has(entity.id)) console.warn(`[registry] duplicate id ${entity.id} - replacing`);
    this.byId.set(entity.id, entity);
    if (!this.byKind.has(entity.kind)) this.byKind.set(entity.kind, []);
    const list = this.byKind.get(entity.kind);
    const i = list.findIndex((e) => e.id === entity.id);
    if (i >= 0) list[i] = entity; else list.push(entity);
    return entity;
  }
  get(id) { return this.byId.get(id) || null; }
  has(id) { return this.byId.has(id); }
  list(kind) { return kind ? (this.byKind.get(kind) || []) : [...this.byId.values()]; }
  /** Convenience: a fixed place from lat/lon. */
  addPlace(id, name, lat, lon, alt = 0, extra = {}) {
    const p = toWorld(lat, lon, alt);
    return this.add({ id, kind: 'place', side: null, name, radius: 200, getPosition: (_t, out = new THREE.Vector3()) => out.copy(p), isActive: () => true, info: {}, ...extra });
  }
  /** Convenience: a fixed place from world coordinates. */
  addPoint(id, name, x, y, z, extra = {}) {
    const p = new THREE.Vector3(x, y, z);
    return this.add({ id, kind: 'place', side: null, name, radius: 200, getPosition: (_t, out = new THREE.Vector3()) => out.copy(p), isActive: () => true, info: {}, ...extra });
  }
}

/** URL query parameters as an object with typed accessors. */
export function parseParams(search = (typeof location !== 'undefined' ? location.search : '')) {
  const q = new URLSearchParams(search);
  return {
    raw: q,
    has: (k) => q.has(k),
    str: (k, d = null) => (q.has(k) ? q.get(k) : d),
    num: (k, d = null) => (q.has(k) && q.get(k) !== '' && Number.isFinite(+q.get(k)) ? +q.get(k) : d),
    bool: (k, d = false) => (q.has(k) ? !['0', 'false', 'off', 'no'].includes(q.get(k)) : d),
    list: (k) => (q.has(k) && q.get(k) !== '' ? q.get(k).split(',').map((s) => s.trim()).filter(Boolean) : null),
    nums: (k) => (q.has(k) ? q.get(k).split(',').map(Number) : null),
  };
}

/**
 * QUALITY TIERS.  Systems read app.quality.<field>; never hard-code budgets.
 *   particles / crowd / foliage: multipliers on a system's nominal counts
 *   oceanDetail / terrainDetail / cloudDetail: 0..1.5 mesh+shader detail multipliers
 */
export const QUALITY_TIERS = {
  low:    { tier: 'low',    pixelRatio: 1.0,  maxPixels: 1280 * 720,  msaa: 0, shadows: false, shadowMap: 1024, particles: 0.3, crowd: 0.3, foliage: 0.3, oceanDetail: 0.5,  terrainDetail: 0.5,  cloudDetail: 0.5,  bloom: false, post: true, anisotropy: 2,  envMapSize: 64 },
  medium: { tier: 'medium', pixelRatio: 1.0,  maxPixels: 1920 * 1080, msaa: 2, shadows: true,  shadowMap: 2048, particles: 0.6, crowd: 0.6, foliage: 0.6, oceanDetail: 0.75, terrainDetail: 0.75, cloudDetail: 0.75, bloom: true,  post: true, anisotropy: 4,  envMapSize: 128 },
  high:   { tier: 'high',   pixelRatio: 1.5,  maxPixels: 2560 * 1440, msaa: 4, shadows: true,  shadowMap: 4096, particles: 1.0, crowd: 1.0, foliage: 1.0, oceanDetail: 1.0,  terrainDetail: 1.0,  cloudDetail: 1.0,  bloom: true,  post: true, anisotropy: 8,  envMapSize: 256 },
  ultra:  { tier: 'ultra',  pixelRatio: 2.0,  maxPixels: 3840 * 2160, msaa: 4, shadows: true,  shadowMap: 4096, particles: 1.6, crowd: 1.5, foliage: 1.5, oceanDetail: 1.5,  terrainDetail: 1.5,  cloudDetail: 1.5,  bloom: true,  post: true, anisotropy: 16, envMapSize: 256 },
};

export function detectQuality(renderer, requested) {
  if (requested && QUALITY_TIERS[requested]) return { ...QUALITY_TIERS[requested] };
  let tier = 'high';
  try {
    const gl = renderer.getContext();
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    const name = (ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)) || '';
    const mobile = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent);
    if (/SwiftShader|llvmpipe|Software|Basic Render/i.test(name)) tier = 'low';
    else if (mobile) tier = 'medium';
    else if (/Intel|UHD|Iris|HD Graphics/i.test(name) && !/Arc/i.test(name)) tier = 'medium';
    else if (/Apple M|Apple GPU/i.test(name)) tier = 'high';
  } catch (e) { /* keep default */ }
  return { ...QUALITY_TIERS[tier] };
}
