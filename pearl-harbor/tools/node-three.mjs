// Lets plain node import the project's browser ES modules (which use the bare specifier 'three').
//   node --import ./tools/node-three.mjs tools/some-check.mjs
// Maps 'three' and 'three/addons/*' to the vendored copies, exactly like the import map in index.html.
import { register } from 'node:module';
register('./node-three-hooks.mjs', import.meta.url);
