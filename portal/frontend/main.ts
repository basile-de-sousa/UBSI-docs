import { initializeDocuments } from "./documents";
import { initializeAssistant } from "./assistant";
import htmx from "htmx.org";
import "./styles.css";

// Future interactions must work under the site's restrictive CSP.
htmx.config.allowEval = false;
htmx.config.allowScriptTags = false;
htmx.config.includeIndicatorStyles = false;
htmx.config.selfRequestsOnly = true;
htmx.config.historyCacheSize = 0;

const toggle = document.querySelector<HTMLButtonElement>("[data-menu-toggle]");
const sidebar = document.querySelector<HTMLElement>("[data-sidebar]");
const menuClose = document.querySelector<HTMLButtonElement>("[data-menu-close]");
if (toggle && sidebar) {
  const closeMenu = () => {
    toggle.setAttribute("aria-expanded", "false");
    sidebar.classList.remove("is-open");
  };
  toggle.addEventListener("click", () => {
    const open = toggle.getAttribute("aria-expanded") !== "true";
    toggle.setAttribute("aria-expanded", String(open));
    sidebar.classList.toggle("is-open", open);
    if (open) menuClose?.focus();
  });
  menuClose?.addEventListener("click", () => {
    closeMenu();
    toggle.focus();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      closeMenu();
      toggle.focus();
    }
  });
  document.addEventListener("click", (event) => {
    if (event.target instanceof Node && !sidebar.contains(event.target) && !toggle.contains(event.target)) closeMenu();
  });
  window.matchMedia("(min-width: 901px)").addEventListener("change", closeMenu);
}

document.querySelectorAll<HTMLFormElement>("[data-content-form]").forEach(contentForm => {
  let dirty = contentForm.dataset.conflict === "true";
  const publishButtons = document.querySelectorAll<HTMLButtonElement>("[data-publish-button]");
  const status = contentForm.querySelector<HTMLElement>("[data-save-status]");
  const markDirty = () => {
    dirty = true;
    contentForm.dataset.dirty = "true";
    if (status) status.textContent = "Modifications non enregistrées · enregistrez avant de publier";
    publishButtons.forEach(button => { button.disabled = true; });
  };
  contentForm.addEventListener("input", markDirty);
  contentForm.addEventListener("change", markDirty);
  contentForm.addEventListener("submit", () => {
    dirty = false;
    contentForm.dataset.dirty = "false";
    contentForm.setAttribute("aria-busy", "true");
    if (status) status.textContent = "Enregistrement en cours…";
  });
  window.addEventListener("beforeunload", event => { if (dirty) event.preventDefault(); });
  if (dirty) markDirty();
});
if (document.querySelector("[data-editor]")) {
  import("./editor").then(module => module.mountEditor()).catch(() => {
    const error = document.querySelector<HTMLElement>("[data-editor-error]");
    if (error) { error.hidden = false; error.textContent = "L’éditeur n’est pas disponible. Rechargez la page avant de modifier le texte."; }
  });
}
const missingSection = document.querySelector<HTMLElement>("[data-missing-section]");
const checkSection = () => {
  if (missingSection && location.hash.startsWith("#section-") && !document.getElementById(location.hash.slice(1))) missingSection.hidden = false;
};
checkSection();
window.addEventListener("hashchange", checkSection);

document.querySelectorAll<HTMLFormElement>("[data-transition-form]").forEach(form => {
  let pending = false;
  form.addEventListener("submit", event => {
    if (pending) { event.preventDefault(); return; }
    pending = true;
    form.setAttribute("aria-busy", "true");
    const status = form.querySelector<HTMLElement>("[data-transition-status]");
    if (status) { status.hidden = false; status.textContent = "Publication en cours…"; }
  });
  window.addEventListener("pageshow", () => {
    pending = false;
    form.removeAttribute("aria-busy");
    const status = form.querySelector<HTMLElement>("[data-transition-status]");
    if (status) status.hidden = true;
  });
});

initializeDocuments();
initializeAssistant();
