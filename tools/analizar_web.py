"""
Analiza la web de la marca para sacar su identidad visual y sus textos: colores, tipografías, logo, capturas y el
texto de las páginas. Con eso /empezar escribe el borrador de marca/guia_visual.md, marca/hechos.md y plantillas/_marca.css.

Abre cada página en un navegador sin ventana (el mismo que construye las imágenes) y mide lo que se ve de verdad:
qué colores ocupan más superficie, qué fuentes usan los títulos y el texto, qué color tienen los botones.

Uso:
    python3 tools/analizar_web.py https://mimarca.com [https://mimarca.com/sobre-nosotros …]

Salida en marca/_analisis/web/:
    resumen.json        colores (con % de superficie), fuentes, color de botones y enlaces, logo, metadatos
    texto_<n>.md        texto visible de cada página (para sacar hechos: qué es, servicios, cifras)
    captura_<n>.png     captura de escritorio de cada página
    captura_movil.png   captura móvil de la primera página
    logo.<ext>          el logo, si se ha podido identificar (revisar siempre a ojo)
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "marca" / "_analisis" / "web"

MEDIR = r"""
() => {
  const rgb = c => { const m = c && c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x)); if (p.length > 3 && p[3] < 0.5) return null;
    return '#' + p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase(); };
  const visible = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > 0.1; };
  const fondos = {}, textos = {}, fuentes = {};
  const area = el => { const r = el.getBoundingClientRect(); return Math.min(r.width, innerWidth) * Math.min(r.height, 4000); };
  const pageH = Math.max(document.body.scrollHeight, 1);
  for (const el of document.querySelectorAll('body, body *')) {
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    const bg = rgb(s.backgroundColor);
    if (bg) fondos[bg] = (fondos[bg] || 0) + area(el);
    const directo = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 2);
    if (directo) {
      const n = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').length;
      const c = rgb(s.color); if (c) textos[c] = (textos[c] || 0) + n;
      const f = s.fontFamily.split(',')[0].replace(/["']/g, '').trim();
      const k = f + '|' + s.fontWeight; fuentes[k] = (fuentes[k] || 0) + n;
    }
  }
  const estilo = sel => { const el = [...document.querySelectorAll(sel)].find(visible); if (!el) return null;
    const s = getComputedStyle(el); return { texto: el.innerText.trim().slice(0, 60), fuente: s.fontFamily, peso: s.fontWeight,
      tamano: s.fontSize, color: rgb(s.color), fondo: rgb(s.backgroundColor), radio: s.borderRadius }; };
  const logos = [...document.querySelectorAll('header img, header svg, nav img, nav svg, a[href="/"] img, a[href="/"] svg, img[alt*="logo" i], img[src*="logo" i], img[class*="logo" i], svg[class*="logo" i]')]
    .filter(visible).slice(0, 5).map(el => ({ tipo: el.tagName.toLowerCase(), src: el.currentSrc || el.src || null,
      svg: el.tagName.toLowerCase() === 'svg' ? el.outerHTML.slice(0, 20000) : null, alt: el.getAttribute('alt') }));
  const meta = n => (document.querySelector(`meta[name="${n}"], meta[property="${n}"]`) || {}).content || null;
  const fontLinks = [...document.querySelectorAll('link[href*="fonts.googleapis"], link[href*="use.typekit"], link[href*="fonts.bunny"]')].map(l => l.href);
  return { titulo: document.title, descripcion: meta('description'), og_imagen: meta('og:image'), tema_color: meta('theme-color'),
    fondos, textos, fuentes, h1: estilo('h1'), h2: estilo('h2'), parrafo: estilo('p'),
    boton: estilo('button, a[class*="btn" i], a[class*="button" i], [role="button"]'), enlace: estilo('main a, article a, p a'),
    logos, enlaces_fuentes: fontLinks, alto_pagina: pageH };
}
"""


def top(contador, n, total=None):
    total = total or sum(contador.values()) or 1
    return [{"valor": k, "porcentaje": round(100 * v / total, 1)} for k, v in contador.most_common(n)]


def guardar_logo(logos, base_url):
    for logo in logos:
        if logo.get("svg"):
            (SALIDA / "logo.svg").write_text(logo["svg"], encoding="utf-8")
            return "logo.svg"
        if logo.get("src") and not logo["src"].startswith("data:"):
            url = urljoin(base_url, logo["src"])
            try:
                r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
            except Exception:
                continue
            ext = Path(urlparse(url).path).suffix.lower() or ".png"
            ext = ext if ext in (".svg", ".png", ".jpg", ".jpeg", ".webp") else ".png"
            (SALIDA / f"logo{ext}").write_bytes(r.content)
            return f"logo{ext}"
    return None


def main():
    global SALIDA
    args = sys.argv[1:]
    if "--salida" in args:                      # solo para pruebas: guardar fuera de marca/
        i = args.index("--salida")
        SALIDA = Path(args[i + 1]).resolve()
        del args[i:i + 2]
    urls = [u if u.startswith("http") else "https://" + u for u in args]
    if not urls:
        sys.exit("Uso: python3 tools/analizar_web.py https://mimarca.com [más páginas…]")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Falta Playwright. Escribe /empezar en el chat para instalarlo.")
    SALIDA.mkdir(parents=True, exist_ok=True)

    fondos, textos, fuentes, paginas = Counter(), Counter(), Counter(), []
    with sync_playwright() as p:
        nav = p.chromium.launch()
        for i, url in enumerate(urls, 1):
            ctx = nav.new_context(viewport={"width": 1440, "height": 900}, locale="es-ES")
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception:
                page.wait_for_timeout(3000)      # webs que nunca llegan a "networkidle": seguimos con lo cargado
            for sel in ['button:has-text("Aceptar")', 'button:has-text("Accept")', 'button:has-text("Aceptar todo")',
                        'button:has-text("Allow all")', '#onetrust-accept-btn-handler']:
                try:
                    page.click(sel, timeout=800)   # cerrar el aviso de cookies para que no tape la captura
                    break
                except Exception:
                    pass
            page.wait_for_timeout(800)
            datos = page.evaluate(MEDIR)
            fondos.update(datos.pop("fondos"))
            textos.update(datos.pop("textos"))
            fuentes.update(datos.pop("fuentes"))
            page.screenshot(path=str(SALIDA / f"captura_{i}.png"), full_page=False)
            texto = page.inner_text("body")
            texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
            (SALIDA / f"texto_{i}.md").write_text(f"# {datos.get('titulo') or url}\n\nFuente: {url}\n\n{texto}\n", encoding="utf-8")
            datos["url"] = url
            paginas.append(datos)
            ctx.close()
        movil = nav.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True)
        page = movil.new_page()
        try:
            page.goto(urls[0], wait_until="networkidle", timeout=45000)
        except Exception:
            page.wait_for_timeout(3000)
        page.screenshot(path=str(SALIDA / "captura_movil.png"))
        nav.close()

    primera = paginas[0]
    resumen = {
        "web": urls,
        "titulo": primera.get("titulo"), "descripcion": primera.get("descripcion"),
        "color_tema": primera.get("tema_color"),
        "colores_de_fondo": top(fondos, 8),
        "colores_de_texto": top(textos, 6),
        "fuentes": [{"fuente": x["valor"].split("|")[0], "peso": x["valor"].split("|")[1], "porcentaje": x["porcentaje"]}
                    for x in top(fuentes, 8)],
        "titulo_h1": primera.get("h1"), "subtitulo_h2": primera.get("h2"), "parrafo": primera.get("parrafo"),
        "boton": primera.get("boton"), "enlace": primera.get("enlace"),
        "hojas_de_fuentes": sorted({l for pg in paginas for l in pg.get("enlaces_fuentes", [])}),
        "logo_archivo": guardar_logo(primera.get("logos", []), urls[0]),
        "og_imagen": primera.get("og_imagen"),
        "nota": "El color de acento suele ser el del botón principal. Los porcentajes son de superficie (fondos) o de "
                "cantidad de texto (texto y fuentes). Revisa el logo a ojo: puede no ser el bueno.",
    }
    (SALIDA / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    print(f"\nArchivos en {SALIDA}/")


if __name__ == "__main__":
    main()
