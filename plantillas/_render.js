// Ayudas comunes. tools/construir_visual.py inyecta este archivo y `const DATOS = {...}` en cada plantilla.
// Marcado en los textos:
//   **negrita**      -> <b>
//   [[palabra]]      -> palabra destacada con el color de acento
//   _cursiva_        -> <em>
//   \n               -> salto de línea
const esc = s => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function md(s) {
  return esc(s)
    .replace(/\*\*([\s\S]+?)\*\*/g, "<b>$1</b>")
    .replace(/\[\[([\s\S]+?)\]\]/g, '<b class="acento">$1</b>')
    .replace(/(^|[\s(>])_(.+?)_(?=[\s.,;:!?)<]|$)/g, "$1<em>$2</em>")
    .replace(/\[A CONFIRMAR[^\]]*\]/g, m => `<span class="pendiente">${m}</span>`)
    .replace(/\n/g, "<br>");
}
const FLECHA_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
function $(sel) { return document.querySelector(sel); }
function poner(sel, html) { const el = $(sel); if (el) el.innerHTML = html; }
function quitar(sel) { const el = $(sel); if (el) el.remove(); }
function imagen(src, cls = "foto", estilo = "") { return src ? `<img class="${cls}" src="${src}" style="${estilo}">` : ""; }
// Espera a fuentes e imágenes antes de marcar body.listo (el renderizador espera a esa clase).
function listo() {
  const imgs = [...document.images].map(i => i.complete ? Promise.resolve() : new Promise(r => { i.onload = i.onerror = r; }));
  Promise.all([document.fonts.ready, ...imgs]).then(() => document.body.classList.add("listo"));
}
