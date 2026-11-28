// Boot: create the App, load whichever systems exist, wire URL parameters and the dev API.
//
// URL parameters (all optional):
//   dev=1            developer mode: no title screen, explore mode, paused
//   sys=a,b,c        load only these systems          nosys=a,b   skip these
//   q=low|medium|high|ultra   force a quality tier    pr=1.0      force pixel ratio
//   t=07:55:30       start at this sim time (explore mode)        doc=123.4   start at this documentary time
//   cam=x,y,z,tx,ty,tz[,fov]  camera position + target (world metres)
//   look=id[,dist,az,el[,fov]]  orbit view of an entity
//   scene=dev/scenes/foo.js   run a dev fixture module after init: export default async (app) => {}
//   play=1           keep the clock running in dev mode          rate=60   explore-mode sim seconds per second
//   manual=1         no animation loop; frames are driven through window.__ph.frames() (screenshot tool)
import * as THREE from 'three';
import { App } from './core/app.js';
import { SYSTEMS } from './systems/index.js';

const base = new URL('../', import.meta.url).href;
const canvas = document.getElementById('view');
const hud = document.getElementById('hud');
const loader = document.getElementById('loader');
const loaderText = document.getElementById('loader-text');
const loaderBar = document.getElementById('loader-bar');

const app = new App({ canvas, hud, base });
const P = app.params;
const dev = P.bool('dev') || P.has('sys') || P.has('t') || P.has('cam') || P.has('look') || P.has('scene') || P.has('manual');
app.dev = dev;

let readyResolve;
const ph = (window.__ph = {
  app, THREE,
  ready: new Promise((r) => (readyResolve = r)),
  errors: app.errors,
  seekSim: (t) => app.seekSim(t),
  seekDoc: (s) => app.seekDoc(s),
  cam: (pos, target, fov) => app.setCamera(pos, target, fov),
  look: (id, opts) => app.lookAtEntity(id, opts),
  /** render n frames, advancing dt real seconds each (0 = frozen time). */
  frames: (n = 1, dt = 0) => { for (let i = 0; i < n; i++) app.frame(dt); return ph.info(); },
  info: () => ({
    time: { sim: app.time.sim, doc: app.time.doc, mode: app.time.mode, scale: app.time.scale },
    camera: { pos: app.camera.position.toArray().map((v) => +v.toFixed(1)), fov: app.camera.fov },
    stats: { frameMs: +app.stats.frameMs.toFixed(1), calls: app.stats.calls, triangles: app.stats.triangles, system: app.stats.system },
    systems: app.systems.map((s) => ({ id: s.id, failed: !!s.failed, initMs: Math.round(s.initMs || 0) })),
    quality: app.quality.tier, pixelRatio: app.pixelRatio, synthTerrain: app.height.synthetic,
    errors: app.errors.slice(),
  }),
});

app.events.on('progress', ({ label, done, total }) => {
  if (loaderText) loaderText.textContent = `Loading ${label}…`;
  if (loaderBar) loaderBar.style.width = `${Math.round((done / total) * 100)}%`;
});

async function exists(url) {
  try { const r = await fetch(url, { method: 'HEAD', cache: 'no-cache' }); return r.ok; } catch (e) { return false; }
}

async function boot() {
  const only = P.list('sys'), skip = P.list('nosys') || [];
  for (const s of SYSTEMS) {
    if (only && !only.includes(s.id)) continue;
    if (skip.includes(s.id)) continue;
    const url = new URL(s.path, new URL('./systems/', import.meta.url)).href;
    if (!(await exists(url))) { if (dev) console.info(`[boot] system "${s.id}" not present - skipped`); continue; }
    try {
      const mod = await import(url);
      const sys = mod.default;
      if (!sys || !sys.id) throw new Error(`${s.path} must default-export a system object with an id`);
      if (sys.order == null) sys.order = s.order;
      app.use(sys);
    } catch (e) { app._err(`load ${s.id}`, e); }
  }
  await app.init();

  // ---- URL-driven state ---------------------------------------------------------------
  if (P.has('rate')) app.time.simRate = P.num('rate', 1);
  if (P.has('doc')) app.seekDoc(P.num('doc', 0));
  else if (P.has('t')) app.seekSim(P.str('t'));
  else if (dev) app.seekSim('07:55');
  if (dev && !P.bool('play')) app.pause();

  const sceneMod = P.str('scene');
  if (sceneMod) {
    try { const m = await import(new URL(sceneMod, base).href); await m.default(app); } catch (e) { app._err('scene', e); }
  }
  const cam = P.nums('cam');
  if (cam && cam.length >= 6) app.setCamera(cam.slice(0, 3), cam.slice(3, 6), cam[6]);
  const look = P.list('look');
  if (look) {
    app.frame(0); // let entities settle so positions are valid
    app.lookAtEntity(look[0], { dist: +look[1] || 800, az: look[2] != null ? +look[2] : 135, el: look[3] != null ? +look[3] : 15, fov: look[4] ? +look[4] : undefined });
  }

  if (loader) { if (dev) loader.style.display = 'none'; loader.classList.add('done'); }
  if (!dev) app.events.emit('boot-complete');   // the HUD shows the title card and starts the documentary on "begin"
  if (!P.bool('manual')) app.start(); else app.frame(0);
  readyResolve(ph.info());
}

boot().catch((e) => { app._err('boot', e); if (loaderText) loaderText.textContent = 'Failed to start - see console.'; readyResolve(ph.info()); });
