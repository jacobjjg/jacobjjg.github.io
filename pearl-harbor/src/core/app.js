// App: renderer, scene graph, clocks, shared environment state, system registry and main loop.
// See docs/ARCHITECTURE.md for the contract every system follows.
import * as THREE from 'three';
import { installAtmosphere, fogShared } from './atmosphere.js';
import { Emitter, Registry, parseParams, detectQuality } from './util.js';
import { HeightField } from './heightfield.js';
import * as geo from './geo.js';
import { T, SIM_EPOCH } from './timeutil.js';
import { clamp, smoothstep } from './math.js';

const _m4 = new THREE.Matrix4();
const _v3 = new THREE.Vector3();
const _v3b = new THREE.Vector3();
const toV3 = (v, out) => (Array.isArray(v) ? out.set(v[0], v[1], v[2]) : out.copy(v));

export class App {
  /**
   * @param {object} o
   * @param {HTMLCanvasElement} o.canvas
   * @param {HTMLElement} o.hud        overlay root for DOM UI
   * @param {string} o.base            URL of the pearl-harbor/ directory, ending in '/'
   */
  constructor({ canvas, hud, base }) {
    installAtmosphere();
    this.THREE = THREE;
    this.geo = geo;
    this.canvas = canvas;
    this.hud = hud;
    this.base = base;
    this.params = parseParams();
    this.events = new Emitter();
    this.registry = new Registry();
    this.height = new HeightField();
    this.data = {};
    this.plan = null;
    this.systems = [];
    this._systemById = new Map();
    this.errors = [];
    this.stats = { fps: 0, frameMs: 0, calls: 0, triangles: 0, system: {} };

    // ---- renderer ---------------------------------------------------------------------
    const capture = this.params.bool('capture');
    this.renderer = new THREE.WebGLRenderer({
      canvas, antialias: true, alpha: false, stencil: false,
      logarithmicDepthBuffer: true,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: capture,
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.info.autoReset = false;
    this.quality = detectQuality(this.renderer, this.params.str('q'));
    this.renderer.shadowMap.enabled = this.quality.shadows;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // ---- scene graph ------------------------------------------------------------------
    // Everything lives in `world`, positioned in GLOBAL metres.  `world` itself is shifted by
    // -origin (floating origin) so the GPU only ever sees coordinates near the camera.
    this.scene = new THREE.Scene();
    this.world = new THREE.Group();
    this.world.name = 'world';
    this.scene.add(this.world);
    this.origin = new THREE.Vector3();
    this.scene.fog = new THREE.FogExp2(0xa9bccb, 2.5e-5);

    this.camera = new THREE.PerspectiveCamera(35, 16 / 9, 0.3, 3.0e6);
    this.camera.position.set(1500, 400, 2500);
    this.world.add(this.camera);
    // lookAt in GLOBAL coordinates (the stock implementation would mix global and render space).
    this.camera.lookAt = function lookAtGlobal(x, y, z) {
      if (x && x.isVector3) _v3.copy(x); else _v3.set(x, y, z);
      _m4.lookAt(this.position, _v3, this.up);
      this.quaternion.setFromRotationMatrix(_m4);
    };
    this.camera.lookAt(0, 0, 0);

    // ---- clocks -----------------------------------------------------------------------
    this.time = {
      sim: T('07:50'),   // seconds after 00:00 HST 7 Dec 1941
      prevSim: T('07:50'),
      dSim: 0,           // sim seconds elapsed this frame
      scale: 1,          // sim seconds per real second right now (time-lapse > 1, slow motion < 1)
      doc: 0,            // documentary playback position (s)
      visual: 0,         // "ambient motion" clock (s): waves, flags, clouds.  Never races in time-lapse.
      dt: 0,             // real seconds since the previous frame
      frame: 0,
      mode: 'explore',   // 'doc' (director drives sim time + camera) | 'explore' (free time + camera)
      playing: true,
      rate: 1,           // doc-mode playback rate
      simRate: 1,        // explore-mode sim seconds per real second
      jumped: true,      // true on frames where sim time changed discontinuously (seek, cut, reverse)
    };
    this._seekFlag = true;

    // ---- environment (written by the sky system; sane defaults otherwise) ------------------
    this.env = {
      sunDir: new THREE.Vector3(0.5, 0.4, 0.7).normalize(), sunAzimuth: 120, sunElevation: 18,
      moonDir: new THREE.Vector3(-0.5, 0.4, -0.7).normalize(), moonElevation: -30, moonIllumination: 0.85,
      sunColor: new THREE.Color(3.2, 2.9, 2.5),      // DirectionalLight colour x intensity for the sun
      moonColor: new THREE.Color(0, 0, 0),
      ambientSky: new THREE.Color(0.55, 0.7, 0.95),  // HemisphereLight sky colour x intensity
      ambientGround: new THREE.Color(0.25, 0.24, 0.2),
      skyZenith: new THREE.Color(0.18, 0.36, 0.75),  // approximate sky radiance for cheap reflections
      skyHorizon: new THREE.Color(0.62, 0.74, 0.86),
      fogColor: new THREE.Color(0.66, 0.74, 0.82),
      fogSunColor: new THREE.Color(1.0, 0.86, 0.66),
      fogDensity: 2.5e-5,        // extinction per metre at sea level
      fogHeightFalloff: 1 / 1800, // 1/m
      fogSunPower: 6,
      wind: new THREE.Vector3(-4.3, 0, 2.5), // m/s, direction the air moves TOWARD (NE trade wind -> blows to the SW)
      exposure: 1.0,
      dayFactor: 1,              // 0 night .. 1 full day
    };
    this.envProvider = null;     // the sky system sets this to itself; otherwise the built-in fallback lights are used

    // ---- shared uniforms (use the SAME objects in ShaderMaterials via makeUniforms) ---------
    this.uniforms = {
      uTime: { value: 0 },                       // = time.visual
      uSimTime: { value: 0 },                    // = time.sim - SIM_EPOCH
      uSunDir: { value: this.env.sunDir },
      uMoonDir: { value: this.env.moonDir },
      uSunColor: { value: new THREE.Color() },   // env.sunColor / PI
      uMoonColor: { value: new THREE.Color() },
      uAmbientSky: { value: new THREE.Color() }, // env.ambientSky / PI
      uAmbientGround: { value: new THREE.Color() },
      uSkyZenith: { value: this.env.skyZenith },
      uSkyHorizon: { value: this.env.skyHorizon },
      uWind: { value: this.env.wind },
      uOrigin: { value: this.origin },           // global position of render-space (0,0,0)
      uResolution: { value: new THREE.Vector2(1, 1) },
      uDayFactor: { value: 1 },
    };

    // The view that gets rendered.  Normally the 3D world; the map system swaps in its own scene + camera
    // for strategic-map shots via setView() and restores it with resetView().  The post system renders app.view.
    this.view = { scene: this.scene, camera: this.camera };

    this._fallback = null;
    this._raf = 0;
    this._lastNow = 0;
    this.renderFn = null; // a post-processing system may replace the final render: (app) => void
    this.ready = false;
    this._resize = this._resize.bind(this);
    this._tick = this._tick.bind(this);
    window.addEventListener('resize', this._resize);
    window.addEventListener('error', (e) => this._err('window', e.error || e.message));
    window.addEventListener('unhandledrejection', (e) => this._err('promise', e.reason));
  }

  // ---- helpers ------------------------------------------------------------------------
  asset(rel) { return this.base + rel; }
  async loadJSON(rel) {
    if (this.data[rel]) return this.data[rel];
    const res = await fetch(this.asset(rel));
    if (!res.ok) throw new Error(`${rel}: HTTP ${res.status}`);
    return (this.data[rel] = await res.json());
  }
  _err(where, e) {
    const msg = e && e.stack ? e.stack : String(e);
    if (this.errors.length < 200) this.errors.push(`[${where}] ${msg}`);
    console.error(`[${where}]`, e);
  }

  /** Uniforms for a custom ShaderMaterial: fog uniforms + all shared uniforms (by reference) + your own. */
  makeUniforms(extra = {}) {
    return { ...THREE.UniformsUtils.clone(THREE.UniformsLib.fog), ...this.uniforms, ...extra };
  }

  getSystem(id) { return this._systemById.get(id) || null; }

  /** Render a different scene/camera (e.g. the strategic map) through the normal pipeline until resetView(). */
  setView(scene, camera) { this.view.scene = scene; this.view.camera = camera; }
  resetView() { this.view.scene = this.scene; this.view.camera = this.camera; }
  /** true while the 3D world is what is being shown (systems may skip heavy work when false). */
  get worldVisible() { return this.view.scene === this.scene; }

  /** Register a system: { id, order?, init?(app), update?(app), resize?(app,w,h), dispose?(app) }. */
  use(system) {
    if (!system || !system.id) throw new Error('system needs an id');
    if (system.order == null) system.order = 50;
    this.systems.push(system);
    this._systemById.set(system.id, system);
    return this;
  }

  // ---- camera --------------------------------------------------------------------------
  /** Place the camera (global coords) looking at a target (global coords). */
  setCamera(pos, target, fov) {
    toV3(pos, this.camera.position);
    this.camera.up.set(0, 1, 0);
    this.camera.lookAt(toV3(target, _v3b));
    if (fov) { this.camera.fov = fov; this.camera.updateProjectionMatrix(); }
  }
  /** Orbit view of an entity (or world point): camera `dist` metres away toward compass bearing `az`, `el` degrees above the horizon. */
  lookAtEntity(idOrPoint, { dist = 800, az = 135, el = 15, fov, yOffset = 0 } = {}) {
    const target = new THREE.Vector3();
    if (typeof idOrPoint === 'string') {
      const e = this.registry.get(idOrPoint);
      if (!e) { console.warn(`lookAtEntity: unknown entity ${idOrPoint}`); return false; }
      e.getPosition(this.time.sim, target);
    } else toV3(idOrPoint, target);
    target.y += yOffset;
    const a = az * geo.DEG, e = el * geo.DEG;
    const pos = new THREE.Vector3(target.x + Math.sin(a) * Math.cos(e) * dist, target.y + Math.sin(e) * dist, target.z - Math.cos(a) * Math.cos(e) * dist);
    this.setCamera(pos, target, fov);
    return true;
  }
  /** Project a GLOBAL point to CSS pixels: { x, y, depth (m along view), visible }. */
  project(p, out = {}) {
    _v3.copy(p).sub(this.origin).applyMatrix4(this.camera.matrixWorldInverse);
    const depth = -_v3.z;
    _v3.applyMatrix4(this.camera.projectionMatrix);
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    out.x = (_v3.x * 0.5 + 0.5) * w;
    out.y = (-_v3.y * 0.5 + 0.5) * h;
    out.depth = depth;
    out.visible = depth > 0 && Math.abs(_v3.x) <= 1.05 && Math.abs(_v3.y) <= 1.05;
    return out;
  }

  // ---- clocks --------------------------------------------------------------------------
  setMode(mode) { if (this.time.mode !== mode) { this.time.mode = mode; this._seekFlag = true; this.events.emit('mode', mode); } }
  play() { this.time.playing = true; this.events.emit('play'); }
  pause() { this.time.playing = false; this.events.emit('pause'); }
  /** Jump to a sim time (number or 'HH:MM[:SS]').  Switches to explore mode. */
  seekSim(t) {
    this.setMode('explore');
    this.time.sim = T(t);
    this.time.visual = (((this.time.sim % 3600) + 3600) % 3600);
    this._seekFlag = true;
    this.events.emit('seek', { sim: this.time.sim });
  }
  /** Jump to a documentary time (seconds).  Switches to doc mode; the director maps it to sim time + camera. */
  seekDoc(sec) {
    this.setMode('doc');
    this.time.doc = Math.max(0, sec);
    this._seekFlag = true;
    this.events.emit('seek', { doc: this.time.doc });
  }

  // ---- lifecycle -----------------------------------------------------------------------
  async init() {
    this._resize();
    this.events.emit('progress', { label: 'terrain data', done: 0, total: this.systems.length + 1 });
    await this.height.load(this.asset('assets/geo/'), { lowMemory: this.quality.tier === 'low' });
    let i = 0;
    for (const sys of this.systems) {
      this.events.emit('progress', { label: sys.id, done: ++i, total: this.systems.length + 1 });
      const t0 = performance.now();
      try { if (sys.init) await sys.init(this); } catch (e) { sys.failed = true; this._err(`init ${sys.id}`, e); }
      sys.initMs = performance.now() - t0;
    }
    this._ordered = this.systems.slice().sort((a, b) => a.order - b.order);
    if (!this.envProvider) this._installFallbackEnv();
    this._resize();
    this.ready = true;
    this.events.emit('ready');
  }

  start() {
    if (this._raf) return;
    this._lastNow = performance.now();
    this._raf = requestAnimationFrame(this._tick);
  }
  stop() { cancelAnimationFrame(this._raf); this._raf = 0; }
  _tick(now) {
    this._raf = requestAnimationFrame(this._tick);
    const dt = clamp((now - this._lastNow) / 1000, 0, 0.1);
    this._lastNow = now;
    this.frame(dt);
  }

  /** Advance by dt real seconds and render one frame.  Safe to call manually (capture / tests). */
  frame(dt = 1 / 60) {
    const t0 = performance.now();
    const time = this.time;
    time.dt = dt;
    time.frame++;
    if (time.playing) {
      if (time.mode === 'doc') time.doc += dt * time.rate;
      else {
        time.sim += dt * time.simRate;
        time.visual += dt * clamp(Math.abs(time.simRate), 0, 2);
        time.scale = time.simRate;
      }
    } else if (time.mode === 'explore') time.scale = 0;

    const ordered = this._ordered || this.systems;
    // phase 1: time + camera owners (director, controls): order < 10
    let k = 0;
    for (; k < ordered.length && ordered[k].order < 10; k++) this._update(ordered[k]);

    // bookkeeping between the phases
    time.dSim = time.sim - time.prevSim;
    time.jumped = this._seekFlag || time.dSim < 0 || Math.abs(time.dSim) > Math.max(2, Math.abs(time.scale) * dt * 4 + 1);
    this._seekFlag = false;
    time.prevSim = time.sim;
    this._updateOrigin();
    this._updateAstronomy();
    if (!this.envProvider) this._fallbackEnv();

    // phase 2: everything else
    for (; k < ordered.length; k++) this._update(ordered[k]);

    this._syncUniforms();
    this.camera.updateMatrixWorld();
    this.renderer.info.reset();
    if (this.renderFn) this.renderFn(this); else this.renderer.render(this.view.scene, this.view.camera);

    const s = this.stats;
    s.frameMs = performance.now() - t0;
    s.fps = s.fps ? s.fps * 0.95 + (1 / Math.max(dt, 1e-3)) * 0.05 : 1 / Math.max(dt, 1e-3);
    s.calls = this.renderer.info.render.calls;
    s.triangles = this.renderer.info.render.triangles;
  }

  _update(sys) {
    if (sys.failed || !sys.update) return;
    const t0 = performance.now();
    try { sys.update(this); } catch (e) {
      sys._errors = (sys._errors || 0) + 1;
      if (sys._errors <= 3) this._err(`update ${sys.id}`, e);
      if (sys._errors > 120) { sys.failed = true; this._err(`update ${sys.id}`, 'disabled after repeated errors'); }
    }
    this.stats.system[sys.id] = performance.now() - t0;
  }

  _updateOrigin() {
    const p = this.camera.position;
    if (Math.hypot(p.x, p.z) < 90000) this.origin.set(0, 0, 0);
    else this.origin.set(Math.round(p.x / 4000) * 4000, 0, Math.round(p.z / 4000) * 4000);
    this.world.position.copy(this.origin).negate();
  }

  _updateAstronomy() {
    const env = this.env, cam = this.camera.position;
    const ll = geo.toLatLon(cam.x, cam.z);
    const s = geo.sunPosition(this.time.sim, ll.lat, ll.lon);
    env.sunAzimuth = s.azimuth; env.sunElevation = s.elevation;
    geo.azElToVec(s.azimuth, s.elevation, env.sunDir);
    const m = geo.moonPosition(this.time.sim, ll.lat, ll.lon);
    env.moonAzimuth = m.azimuth; env.moonElevation = m.elevation; env.moonIllumination = m.illumination;
    geo.azElToVec(m.azimuth, m.elevation, env.moonDir);
    env.dayFactor = smoothstep(-6, 4, s.elevation);
  }

  _syncUniforms() {
    const env = this.env, u = this.uniforms, time = this.time;
    u.uTime.value = time.visual;
    u.uSimTime.value = time.sim - SIM_EPOCH;
    u.uSunColor.value.copy(env.sunColor).multiplyScalar(1 / Math.PI);
    u.uMoonColor.value.copy(env.moonColor).multiplyScalar(1 / Math.PI);
    u.uAmbientSky.value.copy(env.ambientSky).multiplyScalar(1 / Math.PI);
    u.uAmbientGround.value.copy(env.ambientGround).multiplyScalar(1 / Math.PI);
    u.uDayFactor.value = env.dayFactor;
    const fog = this.scene.fog;
    if (fog) { fog.color.copy(env.fogColor); if (fog.isFogExp2) fog.density = env.fogDensity; }
    // the fog glow follows the sun by day and the moon at night
    const glowDir = env.sunElevation > -8 ? env.sunDir : env.moonDir;
    fogShared.sunDir[0] = glowDir.x; fogShared.sunDir[1] = glowDir.y; fogShared.sunDir[2] = glowDir.z;
    fogShared.sunColor[0] = env.fogSunColor.r; fogShared.sunColor[1] = env.fogSunColor.g; fogShared.sunColor[2] = env.fogSunColor.b;
    fogShared.params[0] = env.fogHeightFalloff; fogShared.params[1] = 0; fogShared.params[2] = env.fogSunPower; fogShared.params[3] = 1;
    this.renderer.toneMappingExposure = env.exposure;
  }

  // Minimal lighting + background used only when no sky system is loaded (dev sandboxes).
  _installFallbackEnv() {
    const sun = new THREE.DirectionalLight(0xffffff, 1);
    const hemi = new THREE.HemisphereLight(0xffffff, 0xffffff, 1);
    this.world.add(sun, sun.target, hemi);
    this._fallback = { sun, hemi };
    this.scene.background = new THREE.Color(0x8fb0d0);
  }
  _fallbackEnv() {
    const env = this.env, f = this._fallback;
    if (!f) return;
    const e = env.sunElevation;
    const day = smoothstep(-4, 8, e), warm = 1 - smoothstep(2, 30, e);
    env.sunColor.setRGB(3.4, 3.4 - 1.1 * warm, 3.3 - 2.2 * warm).multiplyScalar(smoothstep(-1, 6, e));
    env.ambientSky.setRGB(0.5, 0.66, 0.95).multiplyScalar(0.08 + 1.0 * day);
    env.ambientGround.setRGB(0.28, 0.26, 0.22).multiplyScalar(0.05 + 0.9 * day);
    env.skyZenith.setRGB(0.16, 0.34, 0.75).multiplyScalar(0.03 + day);
    env.skyHorizon.setRGB(0.6 + 0.3 * warm, 0.72, 0.86 - 0.2 * warm).multiplyScalar(0.04 + day);
    env.fogColor.copy(env.skyHorizon).multiplyScalar(0.9);
    env.fogSunColor.setRGB(1.0, 0.82, 0.6).multiplyScalar(0.05 + day);
    const c = this.camera.position;
    f.sun.color.copy(env.sunColor); f.sun.intensity = 1;
    f.sun.target.position.set(c.x, 0, c.z);
    f.sun.position.copy(f.sun.target.position).addScaledVector(env.sunDir, 1000);
    f.hemi.color.copy(env.ambientSky); f.hemi.groundColor.copy(env.ambientGround); f.hemi.intensity = 1;
    this.scene.background.copy(env.skyHorizon).lerp(env.skyZenith, 0.5);
  }

  _resize() {
    const w = Math.max(1, this.canvas.clientWidth || window.innerWidth), h = Math.max(1, this.canvas.clientHeight || window.innerHeight);
    let pr = Math.min(window.devicePixelRatio || 1, this.quality.pixelRatio);
    const forced = this.params.num('pr');
    if (forced) pr = forced;
    else if (w * h * pr * pr > this.quality.maxPixels) pr = Math.sqrt(this.quality.maxPixels / (w * h));
    this.pixelRatio = pr;
    this.renderer.setPixelRatio(pr);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.getDrawingBufferSize(this.uniforms.uResolution.value);
    for (const sys of this.systems) { try { if (!sys.failed && sys.resize) sys.resize(this, w, h, pr); } catch (e) { this._err(`resize ${sys.id}`, e); } }
  }
}
