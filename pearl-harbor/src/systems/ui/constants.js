// =========================================================================================
// HISTORICALLY SENSITIVE + EDITORIAL CONSTANTS OF THE UI - everything a historian or editor
// may want to correct lives in this one file (times, names, wording, chart colours).
// Nothing here is used by the 3D reconstruction itself; the HUD only labels what the other
// systems register (app.registry) and plan (app.plan).
// =========================================================================================

/** Opening card wording. */
export const OPENING = {
  date: '7 · XII · 1941',
  title: 'PEARL HARBOR',
  sub: 'December 7, 1941 · A minute-by-minute reconstruction',
  note: 'This film is a reconstruction. Ship positions, timings and the course of both attack waves follow the historical record: action reports, deck logs, the Opana radar plot, Japanese and American accounts.',
  note2: 'Where the record is silent — the exact path of a single aircraft, the movements of individual people — motion is interpolated. Read it as plausible, not as documented.',
  begin: 'Begin the documentary',
  explore: 'Explore the morning freely',
  exploreStart: '07:45',                 // sim time the free exploration starts at
  exploreView: { target: [300, 0, 300], dist: 5200, az: 205, el: 24, fov: 35 }, // establishing view of Ford Island from the SSW
};

/** Explore-mode timeline range (Hawaii time, 7 December 1941). */
export const TIMELINE = { start: '03:30', end: '10:30' };

/**
 * Labelled moments on the explore timeline.
 * `t` is the fallback clock time; when the battle plan is present and `plan(impact)` matches an
 * impact, the time of the FIRST matching impact is used instead, so the label always sits on
 * what the reconstruction actually shows.
 *   06:00 first-wave launch begins (research/kido_butai.json launchOps.wave1.start)
 *   07:02 Opana SCR-270 contact, 132-137 statute miles, 3 deg east of north (research/warnings.md)
 *   07:55 attack begins on Ford Island / Hickam (research/wave1.json timeline)
 *   08:10 Arizona forward magazines - TRADITIONAL time; research/wave1.json gives 08:06 for the hit
 *   08:54 second wave deploys over Oahu
 *   09:30 USS Shaw's forward magazine explodes in floating drydock YFD-2
 */
export const MOMENTS = [
  { t: '06:00', label: 'First wave launches', short: 'Launch', rank: 2 },
  { t: '07:02', label: 'Opana radar contact', short: 'Radar', rank: 3 },
  { t: '07:55', label: 'The attack begins', short: 'Attack', rank: 1 },
  { t: '08:10', label: 'Arizona explodes', short: 'Arizona', rank: 2, plan: (i) => i.kind === 'magazine_explosion' && i.targetId === 'arizona' },
  { t: '08:54', label: 'Second wave arrives', short: '2nd wave', rank: 3 },
  { t: '09:30', label: 'Shaw explodes', short: 'Shaw', rank: 4, plan: (i) => i.kind === 'magazine_explosion' && i.targetId === 'shaw' },
];

/** Impacts at least this large (Impact.size, 1 = 250 kg bomb) are drawn as major ticks on the timeline. */
export const MAJOR_IMPACT_SIZE = 8;

/** Explore-mode time rates (sim seconds per real second). */
export const SIM_RATES = [1, 5, 30, 120];
/** Documentary playback rates. */
export const DOC_RATES = [0.5, 1, 2];

/** Sides. Colours are deliberately muted (chart inks, not game team colours). */
export const SIDES = {
  us: { name: 'United States', short: 'U.S.', color: '#8fb1dc', chart: '#9cc0ee' },
  jp: { name: 'Empire of Japan', short: 'Japan', color: '#d9705f', chart: '#ee7c68' },
  civ: { name: 'Civilian', short: 'Civilian', color: '#cfc7b2', chart: '#d8d0bb' },
  none: { name: '', short: '', color: '#cfc7b2', chart: '#d8d0bb' },
};

/**
 * Ship type codes (entity.type) -> plural section title, singular, sort rank, label priority.
 * Both US Navy hull codes and the long forms used in research/kido_butai.json are accepted.
 */
export const SHIP_TYPES = {
  CV: { plural: 'Aircraft carriers', one: 'Aircraft carrier', rank: 0, pri: 90 },
  BB: { plural: 'Battleships', one: 'Battleship', rank: 1, pri: 85 },
  CA: { plural: 'Heavy cruisers', one: 'Heavy cruiser', rank: 2, pri: 62 },
  CL: { plural: 'Light cruisers', one: 'Light cruiser', rank: 3, pri: 58 },
  DD: { plural: 'Destroyers', one: 'Destroyer', rank: 4, pri: 34 },
  SS: { plural: 'Submarines', one: 'Submarine', rank: 5, pri: 30 },
  AUX: { plural: 'Auxiliaries, minecraft & service craft', one: 'Auxiliary', rank: 6, pri: 26 },
};
export const SHIP_TYPE_ALIASES = {
  aircraft_carrier: 'CV', carrier: 'CV', battleship: 'BB', heavy_cruiser: 'CA', light_cruiser: 'CL', cruiser: 'CL',
  destroyer: 'DD', submarine: 'SS', midget_submarine: 'SS', oiler: 'AUX', tanker: 'AUX',
};
/** Long names for individual hull classification symbols, shown on info cards. */
export const HULL_CODES = {
  BB: 'Battleship', CA: 'Heavy cruiser', CL: 'Light cruiser', CV: 'Aircraft carrier', DD: 'Destroyer', SS: 'Submarine',
  DM: 'Light minelayer', DMS: 'High-speed minesweeper', CM: 'Minelayer', AM: 'Minesweeper', AMC: 'Coastal minesweeper',
  AD: 'Destroyer tender', AR: 'Repair ship', AS: 'Submarine tender', AV: 'Seaplane tender', AVD: 'Seaplane tender (destroyer)',
  AVP: 'Small seaplane tender', AO: 'Fleet oiler', AE: 'Ammunition ship', AF: 'Stores ship', AH: 'Hospital ship',
  AG: 'Miscellaneous auxiliary', AK: 'Cargo ship', AKS: 'General stores issue ship', AT: 'Fleet tug', ASR: 'Submarine rescue vessel',
  PG: 'Gunboat', PT: 'Motor torpedo boat', YFD: 'Floating drydock', YT: 'Harbor tug', YO: 'Fuel oil barge', PY: 'Patrol yacht',
  aircraft_carrier: 'Aircraft carrier', battleship: 'Battleship', heavy_cruiser: 'Heavy cruiser', light_cruiser: 'Light cruiser',
  destroyer: 'Destroyer', submarine: 'Submarine', midget_submarine: 'Midget submarine', oiler: 'Fleet oiler',
};

/**
 * Aircraft type codes (Flight.type) -> display designation.  Allied reporting names ("Kate", "Val", "Zeke")
 * were not assigned until 1942-43 and are deliberately not used for December 1941.
 */
export const AIRCRAFT_TYPES = {
  a6m: { name: 'Mitsubishi A6M2 Type 0 carrier fighter', short: 'A6M2 Zero fighter', role: 'Fighters' },
  b5n: { name: 'Nakajima B5N2 Type 97 carrier attack bomber', short: 'B5N2 attack bomber', role: 'Attack bombers' },
  d3a: { name: 'Aichi D3A1 Type 99 carrier dive bomber', short: 'D3A1 dive bomber', role: 'Dive bombers' },
  e13a: { name: 'Aichi E13A1 Type 0 reconnaissance floatplane', short: 'E13A1 floatplane', role: 'Reconnaissance' },
  e8n: { name: 'Nakajima E8N2 Type 95 reconnaissance floatplane', short: 'E8N2 floatplane', role: 'Reconnaissance' },
  p40: { name: 'Curtiss P-40 Warhawk', short: 'P-40 pursuit', role: 'Pursuit' },
  p36: { name: 'Curtiss P-36A Hawk', short: 'P-36A pursuit', role: 'Pursuit' },
  b17: { name: 'Boeing B-17 Flying Fortress', short: 'B-17 bomber', role: 'Bombers' },
  b18: { name: 'Douglas B-18 Bolo', short: 'B-18 bomber', role: 'Bombers' },
  a20: { name: 'Douglas A-20 Havoc', short: 'A-20 bomber', role: 'Bombers' },
  sbd: { name: 'Douglas SBD Dauntless', short: 'SBD scout bomber', role: 'Scout bombers' },
  pby: { name: 'Consolidated PBY-5 Catalina', short: 'PBY-5 patrol flying boat', role: 'Patrol' },
  f4f: { name: 'Grumman F4F-3 Wildcat', short: 'F4F-3 fighter', role: 'Fighters' },
  os2u: { name: 'Vought OS2U Kingfisher', short: 'OS2U floatplane', role: 'Observation' },
  soc: { name: 'Curtiss SOC Seagull', short: 'SOC floatplane', role: 'Observation' },
  j2f: { name: 'Grumman J2F Duck', short: 'J2F utility amphibian', role: 'Utility' },
  civil: { name: 'Civilian light aircraft', short: 'Civilian aircraft', role: 'Civilian' },
};

/** Flight.state().phase / .load -> wording for the info card. */
export const PHASE_TEXT = {
  deck: 'On deck', takeoff: 'Taking off', cruise: 'In cruise formation', attack: 'Attacking', egress: 'Withdrawing',
  landing: 'Landing', crashing: 'Going down', gone: 'No longer in the air', parked: 'Parked', taxi: 'Taxiing', orbit: 'Orbiting',
};
export const LOAD_TEXT = {
  torpedo: 'one Type 91 aerial torpedo', bomb800: 'one 800 kg armour-piercing bomb', bomb250: 'one 250 kg bomb',
  bomb60: '60 kg bombs', guns: 'guns only',
};
export const IMPACT_TEXT = {
  torpedo_hit: 'Torpedo hit', bomb_hit: 'Bomb hit', bomb_water: 'Near miss', bomb_ground: 'Bomb strike', magazine_explosion: 'Magazine explosion',
  aircraft_crash: 'Aircraft crash', depth_charge: 'Depth charge', shell_splash: 'Shell splash',
};

/** Info-card labels for well-known entity.info keys (anything else is prettified from the key itself). */
export const INFO_LABELS = {
  co: 'Commanding officer', captain: 'Commanding officer', commander: 'Commander', hull: 'Hull number', class: 'Class',
  commissioned: 'Commissioned', launched: 'Launched', displacement: 'Displacement', length: 'Length', beam: 'Beam', crew: 'Complement',
  complement: 'Complement', armament: 'Armament', berth: 'Berth', mooring: 'Mooring', fate: 'Fate', casualties: 'Casualties', killed: 'Killed',
  wounded: 'Wounded', damage: 'Damage', notes: 'Notes', note: 'Note', unit: 'Unit', carrier: 'Carrier', pilot: 'Pilot', crewNames: 'Crew',
  tail: 'Tail code', target: 'Target', basis: 'Basis', confidence: 'Confidence', source: 'Source', sources: 'Sources', aircraft: 'Aircraft',
  wave: 'Wave', role: 'Role', speed: 'Speed', elevation: 'Elevation', status: 'Status', flagship: 'Flagship', division: 'Division',
};
/** entity.info keys never shown on the card (internal plumbing). */
export const INFO_HIDDEN = new Set(['id', 'model', 'mesh', 'lod', 'anchors', 'index', 'seed', 'pos', 'position', 'lat', 'lon', 'x', 'y', 'z', 'heading', 'label', 'labelSub']);

/**
 * 1941 place names used on the chart ONLY when the registry holds fewer than three places (dev sandboxes).
 * Positions are approximate (about +/- 1.5 km), good enough for a chart 300 px wide.  rank: 1 = always shown.
 */
export const FALLBACK_PLACES = [
  { name: 'Pearl Harbor', lat: 21.365, lon: -157.960, rank: 1 },
  { name: 'Honolulu', lat: 21.307, lon: -157.858, rank: 1 },
  { name: 'Hickam Field', lat: 21.335, lon: -157.948, rank: 2 },
  { name: 'Wheeler Field', lat: 21.482, lon: -158.038, rank: 1 },
  { name: 'Ewa', lat: 21.325, lon: -158.045, rank: 2 },
  { name: 'Kaneohe', lat: 21.447, lon: -157.770, rank: 1 },
  { name: 'Bellows Field', lat: 21.366, lon: -157.711, rank: 2 },
  { name: 'Haleiwa', lat: 21.603, lon: -158.103, rank: 2 },
  { name: 'Kahuku Point', lat: 21.712, lon: -157.985, rank: 1 },
  { name: 'Opana', lat: 21.6856, lon: -158.0100, rank: 2 },
  { name: 'Kaena Point', lat: 21.575, lon: -158.281, rank: 1 },
  { name: 'Barbers Point', lat: 21.297, lon: -158.107, rank: 2 },
  { name: 'Diamond Head', lat: 21.262, lon: -157.806, rank: 2 },
];

/**
 * SCHEMATIC outlines (lat, lon) of the neighbouring islands for the wide "approach" chart only.
 * Hand-digitised to about +/- 3 km: they are there so that Oahu is not shown alone in an empty ocean.
 * Oahu itself is always drawn from the elevation raster.
 */
export const NEIGHBOUR_ISLANDS = [
  { name: 'Kauai', pts: [[22.23, -159.40], [22.21, -159.30], [22.10, -159.29], [21.96, -159.33], [21.88, -159.44], [21.90, -159.60], [21.96, -159.72], [22.07, -159.78], [22.17, -159.71], [22.22, -159.58], [22.23, -159.48]] },
  { name: 'Niihau', pts: [[22.02, -160.10], [21.95, -160.05], [21.86, -160.12], [21.78, -160.20], [21.81, -160.25], [21.92, -160.22], [22.00, -160.15]] },
  { name: 'Molokai', pts: [[21.21, -157.25], [21.22, -157.02], [21.20, -156.97], [21.17, -156.85], [21.17, -156.71], [21.10, -156.74], [21.05, -156.88], [21.08, -157.03], [21.09, -157.25], [21.15, -157.30]] },
  { name: 'Lanai', pts: [[20.93, -156.98], [20.92, -156.88], [20.83, -156.81], [20.74, -156.88], [20.74, -156.97], [20.82, -157.05]] },
  { name: 'Maui', pts: [[21.03, -156.63], [20.94, -156.51], [20.90, -156.47], [20.95, -156.30], [20.92, -156.20], [20.80, -156.02], [20.76, -155.98], [20.63, -156.05], [20.58, -156.25], [20.60, -156.42], [20.78, -156.46], [20.79, -156.52], [20.78, -156.62], [20.87, -156.69], [20.97, -156.68]] },
  { name: 'Kahoolawe', pts: [[20.60, -156.57], [20.55, -156.54], [20.51, -156.60], [20.53, -156.69], [20.58, -156.66]] },
];

/** Chart (minimap) views.  Rects are world metres (x east, z south); all are 5:4. */
export const CHART_VIEWS = [
  { id: 'approach', title: 'North of Oahu', rect: { x0: -337500, x1: 337500, z0: -480000, z1: 60000 }, scaleBar: 100000, raster: 'island' },
  { id: 'island', title: 'Oahu', rect: { x0: -40960, x1: 40960, z0: -45568, z1: 19968 }, scaleBar: 10000, raster: 'island' },
  { id: 'harbor', title: 'Pearl Harbor', rect: { x0: -5600, x1: 5600, z0: -3980, z1: 4980 }, scaleBar: 1000, raster: 'harbor' },
];

/** Chart inks. */
export const CHART = {
  seaDeep: [9, 14, 20], seaShelf: [22, 34, 45], landLow: [54, 53, 47], landHigh: [128, 121, 104],
  coast: 'rgba(236,230,214,0.62)', grid: 'rgba(236,230,214,0.10)', gridText: 'rgba(236,230,214,0.42)',
  name: 'rgba(239,233,218,0.86)', nameHalo: 'rgba(6,8,10,0.85)', frustum: 'rgba(239,233,218,0.9)', frustumFill: 'rgba(239,233,218,0.10)',
  radar: 'rgba(201,178,124,0.75)', radarFill: 'rgba(201,178,124,0.07)',
};

/** Label priorities / visibility thresholds (projected radius in px at which a label starts to appear). */
export const LABEL_RULES = {
  ship: { minPx: 7, pri: 30 }, aircraft: { minPx: 3.2, pri: 22 }, place: { minPx: 4.5, pri: 40 },
  person: { minPx: 5, pri: 20 }, group: { minPx: 2.5, pri: 46 },
};
