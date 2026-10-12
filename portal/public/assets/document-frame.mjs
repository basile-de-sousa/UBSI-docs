const allowedOrigin=new URL(location.href).origin;
const status=document.querySelector('#status');
let pdf, pageNumber=1, scale=1, currentUrl, renderTask, imageDimensions;
function report(state,message){status.textContent=message;parent.postMessage({ubsiViewer:state,message},allowedOrigin);}
async function render(){
  if(pdf){
    if(renderTask) {try{await renderTask.promise;}catch{}}
    const page=await pdf.getPage(pageNumber);
    let viewport=page.getViewport({scale});
    const ratio=Math.min(1,8000/viewport.width,8000/viewport.height,Math.sqrt(16000000/(viewport.width*viewport.height)));
    viewport=page.getViewport({scale:scale*ratio});
    const canvas=document.querySelector('#pdf');canvas.hidden=false;canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);
    renderTask=page.render({canvasContext:canvas.getContext('2d'),viewport});await renderTask.promise;
    report('ready',`Page ${pageNumber} / ${pdf.numPages} · lecture seule`);
  } else if(imageDimensions){
    const image=document.querySelector('#image');image.width=Math.ceil(imageDimensions[0]*scale);image.height=Math.ceil(imageDimensions[1]*scale);
    report('ready','Image · lecture seule');
  }
}
window.addEventListener('message', async event=>{
 if(event.source!==parent || event.origin!==allowedOrigin || !['image','pdf'].includes(event.data?.ubsiDocument)) return;
 try{
  if(event.data.ubsiDocument==='pdf'){
   // Use the bundled worker handler in this isolated frame. It performs no remote worker fetch.
   const worker=await import('../vendor/pdfjs/build/pdf.worker.mjs');globalThis.pdfjsWorker=worker;
   const pdfjs=await import('../vendor/pdfjs/build/pdf.mjs');
   pdf=await pdfjs.getDocument({data:new Uint8Array(event.data.bytes),isEvalSupported:false,enableXfa:false,useSystemFonts:true,cMapUrl:`${allowedOrigin}/static/vendor/pdfjs/cmaps/`,cMapPacked:true,standardFontDataUrl:`${allowedOrigin}/static/vendor/pdfjs/standard_fonts/`,wasmUrl:`${allowedOrigin}/static/vendor/pdfjs/wasm/`}).promise;
   pageNumber=event.data.page;scale=1;await render();
  }else{
   const image=document.querySelector('#image');if(currentUrl)URL.revokeObjectURL(currentUrl);
   currentUrl=URL.createObjectURL(new Blob([event.data.bytes],{type:'image/png'}));image.src=currentUrl;
   await image.decode();image.hidden=false;imageDimensions=[image.naturalWidth,image.naturalHeight];
   scale=Math.min(1,(document.documentElement.clientWidth-24)/imageDimensions[0]);await render();
  }
 }catch{report('failed','L’aperçu ne peut pas être affiché. Rechargez la page ou réimportez un fichier corrigé.');}
});
document.querySelector('#in').onclick=()=>{scale=Math.min(4,scale*1.25);render().catch(()=>report('failed','Rendu indisponible.'));};
document.querySelector('#out').onclick=()=>{scale=Math.max(.1,scale/1.25);render().catch(()=>report('failed','Rendu indisponible.'));};
document.querySelector('#fit').onclick=async()=>{if(pdf){const page=await pdf.getPage(pageNumber);scale=Math.min(2,(document.documentElement.clientWidth-24)/page.getViewport({scale:1}).width);}else if(imageDimensions) scale=Math.min(1,(document.documentElement.clientWidth-24)/imageDimensions[0]);await render();};
parent.postMessage({ubsiViewer:'waiting'},allowedOrigin);

window.addEventListener("message",event=>{if(event.source===parent && event.origin===allowedOrigin && event.data?.ubsiPing)parent.postMessage({ubsiViewer:"waiting"},allowedOrigin);});

// Inert DOM diagnostics for the embedded viewer's security boundary.
let parentAccess = parent === window ? 'standalone' : 'blocked';
if (parent !== window) {
  try { if (parent.document) parentAccess = 'readable'; } catch { /* Opaque sandbox origin. */ }
}
document.documentElement.dataset.parentAccess = parentAccess;
