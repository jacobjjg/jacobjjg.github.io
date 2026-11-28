// Headless (node) stand-in for the parts of `app` that pure simulation logic needs:
// geo, time helpers, the terrain heightfield (decoded from the PNG rasters with zlib - no canvas),
// a registry, an event emitter and JSON loading.  No renderer, no DOM.
//
//   import { createNodeApp } from './node-env.mjs';
//   const app = await createNodeApp();          // app.height.at(x,z), app.registry, app.loadJSON('data/x.json') ...
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';
import * as THREE from 'three';
import * as geo from '../src/core/geo.js';
import { Emitter, Registry, QUALITY_TIERS } from '../src/core/util.js';
import { HeightField } from '../src/core/heightfield.js';
import { T } from '../src/core/timeutil.js';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/** Minimal PNG decoder for 8-bit greyscale / RGB / RGBA, non-interlaced. Returns { w, h, channels, data: Uint8Array }. */
export function decodePNG(file) {
  const buf = fs.readFileSync(file);
  let p = 8, w = 0, h = 0, depth = 0, ctype = 0, interlace = 0;
  const idat = [];
  while (p < buf.length) {
    const len = buf.readUInt32BE(p), type = buf.toString('ascii', p + 4, p + 8), d = buf.subarray(p + 8, p + 8 + len);
    if (type === 'IHDR') { w = d.readUInt32BE(0); h = d.readUInt32BE(4); depth = d[8]; ctype = d[9]; interlace = d[12]; }
    else if (type === 'IDAT') idat.push(d);
    else if (type === 'IEND') break;
    p += 12 + len;
  }
  if (depth !== 8 || interlace !== 0 || ![0, 2, 6].includes(ctype)) throw new Error(`${file}: unsupported PNG (depth ${depth}, colour type ${ctype}, interlace ${interlace})`);
  const ch = ctype === 0 ? 1 : ctype === 2 ? 3 : 4, stride = w * ch;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const out = new Uint8Array(w * h * ch);
  let prev = new Uint8Array(stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)], line = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1)), cur = out.subarray(y * stride, (y + 1) * stride);
    for (let x = 0; x < stride; x++) {
      const a = x >= ch ? cur[x - ch] : 0, b = prev[x], c = x >= ch ? prev[x - ch] : 0;
      let v = line[x];
      if (f === 1) v += a; else if (f === 2) v += b; else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) { const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      cur[x] = v & 255;
    }
    prev = cur;
  }
  return { w, h, channels: ch, data: out };
}

function loadHeightRaster(names, rect) {
  for (const n of names) {
    const file = path.join(ROOT, 'assets/geo', n);
    if (!fs.existsSync(file)) continue;
    const { w, h, channels, data } = decodePNG(file);
    const heights = new Float32Array(w * h), water = new Uint8Array(w * h);
    for (let i = 0, j = 0; i < w * h; i++, j += channels) { heights[i] = (data[j] * 256 + data[j + 1]) * 0.05 - 600; water[i] = data[j + 2] > 127 ? 1 : 0; }
    return { w, h, rect, heights, water, synthetic: false, file: n };
  }
  return null;
}

export async function createNodeApp({ requireTerrain = false } = {}) {
  const height = new HeightField();
  const island = loadHeightRaster(['island_height41.png', 'island_height.png'], geo.RECT_ISLAND);
  const harbor = loadHeightRaster(['harbor_height41.png', 'harbor_height.png'], geo.RECT_HARBOR);
  if (island && harbor) { height.rasters.island = island; height.rasters.harbor = harbor; height.synthetic = false; }
  else if (requireTerrain) throw new Error('terrain rasters missing in assets/geo');
  const data = {};
  const app = {
    THREE, geo, node: true, dev: true,
    events: new Emitter(), registry: new Registry(), height, data, plan: null,
    quality: { ...QUALITY_TIERS.high },
    time: { sim: T('07:55'), prevSim: T('07:55'), dSim: 0, scale: 1, doc: 0, visual: 0, dt: 0, frame: 0, mode: 'explore', playing: false, jumped: true },
    env: { wind: new THREE.Vector3(-4.3, 0, 2.5), sunDir: new THREE.Vector3(0.8, 0.3, 0.5).normalize() },
    _systems: new Map(),
    getSystem(id) { return this._systems.get(id) || null; },
    asset: (rel) => path.join(ROOT, rel),
    async loadJSON(rel) { if (!data[rel]) data[rel] = JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8')); return data[rel]; },
  };
  return app;
}
