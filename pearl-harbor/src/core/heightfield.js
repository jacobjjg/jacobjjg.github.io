// Terrain / bathymetry sampling from the baked rasters in assets/geo/.
//
//   app.height.at(x, z)        elevation in metres (negative = sea floor), bilinear
//   app.height.isWater(x, z)   true where the surface is sea / harbor water
//   app.height.depth(x, z)     water depth in metres (0 on land)
//   app.height.normal(x, z, out)
//   app.height.raster('island' | 'harbor')  -> { w, h, rect, heights: Float32Array, water: Uint8Array }
//   app.height.texture('island' | 'harbor') -> THREE.DataTexture, RG half-float: R = metres, G = water (0..1)
//
// Height PNG encoding: v = R*256 + G ; metres = v*0.05 - 600 ; B = 255 on water.
import * as THREE from 'three';
import { RECT_ISLAND, RECT_HARBOR } from './geo.js';
import { fbm2 } from './noise.js';

const DEEP = -600;

async function decodePNG(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const blob = await res.blob();
  const bmp = await createImageBitmap(blob, { premultiplyAlpha: 'none', colorSpaceConversion: 'none' });
  const w = bmp.width, h = bmp.height;
  const canvas = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(w, h) : Object.assign(document.createElement('canvas'), { width: w, height: h });
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(bmp, 0, 0);
  const px = ctx.getImageData(0, 0, w, h).data;
  bmp.close?.();
  return { w, h, px };
}

function decodeHeight({ w, h, px }, rect) {
  const heights = new Float32Array(w * h);
  const water = new Uint8Array(w * h);
  for (let i = 0, j = 0; i < w * h; i++, j += 4) {
    heights[i] = (px[j] * 256 + px[j + 1]) * 0.05 - 600;
    water[i] = px[j + 2] > 127 ? 1 : 0;
  }
  return { w, h, rect, heights, water, synthetic: false };
}

/** Stand-in island used only when the real rasters are missing (keeps dev sandboxes alive). */
function synthetic(rect, w, h) {
  const heights = new Float32Array(w * h), water = new Uint8Array(w * h);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) {
      const x = rect.x0 + (i + 0.5) * (rect.x1 - rect.x0) / w, z = rect.z0 + (j + 0.5) * (rect.z1 - rect.z0) / h;
      const cx = (x + 2000) / 30000, cz = (z + 13000) / 24000;
      const r = Math.hypot(cx, cz);
      let e = (1 - r) * 500 + (fbm2(x / 6000, z / 6000, 5) - 0.5) * 700;
      // carve a harbor-like basin around the origin
      const hb = Math.hypot(x / 3500, (z - 500) / 3000);
      if (hb < 1) e = Math.min(e, -12 * (1 - hb) - 0.5);
      const fi = Math.hypot(x / 900, z / 600); if (fi < 1) e = 4; // "Ford Island"
      heights[j * w + i] = Math.max(DEEP, e < 0.5 && e > -0.5 ? (e < 0 ? -0.5 : 0.5) : e);
      water[j * w + i] = heights[j * w + i] < 0 ? 1 : 0;
    }
  }
  return { w, h, rect, heights, water, synthetic: true };
}

function sample(r, x, z) {
  const fx = (x - r.rect.x0) / (r.rect.x1 - r.rect.x0) * r.w - 0.5;
  const fz = (z - r.rect.z0) / (r.rect.z1 - r.rect.z0) * r.h - 0.5;
  const i0 = Math.max(0, Math.min(r.w - 1, Math.floor(fx))), j0 = Math.max(0, Math.min(r.h - 1, Math.floor(fz)));
  const i1 = Math.min(r.w - 1, i0 + 1), j1 = Math.min(r.h - 1, j0 + 1);
  const u = Math.max(0, Math.min(1, fx - i0)), v = Math.max(0, Math.min(1, fz - j0));
  const H = r.heights, w = r.w;
  const a = H[j0 * w + i0], b = H[j0 * w + i1], c = H[j1 * w + i0], d = H[j1 * w + i1];
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
function sampleWater(r, x, z) {
  const i = Math.max(0, Math.min(r.w - 1, Math.floor((x - r.rect.x0) / (r.rect.x1 - r.rect.x0) * r.w)));
  const j = Math.max(0, Math.min(r.h - 1, Math.floor((z - r.rect.z0) / (r.rect.z1 - r.rect.z0) * r.h)));
  return r.water[j * r.w + i] === 1;
}
const inside = (rect, x, z, margin = 0) => x >= rect.x0 + margin && x <= rect.x1 - margin && z >= rect.z0 + margin && z <= rect.z1 - margin;

export class HeightField {
  constructor() {
    this.rasters = {};
    this.textures = {};
    this.synthetic = true;
    this.feather = 400; // metres over which the harbor raster blends into the island raster at its edge
  }

  /** baseUrl ends with '/'.  Tries the 1941-corrected rasters first. */
  async load(baseUrl, { lowMemory = false } = {}) {
    const tryLoad = async (names, rect, fw, fh) => {
      for (const n of names) {
        try { return decodeHeight(await decodePNG(baseUrl + n), rect); } catch (e) { /* try next */ }
      }
      console.warn(`[height] ${names[0]} not found - using synthetic stand-in terrain`);
      return synthetic(rect, fw, fh);
    };
    const [island, harbor] = await Promise.all([
      tryLoad(['island_height41.png', 'island_height.png'], RECT_ISLAND, lowMemory ? 320 : 640, lowMemory ? 256 : 512),
      tryLoad(['harbor_height41.png', 'harbor_height.png'], RECT_HARBOR, 512, 512),
    ]);
    this.rasters.island = island;
    this.rasters.harbor = harbor;
    this.synthetic = island.synthetic || harbor.synthetic;
    return this;
  }

  raster(name) { return this.rasters[name]; }

  at(x, z) {
    const isl = this.rasters.island, har = this.rasters.harbor;
    if (!isl) return 0;
    if (har && inside(har.rect, x, z)) {
      const hh = sample(har, x, z);
      const r = har.rect;
      const edge = Math.min(x - r.x0, r.x1 - x, z - r.z0, r.z1 - z);
      if (edge >= this.feather) return hh;
      const k = edge / this.feather;
      return sample(isl, x, z) * (1 - k) + hh * k;
    }
    if (inside(isl.rect, x, z)) return sample(isl, x, z);
    return DEEP;
  }

  isWater(x, z) {
    const isl = this.rasters.island, har = this.rasters.harbor;
    if (!isl) return true;
    if (har && inside(har.rect, x, z)) return sampleWater(har, x, z);
    if (inside(isl.rect, x, z)) return sampleWater(isl, x, z);
    return true;
  }

  depth(x, z) { return Math.max(0, -this.at(x, z)); }

  normal(x, z, out = new THREE.Vector3(), eps = 12) {
    const hx = this.at(x + eps, z) - this.at(x - eps, z);
    const hz = this.at(x, z + eps) - this.at(x, z - eps);
    return out.set(-hx, 2 * eps, -hz).normalize();
  }

  /** RG half-float texture (R = metres, G = water mask) for shaders; created lazily. uv = (x - x0)/(x1 - x0), (z - z0)/(z1 - z0). */
  texture(name) {
    if (this.textures[name]) return this.textures[name];
    const r = this.rasters[name];
    const data = new Uint16Array(r.w * r.h * 2);
    for (let i = 0; i < r.w * r.h; i++) {
      data[i * 2] = THREE.DataUtils.toHalfFloat(r.heights[i]);
      data[i * 2 + 1] = THREE.DataUtils.toHalfFloat(r.water[i]);
    }
    const tex = new THREE.DataTexture(data, r.w, r.h, THREE.RGFormat, THREE.HalfFloatType);
    tex.minFilter = tex.magFilter = THREE.LinearFilter;
    tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.flipY = false;
    tex.generateMipmaps = false;
    tex.needsUpdate = true;
    return (this.textures[name] = tex);
  }
}
