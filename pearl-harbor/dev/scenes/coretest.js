// Dev fixture: exercises the fog patch, log depth and the custom-shader helpers.
import * as THREE from 'three';
import { VERT_PARS, VERT_END, FRAG_PARS, FRAG_BEGIN, FRAG_END, GLSL_LIGHTING } from '../../src/core/atmosphere.js';
import { GLSL_NOISE } from '../../src/core/noise.js';
export default async function (app) {
  const g = new THREE.Group();
  // big ground plane (built-in material) + water-level plane almost coplanar (log depth test)
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(200000, 200000), new THREE.MeshStandardMaterial({ color: 0x4a6b3a, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = -0.5; g.add(ground);
  const mat = new THREE.ShaderMaterial({
    fog: true, uniforms: app.makeUniforms({ uCol: { value: new THREE.Color(0x8a8f96) } }),
    vertexShader: `${VERT_PARS} varying vec3 vN; varying vec3 vW;
      void main(){ vN = normalize(mat3(modelMatrix) * normal); vec4 wp = modelMatrix * vec4(position,1.0); vW = wp.xyz;
        vec4 mvPosition = viewMatrix * wp; gl_Position = projectionMatrix * mvPosition; ${VERT_END} }`,
    fragmentShader: `${FRAG_PARS} ${GLSL_LIGHTING} ${GLSL_NOISE} uniform vec3 uCol; uniform vec3 uOrigin; varying vec3 vN; varying vec3 vW;
      void main(){ ${FRAG_BEGIN} vec3 n = normalize(vN); float k = 0.8 + 0.2 * phFbm2((vW.xz + uOrigin.xz) * 0.05);
        vec3 col = uCol * k * phIrradiance(n); gl_FragColor = vec4(col, 1.0); ${FRAG_END} }`,
  });
  for (let i = 0; i < 40; i++) {
    const d = 200 * Math.pow(1.22, i);            // 200 m .. ~470 km
    const s = 20 + d * 0.06;
    const m = new THREE.Mesh(new THREE.BoxGeometry(s, s * 2, s), i % 2 ? mat : new THREE.MeshStandardMaterial({ color: 0x8a8f96, roughness: 0.8 }));
    m.position.set((i % 2 ? 1 : -1) * s * 1.5, s, -d); g.add(m);
  }
  app.world.add(g);
}
