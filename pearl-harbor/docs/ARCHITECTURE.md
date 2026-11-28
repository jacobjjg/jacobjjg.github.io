# Pearl Harbor — 7 December 1941 · Architecture & system contract

A real-time 3D documentary reconstruction in three.js (r187, WebGL2), served as static files
(GitHub Pages, no build step, no network dependencies at runtime). This file is the contract every
system follows. Read it fully before writing code. If the contract blocks you, say so in your
report instead of working around it silently.

Quality bar: a film-grade historical reconstruction. Real geography (USGS elevation, satellite
imagery, 1950s topographic maps), time-accurate sun and moon, every ship and aircraft where the
record puts it, physically plausible motion, cinematic light. No placeholder art, no cartoon colours,
no visible "game" artefacts (popping, z-fighting, tiling, hard particle quads, floating objects).

## 1. Layout

```
pearl-harbor/
  index.html, css/app.css (shell + loader), css/hud.css (owned by the hud system)
  vendor/three/build/three.module.js   import as 'three'
  vendor/three/addons/...              import as 'three/addons/...'  (postprocessing, shaders, controls, utils, math, csm, objects, lines, geometries, misc, environments, libs)
  assets/geo/        baked terrain / imagery rasters (see assets/geo/README.md + manifest.json when present)
  assets/audio/      optional recorded audio
  research/          historical dossiers (*.md) and their data (*.json) - the factual basis
  data/              runtime datasets (JSON) derived from research/, owned by the system that consumes them
  docs/              this file, SOURCES.md
  dev/scenes/        dev fixtures: `export default async (app) => {}` loaded with ?scene=dev/scenes/x.js
  tools/shot.mjs     headless screenshot / smoke test tool         tools/geo/  raster pipeline (python)
  src/main.js        boot                 src/systems/index.js   the system manifest (ids, paths, order)
  src/core/          app.js geo.js timeutil.js math.js noise.js atmosphere.js heightfield.js util.js   (do not edit; report needed changes)
  src/systems/<name>/   one directory per system; each has index.js (default-exports the system) and a README.md documenting its public API
```

Rules: plain ES modules, browser-native, no bundler, no npm dependencies, no CDN/network fetches
other than files inside `pearl-harbor/`. No `Math.random()`, `Date.now()` or `performance.now()` in
anything that affects what is drawn (use `rng(seed)`, `hash3`, sim time). Edit only your own system
directory, `data/` files you own, and `dev/scenes/<yours>*.js`. Never run git commands.

## 2. Coordinates, units, model frame  (`src/core/geo.js`)

- World frame: origin Ford Island 21.3650 N, 157.9600 W, sea level. **+X east, +Y up, +Z south** (north is −Z). Metres.
  `toWorld(lat, lon, alt)`, `toLatLon(x, z)`, `headingToVec(deg)`, `vecToHeading(x, z)`, `offsetByBearing`, `attitudeQuat(heading, pitch, roll)`.
- Headings / bearings: degrees true, clockwise from north (0 → −Z, 90 → +X).
- Constants: `NMI` 1852, `MILE` 1609.344, `FT` 0.3048, `KT` 0.514444 (m/s per knot), `DEG`.
- **Model frame** for every ship, aircraft, vehicle, person: nose/bow toward local **−Z**, right/starboard **+X**, up **+Y**,
  1 unit = 1 m, true scale. Ship origin: on the centreline amidships at the design waterline. Aircraft origin: centre of gravity.
  `object.rotation.y = -headingDeg * DEG` points a model along a heading; `quatFromForward(dir, bank)` (math.js) for flight attitude.
- Terrain rasters cover `RECT_ISLAND` (x −40960..40960, z −45568..19968) and `RECT_HARBOR` (x −8192..8192, z −5120..11264).
  `app.height.at(x, z)` (metres, negative under water), `app.height.isWater(x, z)`, `.depth`, `.normal`, `.raster(name)`, `.texture(name)`.
- Sea level is y = 0. Sea surface waves are small in the harbor; ships float at y = 0.

### Floating origin
The carrier force launches ~400 km north of Oahu. Everything is positioned in **global** world metres, as
children of `app.world` (never `app.scene`). `app.world` is shifted by `-app.origin` each frame (origin is
(0,0,0) whenever the camera is within 90 km of Ford Island, otherwise the camera position snapped to 4 km), so:
- `Object3D.position` values are global; three.js builds model-view matrices in double precision — fine.
- In shaders, `modelMatrix * position` and `cameraPosition` are **render space** (global − origin). Add the shared
  uniform `uOrigin` (vec3) when you need global coordinates (e.g. ocean wave phase, terrain UVs). Near Oahu uOrigin is 0.
- Keep vertex data and instance matrices near their object's origin: an `InstancedMesh` whose instances are spread
  far from (0,0,0) must set `mesh.position` to a nearby anchor (e.g. the fleet centre or the camera position snapped
  to 1 km) and write instance matrices relative to it.
- `app.camera` is a child of `app.world`; `camera.position` is global. `camera.lookAt(globalTarget)` is overridden to
  work in global coordinates. Use `app.setCamera(pos, target, fov)`, `app.lookAtEntity(id, {dist, az, el, fov})`,
  `app.project(globalPoint)` → CSS pixels. Only the director / controls systems move the camera.

## 3. Time  (`src/core/timeutil.js`)

- **Sim time** `t`: seconds after 1941-12-07 00:00 Hawaii time (HST = UTC−10:30 in 1941). `T('07:55')` = 28500,
  `T('1941-11-26 06:00')` is negative. `fmtClock`, `fmtDate`, `tokyo(t)` (Tokyo = Hawaii + 19 h 30 min).
- `app.time`: `sim`, `dSim` (sim seconds this frame), `scale` (sim s per real s: >1 time-lapse, <1 slow motion, 0 paused),
  `doc` (documentary playback seconds), `visual` (ambient-motion clock), `dt` (real s), `mode` ('doc' | 'explore'),
  `playing`, `jumped` (true when sim time moved discontinuously: seek, cut, reverse).
- **THE STATELESS RULE.** The documentary cuts and scrubs freely. What a system draws must be a pure function of
  `app.time.sim` (plus camera and quality), not of the history of frames. No accumulating simulation state.
  A plume that has burned for 20 minutes must look 20 minutes old on the first frame after a seek. Design everything
  as `state = f(t)`: keyframe `Track`s, `TimedPath`s, hashed per-instance randomness, shader particles whose age is
  derived from time. Where a little history is unavoidable (trails, temporal smoothing) rebuild it when `time.jumped`.
- Use `uniforms.uSimTime` (= sim − `SIM_EPOCH`, epoch 08:00, keeps float32 precise) for event-driven shader animation and
  `uniforms.uTime` (= `time.visual`) for ambient motion (waves, flags, cloud drift) so time-lapse shots do not look frantic.

## 4. The App object  (`src/core/app.js`)

`THREE`, `geo`, `renderer`, `scene`, `world` (add your objects here), `camera`, `canvas`, `hud` (DOM overlay root),
`params` (URL), `quality`, `events` (Emitter: `on/off/emit`), `registry`, `height`, `time`, `env`, `uniforms`,
`origin`, `plan` (battle plan, set by the battle system), `stats`, `dev` (bool).
Helpers: `asset(rel)`, `loadJSON(rel)`, `makeUniforms(extra)`, `getSystem(id)`, `setCamera`, `lookAtEntity`, `project`,
`seekSim(t)`, `seekDoc(sec)`, `play()`, `pause()`, `setMode(mode)`.
Events emitted by core: `progress`, `ready`, `boot-complete`, `mode`, `play`, `pause`, `seek`. Systems may emit their own (document them).

### System interface
```js
export default {
  id: 'ocean',                 // must match src/systems/index.js
  async init(app) {},          // build everything; add to app.world; may await asset loads
  update(app) {},              // every frame; read app.time / app.env / app.camera; obey the stateless rule
  resize(app, w, h, pixelRatio) {},   // optional
  dispose(app) {},             // optional
};
```
Init order = manifest order. Update order = `order` (director 0, controls 5, battle 10, ships 12, sky 20, clouds 22, terrain 30,
ocean 32, installations 34, aircraft 40, people 44, radar 46, weapons 48, fx 50, map 60, audio 70, hud 80, post 90). Systems with
order < 10 own time and camera; core then updates `time.dSim/jumped`, the floating origin and the sun/moon ephemeris before the rest run.
A system must tolerate other systems being absent (`app.getSystem('x')` may be null, `app.plan` may be null) — dev sandboxes load subsets.

### Quality tiers  (`app.quality`)
`tier` low | medium | high | ultra with `pixelRatio`, `maxPixels`, `msaa`, `shadows`, `shadowMap`, `particles`, `crowd`, `foliage`,
`oceanDetail`, `terrainDetail`, `cloudDetail`, `bloom`, `anisotropy`, `envMapSize`. Multiply your nominal counts by the matching
field. Headless tests run on `low` (software GL). Design for 60 fps at 1080p on a mid-range discrete GPU at `high`.
Whole-frame budget at `high`: ≤ 450 draw calls, ≤ 3 M triangles, ≤ 80 k particles on screen. Use `InstancedMesh`, merged geometry
(`BufferGeometryUtils.mergeGeometries`), shared materials, LODs and frustum/distance culling. Per-system budgets are in the task briefs.

## 5. Light, atmosphere, colour

- Core computes the real sun and moon for the sim time and camera location every frame: `env.sunDir`, `env.sunAzimuth`,
  `env.sunElevation` (deg), `env.moonDir`, `env.moonElevation`, `env.moonIllumination`, `env.dayFactor` (0 night..1 day).
  (07:55 → sun 17° above the horizon at azimuth 124°; sunrise 06:26 at azimuth 114°; the moon is a waning gibbous in the west.)
- The **sky** system owns the lights and writes the rest of `app.env` every frame: `sunColor` / `moonColor` (DirectionalLight
  colour × intensity), `ambientSky` / `ambientGround` (HemisphereLight colours × intensity), `skyZenith`, `skyHorizon`,
  `fogColor`, `fogSunColor`, `fogDensity` (extinction per metre at sea level), `fogHeightFalloff`, `fogSunPower`, `wind`
  (Vector3 m/s, the direction the air moves toward), `exposure`. It also sets `scene.environment` (PMREM of the sky) and shadows.
  Without the sky system core supplies fallback lights so models can be tested alone.
- Built-in materials (MeshStandardMaterial / MeshPhysicalMaterial preferred) just work: lights, shadows, environment reflections,
  log depth, global fog. Prefer them, customised through `onBeforeCompile` when needed.
- **Custom `ShaderMaterial`s** (not RawShaderMaterial) must use the helpers in `src/core/atmosphere.js`:
  ```js
  import { VERT_PARS, VERT_END, FRAG_PARS, FRAG_BEGIN, FRAG_END, FRAG_END_NOFOG, GLSL_LIGHTING } from '../../core/atmosphere.js';
  new THREE.ShaderMaterial({ fog: true, uniforms: app.makeUniforms({ uMine: { value: 1 } }),
    vertexShader: `${VERT_PARS} void main(){ vec4 mvPosition = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mvPosition; ${VERT_END} }`,
    fragmentShader: `${FRAG_PARS} ${GLSL_LIGHTING} void main(){ ${FRAG_BEGIN} vec3 col = albedo * phIrradiance(n); gl_FragColor = vec4(col, 1.0); ${FRAG_END} }` });
  ```
  The renderer uses a **logarithmic depth buffer** (camera near 0.3 m, far 3000 km) — the chunks above handle it; a custom shader
  without them will z-fight or vanish. The global fog is an analytic height fog with sun in-scatter (`phFog()`); `fog: true` plus the
  chunks applies it. Emissive / additive effects use `fog: false` and `FRAG_END_NOFOG`.
  `GLSL_LIGHTING` gives `phIrradiance(n)`, `phIrradianceWrap(n, w)`, `phAmbient(n)` with uniforms `uSunDir`, `uSunColor`, `uMoonDir`,
  `uMoonColor`, `uAmbientSky`, `uAmbientGround` (all premultiplied by 1/π: `diffuse = albedo * phIrradiance(n)` matches built-in materials).
  Other shared uniforms from `app.makeUniforms()`: `uTime`, `uSimTime`, `uSkyZenith`, `uSkyHorizon`, `uWind`, `uOrigin`, `uResolution`, `uDayFactor`.
  `src/core/noise.js` exports `GLSL_NOISE` (hash, value noise, fbm, simplex, worley) and JS `vnoise2/3`, `fbm2/3`, `wobble`.
- Colour pipeline: linear HDR scene → post system (half-float target, bloom, grade) → ACES filmic → sRGB. Author albedo colours as
  sRGB hex via `THREE.Color` (converted to linear automatically); keep albedo physically plausible (no pure white/black; painted steel
  0.2–0.4, foliage 0.05–0.15, concrete 0.4–0.5, sea foam 0.8). Emissive fire/flash values may exceed 1 (bloom picks them up).
- Shadows: one sun shadow map fitted around the camera's focus by the sky system. Set `castShadow` on ships, aircraft, buildings;
  `receiveShadow` on terrain, decks, ground structures. Particles neither cast nor receive.

## 6. Entities  (`app.registry`, see `src/core/util.js`)

Anything the director, labels, audio or UI may refer to is registered as an entity:
```js
{ id, kind: 'ship'|'aircraft'|'place'|'person'|'group', side: 'us'|'jp'|'civ'|null, name,
  getPosition(t, out) -> Vector3 (global), getQuaternion?(t, out), getVelocity?(t, out), isActive?(t), radius, info: {...} }
```
All getters are pure functions of sim time. `registry.add(e)`, `get(id)`, `list(kind)`, `addPlace(id, name, lat, lon, alt)`.
Ids are lowercase snake_case and stable (`arizona`, `west_virginia`, `akagi`, `opana_radar`, `hickam_field`, `w1_akagi_torp_03`).

### Ship entities (registered by the ships system)
Extra fields: `class`, `type` ('BB','CA','CL','DD','CV',...), `hull`, `length`, `beam`, `model` (Object3D),
`state(t)` → `{ heading, speed, list (deg, + = starboard down), trim (deg, + = bow down), sink (m settled below normal draught), capsized (0..1), afloat, underway }`,
`localToWorld(t, [x, y, z], out)` (model-space point → global, honouring list/trim/sink), and `anchors`:
`{ bow, stern, bridge, funnels: [[x,y,z]..], turrets: [..], aa: [{ pos:[x,y,z], caliber }..], decks: [{ y, xMin, xMax, zMin, zMax }..], boats: [..] }` in model space.

## 7. The battle plan  (`app.plan`, built once by the battle system; deterministic)

The single source of truth for who is where and what explodes when. Renderers never invent events.
```js
plan = {
  flights: Flight[], flightById: Map,
  parked: Parked[],           // aircraft on the ground / moored: { id, type, base, pos:[x,y,z], heading, fate: { t, kind:'burned'|'destroyed'|'damaged' } | null }
  ordnance: Ordnance[], impacts: Impact[] /* sorted by t */, fires: Fire[], strafes: Strafe[], aa: AASite[],
  impactsBetween(t0, t1) -> Impact[],  firesActive(t) -> Fire[],
}
Flight   = { id, kind:'aircraft', side, type:'a6m'|'b5n'|'d3a'|'e13a'|'p40'|'p36'|'b17'|'sbd'|'pby'|'f4f'|..., name, unit, group, wave, role, leader, tail,
             t0, t1, getPosition(t,out), getQuaternion(t,out), getVelocity(t,out), isActive(t),
             state(t) -> { phase:'deck'|'takeoff'|'cruise'|'attack'|'egress'|'landing'|'crashing'|'gone', load:'torpedo'|'bomb800'|'bomb250'|'bomb60'|null, gear:0..1, smoke:0..1, fire:0..1, firing:bool },
             fate: { t, kind:'recovered'|'shot_down'|'crashed'|'landed'|'ditched', pos:[x,y,z] } }
Ordnance = { id, kind:'torpedo'|'bomb800'|'bomb250'|'bomb60'|'depth_charge'|'shell', by, t0 /*release*/, tw /*water entry, torpedoes*/, t1 /*impact*/,
             p0:[x,y,z], v0:[x,y,z], p1:[x,y,z], targetId, result:'hit'|'near_miss'|'miss'|'dud', getPosition(t,out), getQuaternion(t,out) }
Impact   = { id, t, kind:'torpedo_hit'|'bomb_hit'|'bomb_water'|'bomb_ground'|'magazine_explosion'|'aircraft_crash'|'depth_charge'|'shell_splash',
             pos:[x,y,z], targetId, surface:'ship'|'water'|'ground'|'building', size /* 1 = 250 kg bomb; 800 kg ≈ 2; torpedo ≈ 2.5; magazine ≈ 40 */, ordnanceId, note }
Fire     = { id, t0, t1, attach: entityId|null, local:[x,y,z] /* model space if attached */, pos:[x,y,z] /* global if not */, kind:'ship'|'oil'|'aircraft'|'building'|'fuel',
             radius /* m */, intensity: [[t, 0..1], ...] /* keyframes */, smoke: 0..1 /* blackness */, plume /* typical rise height m */ }
Strafe   = { id, by, t0, t1, p0:[x,y,z], p1:[x,y,z], targetId }       // line swept on the ground / water by gunfire
AASite   = { id, attach: entityId|null, local|pos, caliber:'5in'|'3in'|'1.1in'|'.50'|'.30'|'rifle', activity: [[t, 0..1], ...], rate /* rounds per s at activity 1 */ }
```
Consumers: aircraft (draws flights + parked), weapons (ordnance in flight, torpedo runs, tracers, flak, splashes, wakes),
fx (explosions for impacts, fires and smoke), ships (hit shudder), people, audio, hud/minimap, director.

## 8. Director ↔ HUD ↔ audio

The director owns documentary playback: a list of shots, each mapping documentary time to sim time and a camera rig, with
captions, narration lines, labels and chapter markers. It exposes `app.getSystem('director')` with:
`duration`, `chapters: [{ id, title, start }]`, `state` (updated every frame in doc mode):
`{ shot, chapter, t (doc s), caption, narration: { id, text, start, end } | null, labels: [entityIds], title: { kicker, text, sub } | null,
   letterbox: 0..1, fade: 0..1 (black), mapInset: bool, clockVisible: bool, look: 'colour' | 'newsreel' }`.
The HUD renders that state (and its own explore-mode UI); audio speaks/plays narration and sound; post applies fade/letterbox/look.
In explore mode the director is idle and the controls system owns the camera.

## 9. Testing your work

```
cd pearl-harbor
node tools/shot.mjs --out /path/shot.png --sys sky,ocean,ships --t 08:10 --look arizona,900,160,12
node tools/shot.mjs --out a.png --scene dev/scenes/yours.js --cam "400,250,600,0,10,0,40" --frames 3 --q medium --w 1280 --h 720
node tools/shot.mjs --shots shots.json         # several shots in one browser session
```
It prints JSON: per-system init status/time, draw calls, triangles, frame ms, page errors, console errors (exit code 1 on errors).
Then LOOK at the PNG (Read tool) — every visual claim in your report must come from a screenshot you inspected.
Software GL is slow (seconds per frame) and runs the `low` tier by default; pass `--q high` for a few beauty checks.
Test the stateless rule: the same `--t` must give the same picture whether reached directly or after other times.
Dev fixture for isolated tests: `dev/scenes/<name>.js` → `export default async (app) => { ... }` (may create objects, register fake entities, set app.plan).
Useful: `--eval "return app.stats"`; URL params are listed at the top of `src/main.js`.

## 10. History first

`research/*.md|json` are the factual basis (they carry confidence levels and source lists). Use them; do not contradict them from
memory; where they are silent and you must interpolate, keep it plausible and mark it (`"basis": "interpolated"`) in your data file.
Record anything you had to invent in your system README under "Reconstruction notes".

## 11. Simulation logic is renderer-free and runs in node

Everything that decides *where things are and what happens when* (ship positions and states, flight paths, ordnance,
impacts, fires, vignette timelines, radar plots, shot timing) lives in modules that import only `three` (for maths),
`src/core/geo.js|math.js|timeutil.js|noise.js|util.js` and JSON data — no DOM, no WebGL, no `window`. Rendering modules
(`index.js` of each system) consume them. That keeps the history testable in milliseconds:
```
node --import ./tools/node-three.mjs tools/your-check.mjs      # 'three' resolves to the vendored build, as in the browser
```
`tools/node-env.mjs` exports `createNodeApp()` → an app-like object with `geo`, `height` (the real rasters decoded with
zlib), `registry`, `events`, `loadJSON`, `time`, `env`, `getSystem`. Logic modules therefore take `app` and use only those
fields. Write checks that print tables and assert invariants (counts match the research totals, ships float in water,
flight speeds and turn rates are physical, nothing flies through a mountain, every documented hit has an attacker).
