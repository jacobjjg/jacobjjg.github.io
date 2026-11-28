#!/usr/bin/env node
// Offline frame-by-frame capture of the documentary (or of an explore-mode time span) to a video file.
// Deterministic: every frame advances the clock by exactly 1/fps, however long it takes to render.
//
//   node tools/capture.mjs --out film.mp4 --from 0 --to 60 --fps 24 --w 1280 --h 720 --q medium
//   node tools/capture.mjs --out arizona.mp4 --t 08:09:50 --dur 30 --look arizona,900,160,12 --fps 24      (explore mode, real time)
//   node tools/capture.mjs --out lapse.mp4 --t 07:40 --dur 20 --rate 60 --cam "x,y,z,tx,ty,tz,fov"         (explore mode, 60x)
//
// Options: --from/--to documentary seconds (doc mode)  |  --t sim time + --dur seconds + --rate sim s per s (explore mode)
//          --fps 24  --w 1280 --h 720  --q low|medium|high|ultra  --pr 1  --crf 18  --keep (keep the JPEG frames)
//          --sys a,b  --nosys a,b  --query "extra=1"  --frames-dir DIR  --jpeg 92  --timeout SEC per frame (default 600)
// Needs ffmpeg on PATH.  Software GL is slow: budget several seconds per frame.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav', '.bin': 'application/octet-stream' };

const o = {};
{ const a = process.argv.slice(2); for (let i = 0; i < a.length; i++) if (a[i].startsWith('--')) { const k = a[i].slice(2); o[k] = (i + 1 < a.length && !a[i + 1].startsWith('--')) ? a[++i] : true; } }
const W = +(o.w || 1280), H = +(o.h || 720), FPS = +(o.fps || 24);
const out = path.resolve(o.out || 'capture.mp4');
const framesDir = path.resolve(o['frames-dir'] || fs.mkdtempSync(path.join(os.tmpdir(), 'ph-capture-')));
fs.mkdirSync(framesDir, { recursive: true });
const docMode = o.t == null;
const from = +(o.from || 0), to = +(o.to || from + 10), dur = docMode ? to - from : +(o.dur || 10);
const total = Math.max(1, Math.round(dur * FPS));
const timeout = +(o.timeout || 600) * 1000;

const server = await new Promise((resolve) => {
  const s = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (p.endsWith('/')) p += 'index.html';
    const file = path.join(ROOT, p);
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    if (req.method === 'HEAD') { res.end(); return; }
    fs.createReadStream(file).pipe(res);
  });
  s.listen(0, '127.0.0.1', () => resolve(s));
});

const q = new URLSearchParams(o.query || '');
q.set('manual', '1'); q.set('capture', '1');
if (!docMode) q.set('dev', '1');
q.set('q', o.q || 'medium'); q.set('pr', o.pr || '1');
for (const k of ['sys', 'nosys', 'scene']) if (o[k]) q.set(k, o[k]);
if (docMode) q.set('doc', String(from)); else q.set('t', o.t);
const url = `http://127.0.0.1:${server.address().port}/index.html?${q}`;

const { chromium } = require('playwright');
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--use-gl=angle', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--mute-audio'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.error('[pageerror]', e.message));
await page.goto(url, { waitUntil: 'load', timeout });
await page.waitForFunction('window.__ph && window.__ph.ready', null, { timeout });
await page.evaluate(() => window.__ph.ready);
await page.evaluate(({ docMode, from, t, rate, cam, look }) => {
  const ph = window.__ph, app = ph.app;
  document.getElementById('loader')?.remove();
  if (docMode) { app.seekDoc(from); }
  else {
    app.seekSim(t); app.time.simRate = rate;
    ph.frames(1, 0);
    if (cam) app.setCamera(cam.slice(0, 3), cam.slice(3, 6), cam[6]);
    if (look) app.lookAtEntity(look[0], { dist: +look[1] || 800, az: look[2] != null ? +look[2] : 135, el: look[3] != null ? +look[3] : 15, fov: look[4] ? +look[4] : undefined });
  }
  app.play();
  ph.frames(2, 0); // settle (env map, shadow fit) without advancing time
}, { docMode, from, t: o.t, rate: +(o.rate || 1), cam: o.cam ? o.cam.split(',').map(Number) : null, look: o.look ? o.look.split(',') : null });

const t0 = Date.now();
const quality = +(o.jpeg || 92);
for (let i = 0; i < total; i++) {
  await page.evaluate((dt) => { window.__ph.app.frame(dt); }, i === 0 ? 0 : 1 / FPS);
  await page.screenshot({ path: path.join(framesDir, `f${String(i).padStart(6, '0')}.jpg`), type: 'jpeg', quality, timeout });
  if (i % 24 === 0 || i === total - 1) {
    const el = (Date.now() - t0) / 1000, per = el / (i + 1);
    process.stdout.write(`frame ${i + 1}/${total}  ${per.toFixed(2)} s/frame  eta ${Math.round(per * (total - i - 1))} s\n`);
  }
}
const errors = await page.evaluate(() => window.__ph.errors.slice());
await browser.close();
server.close();
if (errors.length) console.error('page errors:\n' + errors.join('\n'));

fs.mkdirSync(path.dirname(out), { recursive: true });
const ff = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(framesDir, 'f%06d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', String(o.crf || 18), '-movflags', '+faststart', out], { stdio: 'inherit' });
if (ff.status !== 0) { console.error('ffmpeg failed; frames kept in ' + framesDir); process.exit(1); }
if (!o.keep && !o['frames-dir']) fs.rmSync(framesDir, { recursive: true, force: true });
console.log(`wrote ${out}  (${total} frames, ${(dur).toFixed(1)} s at ${FPS} fps)`);
