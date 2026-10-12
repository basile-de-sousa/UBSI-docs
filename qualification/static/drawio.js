const pages = JSON.parse(document.querySelector("#pages").textContent);
mxStencilRegistry.allowEval = false;
let current = 0;
let viewer;
const diagram = document.querySelector("#diagram");
function render() {
  if (viewer) viewer.graph.destroy();
  diagram.replaceChildren();
  diagram.setAttribute("data-mxgraph", JSON.stringify({xml: pages[current], nav: false, resize: true, lightbox: false, edit: null, toolbar: "", border: 10}));
  GraphViewer.createViewerForElement(diagram, instance => {viewer = instance;});
  document.querySelector("#page").textContent = `Page ${current + 1} / ${pages.length}`;
  document.querySelector("#prev").disabled = current === 0;
  document.querySelector("#next").disabled = current === pages.length - 1;
  setTimeout(() => {
    let parentReadable = false;
    try {parentReadable = Boolean(parent.document.body);} catch { /* Expected opaque sandbox origin. */ }
    const report = {page: current + 1, svgElements: diagram.querySelectorAll("svg").length, shapes: diagram.querySelectorAll("path,rect,ellipse,image").length, namedStencilLoaded: Boolean(mxStencilRegistry.stencils["mxgraph.flowchart.database"]), editingEnabled: viewer.graph.isEnabled(), parentReadable, violations: window.m0Violations, resourceUrls: performance.getEntriesByType("resource").map(entry => entry.name)};
    document.querySelector("#render-status").textContent = `Rendu : ${report.shapes} formes · Violations CSP : ${report.violations.length}`;
    parent.postMessage({m0Drawio: report}, "*");
  }, 700);
}
document.querySelector("#next").addEventListener("click", () => {current++; render();});
document.querySelector("#prev").addEventListener("click", () => {current--; render();});
document.querySelector("#zoom").addEventListener("click", () => {viewer.graph.zoomIn();});
render();
