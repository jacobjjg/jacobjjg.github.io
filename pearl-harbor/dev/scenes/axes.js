// Dev fixture: reference objects at the origin so an empty sandbox shows something measurable.
import * as THREE from 'three';
export default async function (app) {
  const g = new THREE.Group();
  const grid = new THREE.GridHelper(2000, 20, 0xffaa00, 0x335577);
  g.add(grid);
  const box = new THREE.Mesh(new THREE.BoxGeometry(30, 20, 185), new THREE.MeshStandardMaterial({ color: 0x8a8f96, roughness: 0.7 }));
  box.position.y = 10; g.add(box);                       // a battleship-sized block, bow toward -Z (north)
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 40), new THREE.MeshStandardMaterial({ color: 0xcc3322 }));
  mast.position.set(0, 40, -60); g.add(mast);            // red mast near the bow
  app.world.add(g);
}
