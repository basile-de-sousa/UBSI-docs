mxStencilRegistry.allowEval = false;
const allowedOrigin = new URL(location.href).origin;
const status = document.querySelector('#status');
let viewer;
function report(state, message) {status.textContent=message; parent.postMessage({ubsiViewer:state,message}, allowedOrigin);}
window.addEventListener('message', event=>{
  if(event.source!==parent || event.origin!==allowedOrigin || event.data?.ubsiDocument!=='drawio') return;
  try {
    if(viewer) viewer.graph.destroy();
    const diagram=document.querySelector('#diagram');diagram.replaceChildren();
    diagram.setAttribute('data-mxgraph', JSON.stringify({xml:event.data.xml,nav:false,resize:false,lightbox:false,edit:null,toolbar:'',border:20}));
    GraphViewer.createViewerForElement(diagram, instance=>{viewer=instance;viewer.graph.setEnabled(false);viewer.graph.setPanning(true);viewer.graph.panningHandler.useLeftButtonForPanning=true;viewer.graph.openLink=()=>null;viewer.graph.fit(20);report('ready','Lecture seule · glissez pour déplacer le diagramme');});
  } catch {report('failed','L’aperçu ne peut pas être affiché. Réimportez un schéma simplifié.');}
});
document.querySelector('#in').onclick=()=>viewer?.graph.zoomIn();
document.querySelector('#out').onclick=()=>viewer?.graph.zoomOut();
document.querySelector('#fit').onclick=()=>viewer?.graph.fit(20);
parent.postMessage({ubsiViewer:'waiting'},allowedOrigin);

window.addEventListener("message",event=>{if(event.source===parent && event.origin===allowedOrigin && event.data?.ubsiPing)parent.postMessage({ubsiViewer:"waiting"},allowedOrigin);});

// Inert DOM diagnostics for the embedded viewer's security boundary.
let parentAccess = parent === window ? 'standalone' : 'blocked';
if (parent !== window) {
  try { if (parent.document) parentAccess = 'readable'; } catch { /* Opaque sandbox origin. */ }
}
document.documentElement.dataset.parentAccess = parentAccess;
