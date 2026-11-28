// Geodesy + astronomy for the Pearl Harbor reconstruction.
//
// WORLD FRAME (the single coordinate system used by every system):
//   origin  = Ford Island, lat 21.3650 N, lon 157.9600 W, sea level
//   +X east, +Y up, +Z SOUTH (so north is -Z).  Units: metres.
//   heading / bearing: degrees true, clockwise from north.  heading 0 -> -Z, 90 -> +X.
//
// MODEL FRAME (every vehicle / ship / aircraft model):
//   nose / bow toward local -Z, starboard / right wing toward +X, up +Y, origin at the
//   waterline amidships (ships) or centre of gravity (aircraft).
//   object.rotation.y = -headingDeg * PI / 180 points the model along a heading.
import * as THREE from 'three';

export const LAT0 = 21.3650;
export const LON0 = -157.9600;
export const M_PER_DEG_LAT = 110721.79;
export const M_PER_DEG_LON = 103715.50;

export const NMI = 1852.0;       // nautical mile (m)
export const MILE = 1609.344;    // statute mile (m)
export const FT = 0.3048;        // foot (m)
export const KT = 0.514444;      // knot (m/s)
export const DEG = Math.PI / 180;

// World rectangles covered by the terrain rasters (x0 west, x1 east, z0 north, z1 south).
export const RECT_ISLAND = Object.freeze({ x0: -40960, x1: 40960, z0: -45568, z1: 19968 });
export const RECT_HARBOR = Object.freeze({ x0: -8192, x1: 8192, z0: -5120, z1: 11264 });

/** lat/lon (deg) [+ altitude m] -> world Vector3. */
export function toWorld(lat, lon, alt = 0, out = new THREE.Vector3()) {
  return out.set((lon - LON0) * M_PER_DEG_LON, alt, -(lat - LAT0) * M_PER_DEG_LAT);
}

/** world x,z -> {lat, lon}. */
export function toLatLon(x, z) {
  return { lat: LAT0 - z / M_PER_DEG_LAT, lon: LON0 + x / M_PER_DEG_LON };
}

/** heading (deg true) -> unit vector in the XZ plane. */
export function headingToVec(deg, out = new THREE.Vector3()) {
  const r = deg * DEG;
  return out.set(Math.sin(r), 0, -Math.cos(r));
}

/** direction (x, z) -> heading deg true in [0, 360). */
export function vecToHeading(x, z) {
  return (Math.atan2(x, -z) / DEG + 360) % 360;
}

/** bearing (deg true) and horizontal distance (m) from point a to point b (world XZ). */
export function bearingDistance(ax, az, bx, bz) {
  const dx = bx - ax, dz = bz - az;
  return { bearing: vecToHeading(dx, dz), distance: Math.hypot(dx, dz) };
}

/** point at `distance` metres along `bearingDeg` from (x, z). */
export function offsetByBearing(x, z, bearingDeg, distance, out = new THREE.Vector3()) {
  const r = bearingDeg * DEG;
  return out.set(x + Math.sin(r) * distance, 0, z - Math.cos(r) * distance);
}

/** Quaternion for a model (nose -Z, up +Y) given heading, pitch (nose up +) and roll (right wing down +), degrees. */
const _e = new THREE.Euler();
export function attitudeQuat(headingDeg, pitchDeg = 0, rollDeg = 0, out = new THREE.Quaternion()) {
  // yaw about Y (negative heading), then pitch about local X (nose up = +X rotation for a -Z nose), then roll about local -Z.
  _e.set(pitchDeg * DEG, -headingDeg * DEG, -rollDeg * DEG, 'YXZ');
  return out.setFromEuler(_e);
}

// ---------------------------------------------------------------------------------------
// Astronomy.  Simulation time `t` = seconds after 1941-12-07 00:00:00 Hawaii time.
// In 1941 Hawaiian Standard Time was UTC-10:30.
// ---------------------------------------------------------------------------------------
export const HST_OFFSET_HOURS = -10.5;
const EPOCH_UTC_MS = Date.UTC(1941, 11, 7, 10, 30, 0); // 00:00 HST 7 Dec 1941

export function simToJulianDate(t) {
  return (EPOCH_UTC_MS + t * 1000) / 86400000 + 2440587.5;
}

const norm360 = (a) => ((a % 360) + 360) % 360;

function altAzFromEquatorial(raDeg, decDeg, jd, latDeg, lonDeg) {
  const d = jd - 2451545.0;
  const T = d / 36525;
  const gmst = norm360(280.46061837 + 360.98564736629 * d + 0.000387933 * T * T);
  const H = norm360(gmst + lonDeg - raDeg) * DEG;
  const phi = latDeg * DEG, dec = decDeg * DEG;
  const sinAlt = Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H);
  const alt = Math.asin(THREE.MathUtils.clamp(sinAlt, -1, 1));
  // azimuth from north, clockwise
  const az = Math.atan2(-Math.cos(dec) * Math.sin(H), Math.sin(dec) * Math.cos(phi) - Math.cos(dec) * Math.cos(H) * Math.sin(phi));
  return { azimuth: norm360(az / DEG), elevation: alt / DEG };
}

function sunEquatorial(jd) {
  const T = (jd - 2451545.0) / 36525;
  const L0 = norm360(280.46646 + 36000.76983 * T + 0.0003032 * T * T);
  const M = norm360(357.52911 + 35999.05029 * T - 0.0001537 * T * T) * DEG;
  const C = Math.sin(M) * (1.914602 - 0.004817 * T - 0.000014 * T * T)
    + Math.sin(2 * M) * (0.019993 - 0.000101 * T) + Math.sin(3 * M) * 0.000289;
  const omega = (125.04 - 1934.136 * T) * DEG;
  const lambda = (L0 + C - 0.00569 - 0.00478 * Math.sin(omega)) * DEG;
  const eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - 0.001813 * T))) / 60) / 60;
  const eps = (eps0 + 0.00256 * Math.cos(omega)) * DEG;
  const ra = norm360(Math.atan2(Math.cos(eps) * Math.sin(lambda), Math.cos(lambda)) / DEG);
  const dec = Math.asin(Math.sin(eps) * Math.sin(lambda)) / DEG;
  return { ra, dec, lambda: lambda / DEG, eps: eps / DEG };
}

function moonEquatorial(jd) {
  const T = (jd - 2451545.0) / 36525;
  const s = (a) => Math.sin(a * DEG);
  const lambda = norm360(218.32 + 481267.881 * T
    + 6.29 * s(135.0 + 477198.87 * T) - 1.27 * s(259.3 - 413335.36 * T)
    + 0.66 * s(235.7 + 890534.22 * T) + 0.21 * s(269.9 + 954397.74 * T)
    - 0.19 * s(357.5 + 35999.05 * T) - 0.11 * s(186.5 + 966404.03 * T));
  const beta = 5.13 * s(93.3 + 483202.02 * T) + 0.28 * s(228.2 + 960400.89 * T)
    - 0.28 * s(318.3 + 6003.15 * T) - 0.17 * s(217.6 - 407332.21 * T);
  const eps = (23.439291 - 0.0130042 * T) * DEG;
  const l = lambda * DEG, b = beta * DEG;
  const x = Math.cos(b) * Math.cos(l);
  const y = Math.cos(eps) * Math.cos(b) * Math.sin(l) - Math.sin(eps) * Math.sin(b);
  const z = Math.sin(eps) * Math.cos(b) * Math.sin(l) + Math.cos(eps) * Math.sin(b);
  return { ra: norm360(Math.atan2(y, x) / DEG), dec: Math.asin(z) / DEG, lambda, beta };
}

function refract(elevDeg) {
  // Saemundsson's formula; small lift near the horizon (deg).
  if (elevDeg < -1.5) return elevDeg;
  const r = 1.02 / Math.tan((elevDeg + 10.3 / (elevDeg + 5.11)) * DEG) / 60;
  return elevDeg + r;
}

/** Direction vector (world frame, unit, pointing FROM the ground TO the body) from azimuth/elevation in degrees. */
export function azElToVec(azimuthDeg, elevationDeg, out = new THREE.Vector3()) {
  const a = azimuthDeg * DEG, e = elevationDeg * DEG;
  return out.set(Math.sin(a) * Math.cos(e), Math.sin(e), -Math.cos(a) * Math.cos(e));
}

/**
 * Sun position for simulation time t (s after 00:00 HST 7 Dec 1941) at lat/lon (default Pearl Harbor).
 * Returns { azimuth, elevation } in degrees (azimuth from north clockwise, elevation refracted).
 * Check: sunrise at Honolulu that morning is about 06:26 HST at azimuth ~113 deg.
 */
export function sunPosition(t, lat = LAT0, lon = LON0) {
  const jd = simToJulianDate(t);
  const s = sunEquatorial(jd);
  const p = altAzFromEquatorial(s.ra, s.dec, jd, lat, lon);
  p.elevation = refract(p.elevation);
  return p;
}

/**
 * Moon position + phase.  Returns { azimuth, elevation, illumination (0..1), waning (bool) }.
 * (The moon was a waning gibbous on 7 Dec 1941; full moon was 3 Dec.)
 */
export function moonPosition(t, lat = LAT0, lon = LON0) {
  const jd = simToJulianDate(t);
  const m = moonEquatorial(jd);
  const s = sunEquatorial(jd);
  const p = altAzFromEquatorial(m.ra, m.dec, jd, lat, lon);
  // topocentric parallax (moon is close): lowers the apparent altitude by up to ~0.95 deg
  p.elevation -= 0.9507 * Math.cos(p.elevation * DEG);
  p.elevation = refract(p.elevation);
  const elong = norm360(m.lambda - s.lambda);
  const cosE = Math.cos(elong * DEG) * Math.cos(m.beta * DEG);
  p.illumination = (1 - cosE) / 2;
  p.waning = elong > 180;
  return p;
}
