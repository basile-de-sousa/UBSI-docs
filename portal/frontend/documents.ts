export function initializeDocuments(): void {
  const root = document.querySelector<HTMLElement>('[data-document-viewer]');
  if(root){
    const frame=root.querySelector<HTMLIFrameElement>('iframe')!;
    const status=root.querySelector<HTMLElement>('[data-viewer-status]')!;
    const data=JSON.parse(root.querySelector('#viewer-payload')!.textContent!);
    let sent=false;
    const failure=()=>{status.textContent='Aperçu indisponible. Rechargez la page ou contactez un administrateur.';};
    window.addEventListener('message',async event=>{
      if(event.source!==frame.contentWindow || event.origin!=='null' || !event.data?.ubsiViewer)return;
      root.dataset.viewerOrigin=event.origin;
      if(event.data.ubsiViewer==='waiting' && !sent){
        sent=true;
        try{
          const response=await fetch(data.url,{credentials:'same-origin',cache:'no-store',redirect:'error'});
          if(!response.ok)throw new Error('Unavailable');
          if(data.kind==='drawio'){
            const page=await response.json();frame.contentWindow!.postMessage({ubsiDocument:'drawio',xml:page.xml},'*');
          }else{
            const bytes=await response.arrayBuffer();frame.contentWindow!.postMessage({ubsiDocument:data.kind,bytes,page:data.page},'*',[bytes]);
          }
        }catch{failure();}
      }else if(event.data.ubsiViewer==='ready')status.textContent='Aperçu en lecture seule';
      else if(event.data.ubsiViewer==='failed')failure();
    });
    // Covers a frame already initialized before the main bundle attaches.
    frame.contentWindow?.postMessage({ubsiPing:true},'*');
    frame.addEventListener('load',()=>{if(!sent)frame.contentWindow?.postMessage({ubsiPing:true},'*');});
  }
  const pending=document.querySelector<HTMLElement>('[data-file-poll]');
  if(pending){
    let attempts=0;
    const poll=async()=>{
      if(++attempts>60){pending.textContent='La préparation continue. Rechargez la page plus tard ; vérifiez que le worker est démarré.';return;}
      try{
        const response=await fetch(pending.dataset.filePoll!,{credentials:'same-origin',cache:'no-store',redirect:'error'});
        if(!response.ok)throw new Error('Unavailable');
        const result=await response.json();
        if(result.state!=='processing'){
          if(document.querySelector('[data-content-form][data-dirty="true"]')){pending.textContent='La préparation est terminée. Enregistrez vos saisies puis rechargez la page pour voir le résultat.';return;}
          location.assign(result.refresh_url);return;
        }
        window.setTimeout(poll,3000);
      }catch{pending.textContent='Le suivi est indisponible. Rechargez la page pour consulter l’état actuel.';}
    };
    window.setTimeout(poll,3000);
  }
}
