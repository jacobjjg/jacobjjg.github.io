// System manifest: every system of the documentary, in the order they are initialised.
// `order` is the per-frame update order (lower first; order < 10 = owners of time and camera).
// A module that does not exist yet is skipped at boot, so the app runs while it is being built.
// Each module default-exports a system object: { id, order?, init(app), update(app), resize?, dispose? }.
export const SYSTEMS = [
  { id: 'director',      order: 0,  path: './director/index.js' },      // doc time -> sim time, shots, camera
  { id: 'controls',      order: 5,  path: './ui/controls.js' },         // explore-mode camera + input
  { id: 'sky',           order: 20, path: './sky/index.js' },           // sky dome, sun/moon lights, shadows, env map, app.env
  { id: 'clouds',        order: 22, path: './sky/clouds.js' },
  { id: 'terrain',       order: 30, path: './terrain/index.js' },       // Oahu from the baked rasters
  { id: 'ocean',         order: 32, path: './ocean/index.js' },
  { id: 'installations', order: 34, path: './installations/index.js' }, // harbor works, airfields, towns, radar sites
  { id: 'ships',         order: 12, path: './ships/index.js' },         // every ship: entities, models, damage states, motion
  { id: 'battle',        order: 10, path: './battle/index.js' },        // the battle plan: flights, ordnance, impacts, fires
  { id: 'aircraft',      order: 40, path: './aircraft/index.js' },      // renders every aircraft of the plan + parked aircraft
  { id: 'people',        order: 44, path: './people/index.js' },        // crowds and vignettes
  { id: 'radar',         order: 46, path: './radar/index.js' },         // Opana SCR-270, plots, scope
  { id: 'weapons',       order: 48, path: './weapons/index.js' },       // ordnance in flight, torpedo runs, tracers, flak, splashes, wakes
  { id: 'fx',            order: 50, path: './fx/index.js' },            // smoke, fire, explosions, debris
  { id: 'map',           order: 60, path: './map/index.js' },           // strategic Pacific map / globe sequences
  { id: 'audio',         order: 70, path: './audio/index.js' },
  { id: 'hud',           order: 80, path: './ui/hud.js' },              // captions, clock, labels, chapters, minimap
  { id: 'post',          order: 90, path: './post/index.js' },          // HDR composer, bloom, grade, grain (sets app.renderFn)
];
