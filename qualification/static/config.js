// Override vendor defaults before loading draw.io; CSP rejects any remaining remote URL.
for (const key of ["PROXY_URL", "STYLE_PATH", "SHAPES_PATH", "STENCIL_PATH", "DRAW_MATH_URL", "GRAPH_IMAGE_PATH", "mxImageBasePath", "mxBasePath", "DRAWIO_VIEWER_URL", "DRAWIO_SERVER_URL"]) {
  window[key] = `/local-vendor/${key}/`;
}
window.mxLoadStylesheets = false;
window.urlParams = {offline: "1", plugins: "0", lightbox: "0", chrome: "0"};
window.m0Violations = [];
document.addEventListener("securitypolicyviolation", event => window.m0Violations.push(`${event.violatedDirective}: ${event.blockedURI}`));
