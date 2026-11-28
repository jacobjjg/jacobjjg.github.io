#!/usr/bin/env node
// Headless screenshot / smoke-test tool.  Serves pearl-harbor/ on an ephemeral port, opens the app in
// headless Chromium (software WebGL), positions time + camera, renders, saves PNGs and prints diagnostics.
//
//   node tools/shot.mjs --out /tmp/a.png --t 08:10 --look arizona,900,160,12
//   node tools/shot.mjs --out a.png --sys sky,ocean --cam "0,300,2000,0,0,0,40" --frames 3
//   node tools/shot.mjs --shots shots.json            # [{ "out": "...", "t": "07:55", "cam": [..], "look": [..], "doc": 12, "frames": 2, "eval": "js" }, ...]
//
// Options:
//   --out FILE         PNG path for a single shot           --shots FILE   JSON array of shots (one browser session)
//   --t HH:MM[:SS]     sim time (explore mode)               --doc SEC      documentary time (doc mode)
//   --cam x,y,z,tx,ty,tz[,fov]                               --look id[,dist,az,el[,fov]]
//   --sys a,b  --nosys a,b  --q low|medium|high|ultra  --scene dev/scenes/x.js  --query "extra=1&more=2"
//   --frames N (default 2)  --dt SEC advance per frame (default 0)  --w 1280 --h 720  --pr 1
//   --eval "js"        async function body run in the page before rendering; args (app, ph, THREE); a returned value is printed as evalResult
//   --timeout SEC (default 300)   --quiet
// Exit code 1 if the page reported errors.  Software rendering is slow: expect seconds per frame.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav', '.bin': 'application/octet-stream', '.md': 'text/markdown', '.woff2': 'font/woff2' };

function args() {
  const a = process.argv.slice(2), o = {};
  for (let i = 0; i < a.length; i++) {
    if (!a[i].startsWith('--')) continue;
    const k = a[i].slice(2);
    if (i + 1 < a.length && !a[i + 1].startsWith('--')) o[k] = a[++i]; else o[k] = true;
  }
  return o;
}

function serve() {
  const server = http.createServer((req, res) => {
    try {
      let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
      if (p.endsWith('/')) p += 'index.html';
      const file = path.join(ROOT, p);
      if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      if (req.method === 'HEAD') { res.end(); return; }
      fs.createReadStream(file).pipe(res);
    } catch (e) { res.writeHead(500); res.end(String(e)); }
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

const o = args();
const W = +(o.w || 1280), H = +(o.h || 720);
const timeout = +(o.timeout || 300) * 1000;
let shots;
if (o.shots) shots = JSON.parse(fs.readFileSync(o.shots, 'utf8'));
else shots = [{ out: o.out || 'shot.png', t: o.t, doc: o.doc, cam: o.cam, look: o.look, frames: o.frames, dt: o.dt, eval: o.eval }];

const q = new URLSearchParams(o.query || '');
q.set('manual', '1'); q.set('dev', '1');
for (const k of ['sys', 'nosys', 'q', 'scene', 'pr']) if (o[k]) q.set(k, o[k]);
if (!q.has('q')) q.set('q', 'low');
if (!q.has('pr')) q.set('pr', o.pr || '1');
const first = shots[0];
if (first.doc != null) q.set('doc', first.doc); else if (first.t) q.set('t', first.t);

const server = await serve();
const url = `http://127.0.0.1:${server.address().port}/index.html?${q}`;
const { chromium } = require('playwright');
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--use-gl=angle', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--disable-gpu-vsync', '--mute-audio'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const consoleErrors = [];
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); else if (m.type() === 'warning' && !o.quiet) consoleErrors.push('[warn] ' + m.text()); });
page.on('pageerror', (e) => consoleErrors.push('[pageerror] ' + (e.stack || e.message)));
page.on('requestfailed', (r) => consoleErrors.push(`[requestfailed] ${r.url()} ${r.failure()?.errorText || ''}`));
page.on('response', (r) => { if (r.status() >= 400 && r.request().method() !== 'HEAD') consoleErrors.push(`[http ${r.status()}] ${r.url()}`); });

let failed = false;
const report = { url, shots: [] };
try {
  await page.goto(url, { waitUntil: 'load', timeout });
  await page.waitForFunction('window.__ph && window.__ph.ready', null, { timeout });
  const boot = await page.evaluate(() => window.__ph.ready);
  report.systems = boot.systems; report.quality = boot.quality; report.synthTerrain = boot.synthTerrain;
  for (const s of shots) {
    const cam = typeof s.cam === 'string' ? s.cam.split(',').map(Number) : s.cam;
    const look = typeof s.look === 'string' ? s.look.split(',') : s.look;
    const info = await page.evaluate(async ({ s, cam, look }) => {
      const ph = window.__ph, app = ph.app;
      if (s.doc != null) app.seekDoc(+s.doc); else if (s.t != null) app.seekSim(s.t);
      app.pause();
      ph.frames(1, 0);
      let evalResult;
      if (s.eval) evalResult = await (0, eval)(`(async (app, ph, THREE) => { ${s.eval} })`)(app, ph, ph.THREE);
      if (cam && cam.length >= 6 && s.doc == null) app.setCamera(cam.slice(0, 3), cam.slice(3, 6), cam[6]);
      if (look && s.doc == null) app.lookAtEntity(look[0], { dist: +look[1] || 800, az: look[2] != null ? +look[2] : 135, el: look[3] != null ? +look[3] : 15, fov: look[4] ? +look[4] : undefined });
      const n = Math.max(1, +(s.frames || 2));
      const r = ph.frames(n, +(s.dt || 0));
      r.evalResult = evalResult;
      return r;
    }, { s, cam, look });
    const out = path.resolve(s.out || 'shot.png');
    fs.mkdirSync(path.dirname(out), { recursive: true });
    await page.screenshot({ path: out, timeout });
    report.shots.push({ out, time: info.time, camera: info.camera, stats: info.stats, ...(info.evalResult !== undefined ? { evalResult: info.evalResult } : {}) });
    report.errors = info.errors;
  }
} catch (e) {
  failed = true;
  report.fatal = String(e && e.stack || e);
  try { report.errors = await page.evaluate(() => window.__ph ? window.__ph.errors.slice() : []); } catch (_) { /* ignore */ }
}
report.console = [...new Set(consoleErrors)].slice(0, 60);
await browser.close();
server.close();
console.log(JSON.stringify(report, null, 1));
if (failed || (report.errors && report.errors.length) || report.console.some((l) => !l.startsWith('[warn]'))) process.exit(1);
