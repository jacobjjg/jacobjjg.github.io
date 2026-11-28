// Deterministic noise: JS implementations + GLSL chunks to paste into shaders.
// JS and GLSL versions are NOT bit-identical; use one or the other for a given feature.

// ---- JS ---------------------------------------------------------------------------------
function ihash(x, y, z) {
  let h = Math.imul(x, 374761393) ^ Math.imul(y, 668265263) ^ Math.imul(z, 1440662683);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
const fade = (t) => t * t * t * (t * (t * 6 - 15) + 10);

/** value noise in [0,1], 2D. */
export function vnoise2(x, y, seed = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = fade(xf), v = fade(yf);
  const a = ihash(xi, yi, seed), b = ihash(xi + 1, yi, seed), c = ihash(xi, yi + 1, seed), d = ihash(xi + 1, yi + 1, seed);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
/** value noise in [0,1], 3D. */
export function vnoise3(x, y, z, seed = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const u = fade(x - xi), v = fade(y - yi), w = fade(z - zi);
  const s = seed * 7919;
  const n = (i, j, k) => ihash(xi + i, yi + j, zi + k + s);
  const x00 = n(0, 0, 0) + (n(1, 0, 0) - n(0, 0, 0)) * u, x10 = n(0, 1, 0) + (n(1, 1, 0) - n(0, 1, 0)) * u;
  const x01 = n(0, 0, 1) + (n(1, 0, 1) - n(0, 0, 1)) * u, x11 = n(0, 1, 1) + (n(1, 1, 1) - n(0, 1, 1)) * u;
  const y0 = x00 + (x10 - x00) * v, y1 = x01 + (x11 - x01) * v;
  return y0 + (y1 - y0) * w;
}
/** fractal value noise in [0,1]. */
export function fbm2(x, y, octaves = 5, lacunarity = 2, gain = 0.5, seed = 0) {
  let amp = 0.5, sum = 0, norm = 0;
  for (let i = 0; i < octaves; i++) { sum += amp * vnoise2(x, y, seed + i * 31); norm += amp; x *= lacunarity; y *= lacunarity; amp *= gain; }
  return sum / norm;
}
export function fbm3(x, y, z, octaves = 4, lacunarity = 2, gain = 0.5, seed = 0) {
  let amp = 0.5, sum = 0, norm = 0;
  for (let i = 0; i < octaves; i++) { sum += amp * vnoise3(x, y, z, seed + i * 31); norm += amp; x *= lacunarity; y *= lacunarity; z *= lacunarity; amp *= gain; }
  return sum / norm;
}
/** smooth 1D noise in [-1,1] - handy for camera shake / wobble as a pure function of time. */
export function wobble(t, seed = 0) {
  return vnoise2(t, seed * 17.13, seed) * 2 - 1;
}

// ---- GLSL -------------------------------------------------------------------------------
/** hash + value noise + fbm + simplex + worley.  Paste once per shader stage: `${GLSL_NOISE}` */
export const GLSL_NOISE = /* glsl */`
#ifndef PH_NOISE
#define PH_NOISE
float phHash11(float p){ p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p); }
float phHash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float phHash13(vec3 p3){ p3 = fract(p3 * 0.1031); p3 += dot(p3, p3.zyx + 31.32); return fract((p3.x + p3.y) * p3.z); }
vec2  phHash22(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973)); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.xx + p3.yz) * p3.zy); }
vec3  phHash33(vec3 p3){ p3 = fract(p3 * vec3(0.1031, 0.1030, 0.0973)); p3 += dot(p3, p3.yxz + 33.33); return fract((p3.xxy + p3.yxx) * p3.zyx); }
float phNoise2(vec2 p){
  vec2 i = floor(p), f = fract(p); vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
  float a = phHash12(i), b = phHash12(i + vec2(1.0, 0.0)), c = phHash12(i + vec2(0.0, 1.0)), d = phHash12(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float phNoise3(vec3 p){
  vec3 i = floor(p), f = fract(p); vec3 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(phHash13(i), phHash13(i + vec3(1,0,0)), u.x), mix(phHash13(i + vec3(0,1,0)), phHash13(i + vec3(1,1,0)), u.x), u.y),
             mix(mix(phHash13(i + vec3(0,0,1)), phHash13(i + vec3(1,0,1)), u.x), mix(phHash13(i + vec3(0,1,1)), phHash13(i + vec3(1,1,1)), u.x), u.y), u.z);
}
float phFbm2(vec2 p){ float a = 0.5, s = 0.0; mat2 m = mat2(1.6, 1.2, -1.2, 1.6); for (int i = 0; i < 5; i++) { s += a * phNoise2(p); p = m * p; a *= 0.5; } return s / 0.96875; }
float phFbm3(vec3 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 4; i++) { s += a * phNoise3(p); p = p * 2.02 + vec3(13.1, 7.7, 3.3); a *= 0.5; } return s / 0.9375; }
// simplex 2D, range about [-1, 1]
vec3 phPermute(vec3 x){ return mod(((x * 34.0) + 1.0) * x, 289.0); }
float phSimplex2(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy)); vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz; x12.xy -= i1; i = mod(i, 289.0);
  vec3 p = phPermute(phPermute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0); m = m * m; m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0; vec3 h = abs(x) - 0.5; vec3 ox = floor(x + 0.5); vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g; g.x = a0.x * x0.x + h.x * x0.y; g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}
// worley (cellular) 2D: returns vec2(F1, F2) distances in cell units
vec2 phWorley2(vec2 p){
  vec2 n = floor(p), f = fract(p); float f1 = 8.0, f2 = 8.0;
  for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
    vec2 g = vec2(float(i), float(j)); vec2 o = phHash22(n + g); vec2 r = g + o - f; float d = dot(r, r);
    if (d < f1) { f2 = f1; f1 = d; } else if (d < f2) { f2 = d; }
  }
  return sqrt(vec2(f1, f2));
}
#endif
`;
