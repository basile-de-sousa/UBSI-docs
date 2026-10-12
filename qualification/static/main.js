import * as pdfjs from "/pdf.mjs";
const failures = [];
let drawioReport;
const violations = [];
document.addEventListener("securitypolicyviolation", event => violations.push(`${event.violatedDirective}: ${event.blockedURI}`));
function diagnostics() {
  const urls = performance.getEntriesByType("resource").map(entry => entry.name);
  const all = [...urls, ...(drawioReport?.resourceUrls || [])];
  const remote = all.filter(url => !url.startsWith(location.origin) && !url.startsWith("data:") && !url.startsWith("blob:"));
  const report = {drawio: drawioReport, externalResources: remote, violations, failures, resources: [...new Set(all)]};
  document.querySelector("#diagnostics").textContent = `Ressources externes : ${remote.length} · Violations CSP : ${violations.length + (drawioReport?.violations.length || 0)} · Erreurs : ${failures.length}`;
  document.querySelector("#resource-list").textContent = JSON.stringify(report, null, 2);
}
window.addEventListener("message", event => {
  if (event.source === document.querySelector("iframe").contentWindow && event.data?.m0Drawio) {drawioReport = event.data.m0Drawio; diagnostics();}
});
const fileResults = await fetch("/files-results.json").then(response => response.json());
document.querySelector("#files-status").textContent = `${fileResults.filter(row => row.passed).length} / ${fileResults.length} contrôles réussis`;
document.querySelector("#files-results").textContent = JSON.stringify(fileResults, null, 2);
const sheets = await fetch("/workbook.json").then(response => response.json());
sheets.push(await fetch("/csv.json").then(response => response.json()));
const select = document.querySelector("#sheet");
for (const [index, sheet] of sheets.entries()) {const option = document.createElement("option"); option.value = index; option.textContent = sheet.name + (sheet.hidden ? " · Masquée" : ""); select.append(option);}
function showSheet() {
  const table = document.querySelector("#workbook"); table.replaceChildren();
  for (const row of sheets[Number(select.value)].rows) {
    const tr = document.createElement("tr");
    for (const cell of row) {const td = document.createElement("td"); td.textContent = cell.value; if(cell.bold) td.style.fontWeight = "bold"; tr.append(td);}
    table.append(tr);
  }
}
select.addEventListener("change", showSheet); showSheet();
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.mjs";
let page = 1, scale = 1.2, pdf;
async function showPdf() {
  try {
    const documentPage = await pdf.getPage(page);
    const viewport = documentPage.getViewport({scale});
    const canvas = document.querySelector("#pdf"); canvas.width = viewport.width; canvas.height = viewport.height;
    await documentPage.render({canvasContext: canvas.getContext("2d"), viewport}).promise;
    document.querySelector("#pdf-status").textContent = `Page ${page} / ${pdf.numPages}`;
    document.querySelector("#pdf-prev").disabled = page === 1;
    document.querySelector("#pdf-next").disabled = page === pdf.numPages;
    diagnostics();
  } catch(error) {failures.push(String(error)); diagnostics();}
}
document.querySelector("#pdf-prev").addEventListener("click", async () => {page--; await showPdf();});
document.querySelector("#pdf-next").addEventListener("click", async () => {page++; await showPdf();});
document.querySelector("#pdf-zoom").addEventListener("click", async () => {scale += .2; await showPdf();});
try {pdf = await pdfjs.getDocument({url: "/synthetic.pdf", isEvalSupported: false, useSystemFonts: true, enableXfa: false}).promise; await showPdf();}
catch(error) {failures.push(String(error)); diagnostics();}
setTimeout(diagnostics, 2000);
