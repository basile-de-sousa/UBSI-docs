// Decode the trusted pinned stencil bundle to qualify names before publication.
import {readFile, writeFile} from 'node:fs/promises';
import vm from 'node:vm';
import {inflateRawSync} from 'node:zlib';
const stencil = await readFile('public/vendor/stencils.min.js', 'utf8');
const viewer = await readFile('public/vendor/viewer-static.min.js', 'utf8');
const registry = {loadStencil(){throw new Error('Unknown bundled stencil');}};
const context = {mxStencilRegistry: registry, STENCIL_PATH:'/stencils', pako:{inflateRaw: x=>new Uint8Array(inflateRawSync(x))}, atob, TextDecoder, Uint8Array, DataView, Map, window:{setTimeout}};
vm.runInNewContext(stencil, context, {timeout:30000});
const names = new Set();
function collect(root){
  if(root.nodeName==='stencils'){for(let n=root.firstChild;n;n=n.nextSibling) collect(n);return;}
  const prefix = (root.getAttribute('name') || '').toLowerCase();
  for(let n=root.firstChild;n;n=n.nextSibling){const name=n.getAttribute('name');if(name) names.add((prefix ? prefix+'.':'')+name.replace(/ /g,'_').toLowerCase());}
}
for(const match of stencil.matchAll(/f\['([^']+)'\] = /g)) collect(registry.loadStencil('/stencils/'+match[1]).documentElement);
const builtins = new Set(['rectangle','ellipse','rhombus','cylinder','connector','actor','triangle','hexagon','cloud','line','arrow','arrowConnector','swimlane','label','image','doubleEllipse']);
for(const match of viewer.matchAll(/registerShape\("([^"]+)"/g)) builtins.add(match[1]);
await writeFile('.vendor/drawio-shapes.json', JSON.stringify({names:[...names].sort(),builtins:[...builtins].sort()}));
console.log(`Qualified ${names.size} stencil names and ${builtins.size} built-in shapes.`);
