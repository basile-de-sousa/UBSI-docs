// Set local defaults before the pinned vendor initializes. No external requests.
const vendorOrigin = new URL(location.href).origin;
for (const key of ['PROXY_URL','STYLE_PATH','SHAPES_PATH','STENCIL_PATH','DRAW_MATH_URL','GRAPH_IMAGE_PATH','mxImageBasePath','mxBasePath','DRAWIO_VIEWER_URL','DRAWIO_SERVER_URL']) window[key] = `${vendorOrigin}/static/vendor/${key}/`;
window.mxLoadStylesheets = false;
window.urlParams = {offline:'1', plugins:'0', lightbox:'0', chrome:'0'};
