// Global aerial-perspective patch + shared shader plumbing.
//
// installAtmosphere() replaces three.js' fog shader chunks with an analytic exponential
// HEIGHT fog that also tints toward the sun (in-scatter glow).  Every built-in material
// (and every custom ShaderMaterial that includes the standard fog chunks with `fog: true`)
// gets consistent atmospheric perspective, driven by scene.fog (a THREE.FogExp2 whose
// `density` is the extinction coefficient per metre at sea level) plus the shared values below.
import * as THREE from 'three';

/** Shared (by reference) typed-array uniform values.  The app updates them every frame from app.env. */
export const fogShared = {
  sunDir: new Float32Array([0.3, 0.5, 0.8]),     // world-space unit vector toward the sun (or moon at night)
  sunColor: new Float32Array([1.0, 0.85, 0.65]), // fog colour when looking toward the sun
  params: new Float32Array([1 / 1800, 0, 6, 1]), // x: height falloff (1/m)  y: reference height (m)  z: sun glow exponent  w: max opacity
};

let installed = false;

export function installAtmosphere() {
  if (installed) return;
  installed = true;

  const add = (u) => {
    u.fogSunDir = { value: fogShared.sunDir };
    u.fogSunColor = { value: fogShared.sunColor };
    u.fogParams = { value: fogShared.params };
  };
  add(THREE.UniformsLib.fog);
  for (const k in THREE.ShaderLib) {
    const u = THREE.ShaderLib[k].uniforms;
    if (u && u.fogColor) add(u);
  }

  THREE.ShaderChunk.fog_pars_vertex = /* glsl */`
#ifdef USE_FOG
  varying vec3 vFogViewPos;
#endif`;

  THREE.ShaderChunk.fog_vertex = /* glsl */`
#ifdef USE_FOG
  vFogViewPos = mvPosition.xyz;
#endif`;

  THREE.ShaderChunk.fog_pars_fragment = /* glsl */`
#ifdef USE_FOG
  uniform vec3 fogColor;
  varying vec3 vFogViewPos;
  #ifdef FOG_EXP2
    uniform float fogDensity;
  #else
    uniform float fogNear;
    uniform float fogFar;
  #endif
  uniform vec3 fogSunDir;
  uniform vec3 fogSunColor;
  uniform vec4 fogParams;
  // returns vec4(fog colour, fog amount) for a fragment at view-space position vp
  vec4 phFog( vec3 vp ) {
    float dist = length( vp );
    vec3 dirW = normalize( vp ) * mat3( viewMatrix );         // view -> world direction
    #ifdef FOG_EXP2
      float k = fogParams.x;
      float camH = max( cameraPosition.y - fogParams.y, -200.0 );
      float a = k * dirW.y * dist;
      float integ = abs( a ) > 1e-3 ? ( 1.0 - exp( - a ) ) / a : 1.0 - 0.5 * a;
      float od = fogDensity * exp( - k * camH ) * dist * integ;
      float amount = 1.0 - exp( - od );
    #else
      float amount = smoothstep( fogNear, fogFar, dist );
    #endif
    float sunAmt = pow( max( dot( dirW, fogSunDir ), 0.0 ), fogParams.z );
    return vec4( mix( fogColor, fogSunColor, sunAmt ), clamp( amount, 0.0, 1.0 ) * fogParams.w );
  }
#endif`;

  THREE.ShaderChunk.fog_fragment = /* glsl */`
#ifdef USE_FOG
  {
    vec4 phF = phFog( vFogViewPos );
    gl_FragColor.rgb = mix( gl_FragColor.rgb, phF.rgb, phF.a );
  }
#endif`;
}

// ---------------------------------------------------------------------------------------
// GLSL boilerplate for custom ShaderMaterials (NOT RawShaderMaterial).
// Use them so custom shaders work with the logarithmic depth buffer, the global fog and
// both render paths (post-processing HDR target and direct-to-screen).
//
//   vertexShader:   `${VERT_PARS}  ...  void main(){ ...; vec4 mvPosition = modelViewMatrix * vec4(p,1.0);
//                      gl_Position = projectionMatrix * mvPosition;  ${VERT_END} }`
//   fragmentShader: `${FRAG_PARS}  ...  void main(){ ${FRAG_BEGIN} ...; gl_FragColor = vec4(col, a);  ${FRAG_END} }`
//   material:       new THREE.ShaderMaterial({ uniforms: app.makeUniforms({...}), fog: true, ... })
// ---------------------------------------------------------------------------------------
export const VERT_PARS = /* glsl */`
#include <common>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
`;
export const VERT_END = /* glsl */`
#include <logdepthbuf_vertex>
#include <fog_vertex>
`;
export const FRAG_PARS = /* glsl */`
#include <common>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
`;
export const FRAG_BEGIN = /* glsl */`
#include <logdepthbuf_fragment>
`;
export const FRAG_END = /* glsl */`
#include <tonemapping_fragment>
#include <colorspace_fragment>
#include <fog_fragment>
`;
/** Same as FRAG_END without fog (emissive / additive effects, sky). */
export const FRAG_END_NOFOG = /* glsl */`
#include <tonemapping_fragment>
#include <colorspace_fragment>
`;

/**
 * Scene lighting for custom shaders, matching what built-in PBR materials receive.
 * All colours already include the 1/PI Lambert factor:  diffuse = albedo * phIrradiance(n).
 * Requires the shared uniforms from app.makeUniforms().
 */
export const GLSL_LIGHTING = /* glsl */`
#ifndef PH_LIGHTING
#define PH_LIGHTING
uniform vec3 uSunDir;        // world space, toward the sun
uniform vec3 uSunColor;      // sun radiance scale (x 1/PI)
uniform vec3 uMoonDir;
uniform vec3 uMoonColor;
uniform vec3 uAmbientSky;    // hemisphere ambient from above (x 1/PI)
uniform vec3 uAmbientGround; // hemisphere ambient from below (x 1/PI)
vec3 phAmbient( vec3 n ) { return mix( uAmbientGround, uAmbientSky, n.y * 0.5 + 0.5 ); }
vec3 phIrradiance( vec3 n ) {
  return uSunColor * max( dot( n, uSunDir ), 0.0 ) + uMoonColor * max( dot( n, uMoonDir ), 0.0 ) + phAmbient( n );
}
// wrap-lit variant for soft volumes (smoke, foliage, cloth): w in 0..1
vec3 phIrradianceWrap( vec3 n, float w ) {
  float s = max( ( dot( n, uSunDir ) + w ) / ( 1.0 + w ), 0.0 );
  float m = max( ( dot( n, uMoonDir ) + w ) / ( 1.0 + w ), 0.0 );
  return uSunColor * s + uMoonColor * m + phAmbient( n );
}
#endif
`;
