"""
Construye las imágenes de un post (PNG) rellenando las plantillas HTML de plantillas/ con los datos de un spec.

El agente diseñador no escribe HTML desde cero: escribe un spec.json con los textos y las fotos del post, y este
script lo valida (campos obligatorios, formatos, fotos que existen, sin [A CONFIRMAR]), genera un HTML por slide
y lo convierte en PNG con un navegador sin ventana (Playwright + Chromium).

Uso:
    python3 tools/construir_visual.py --lista                         # plantillas, formatos y campos
    python3 tools/construir_visual.py --spec posts/<slug>/visual/spec.json
    python3 tools/construir_visual.py --spec ... --solo 3             # solo la entrada 3 del spec
    python3 tools/construir_visual.py --spec ... --permitir-pendientes  # boceto con [A CONFIRMAR] en rojo

Spec (rutas de fotos relativas al propio spec.json; "@marca/..." apunta a la carpeta marca/):
    {
      "slug": "taller-masa-madre",
      "formato": "4:5",
      "slides": [
        {"plantilla": "portada", "datos": {"titulo": "Nadie te enseña a **esperar**", "foto": "../fotos/01.jpg"}},
        {"plantilla": "texto", "datos": {"numero": 1, "texto": "..."}},
        {"plantilla": "cierre", "datos": {"texto": "..."}}
      ]
    }

Salida, junto al spec:
    build/NN_<plantilla>.html   HTML de cada slide (desechable, se regenera)
    final/<slug>_NN.png         slides finales en orden de carrusel
    final/<slug>_vista.jpg      tira con todas las slides para revisarlas de un vistazo
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLAS = RAIZ / "plantillas"
MARCA = RAIZ / "marca"
FORMATOS = {"4:5": (1080, 1350), "3:4": (1080, 1440), "1:1": (1080, 1080), "9:16": (1080, 1920), "16:9": (1920, 1080)}
EXT_IMAGEN = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg")
PENDIENTE = re.compile(r"\[[^\]]*A CONFIRMAR[^\]]*\]", re.I)


def error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def cargar_plantilla(nombre):
    ruta = PLANTILLAS / f"{nombre}.html"
    if not ruta.exists():
        error(f"No existe la plantilla '{nombre}'. Mira las disponibles con --lista.")
    html = ruta.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="esquema">(.*?)</script>', html, re.S)
    return html, (json.loads(m.group(1)) if m else {})


def listar():
    for ruta in sorted(PLANTILLAS.glob("[!_]*.html")):
        _, e = cargar_plantilla(ruta.stem)
        print(f"\n{ruta.stem}  ·  formatos {e.get('formatos')}\n   {e.get('descripcion', '')}")
        for k, v in e.get("obligatorios", {}).items():
            print(f"   * {k}: {v}")
        for k, v in e.get("opcionales", {}).items():
            print(f"     {k}: {v}")
    print("\n(* = obligatorio)")


def buscar_logo(nombre):
    for ext in (".svg", ".png", ".webp", ".jpg"):
        p = MARCA / "logos" / f"{nombre}{ext}"
        if p.exists():
            return p
    return None


def resolver_imagenes(valor, dir_spec, dir_build, faltan):
    """Convierte rutas de imagen (relativas al spec o @marca/) en rutas relativas al HTML generado."""
    if isinstance(valor, dict):
        return {k: resolver_imagenes(v, dir_spec, dir_build, faltan) for k, v in valor.items()}
    if isinstance(valor, list):
        return [resolver_imagenes(v, dir_spec, dir_build, faltan) for v in valor]
    if isinstance(valor, str) and valor.lower().endswith(EXT_IMAGEN) and not valor.startswith(("http://", "https://", "data:")):
        if valor.startswith("@marca/"):
            p = MARCA / valor[len("@marca/"):]
        else:
            p = Path(valor) if os.path.isabs(valor) else dir_spec / valor
        if not p.exists():
            faltan.append(valor)
            return valor
        return os.path.relpath(p.resolve(), dir_build.resolve())
    return valor


def buscar_pendientes(valor, encontrados, ruta="datos"):
    if isinstance(valor, dict):
        for k, v in valor.items():
            buscar_pendientes(v, encontrados, f"{ruta}.{k}")
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            buscar_pendientes(v, encontrados, f"{ruta}[{i}]")
    elif isinstance(valor, str) and PENDIENTE.search(valor):
        encontrados.append(ruta)


def montar_html(html, datos, ancho, alto, dir_build):
    marca_css = (PLANTILLAS / "_marca.css").read_text(encoding="utf-8")
    marca_css = marca_css.replace("@marca/", os.path.relpath(MARCA.resolve(), dir_build.resolve()) + "/")
    css = marca_css + "\n" + (PLANTILLAS / "_base.css").read_text(encoding="utf-8")
    css += f"\n:root {{ --w: {ancho}px; --h: {alto}px; }}\n"
    js = (PLANTILLAS / "_render.js").read_text(encoding="utf-8")
    datos_js = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    out = html.replace("/*CSS*/", css).replace("/*JS*/", js).replace("/*DATOS*/{}", datos_js)
    for marca in ("/*CSS*/", "/*JS*/", "/*DATOS*/"):
        if marca in out:
            error(f"La plantilla no tiene el marcador {marca} donde se espera")
    return out


def renderizar(paginas, transparente=False):
    """paginas: lista de (html_path, png_path, ancho, alto). Un solo navegador para todas."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        error("Falta Playwright. Escribe /empezar en el chat para instalarlo (o: pip install -r tools/requirements.txt).")
    with sync_playwright() as p:
        try:
            nav = p.chromium.launch(args=["--disable-dev-shm-usage"])
        except Exception as exc:
            if "Executable doesn't exist" in str(exc):
                error("Falta el navegador Chromium. Ejecuta: python3 -m playwright install chromium")
            error(f"No se pudo abrir Chromium: {exc}")
        for html_path, png_path, ancho, alto in paginas:
            ctx = nav.new_context(viewport={"width": ancho, "height": alto})
            page = ctx.new_page()
            page.goto(Path(html_path).resolve().as_uri())
            try:
                page.wait_for_selector("body.listo", timeout=30000)
            except Exception:
                error(f"{html_path}: la plantilla no terminó de cargar (¿fuente o imagen que no carga? ¿hay conexión?)")
            page.wait_for_timeout(300)
            page.screenshot(path=str(png_path), omit_background=transparente)
            ctx.close()
        nav.close()


def vista_previa(pngs, destino, alto=500, hueco=12):
    from PIL import Image
    piezas = [Image.open(p).convert("RGB") for p in pngs]
    anchos = [int(t.width * alto / t.height) for t in piezas]
    tira = Image.new("RGB", (sum(anchos) + hueco * (len(piezas) - 1), alto), "white")
    x = 0
    for t, w in zip(piezas, anchos):
        tira.paste(t.resize((w, alto)), (x, 0))
        x += w + hueco
    tira.save(destino, quality=85)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec")
    ap.add_argument("--lista", action="store_true")
    ap.add_argument("--solo", type=int, help="número de entrada del spec (1 = la primera)")
    ap.add_argument("--permitir-pendientes", action="store_true")
    a = ap.parse_args()

    if a.lista:
        listar()
        return
    if not a.spec:
        error("Falta --spec (o usa --lista)")

    ruta_spec = Path(a.spec)
    spec = json.loads(ruta_spec.read_text(encoding="utf-8"))
    dir_spec = ruta_spec.parent
    dir_build, dir_final = dir_spec / "build", dir_spec / "final"
    dir_build.mkdir(exist_ok=True)
    dir_final.mkdir(exist_ok=True)
    slug = spec.get("slug") or dir_spec.parent.name
    formato_def = spec.get("formato", "4:5")
    logo, logo_claro = buscar_logo("logo"), buscar_logo("logo_claro")

    problemas, trabajos = [], []
    for i, entrada in enumerate(spec.get("slides", []), 1):
        nombre = entrada.get("plantilla")
        html, esquema = cargar_plantilla(nombre)
        fmt = entrada.get("formato", formato_def)
        if fmt not in FORMATOS:
            problemas.append(f"#{i} {nombre}: formato '{fmt}' desconocido ({', '.join(FORMATOS)})")
            continue
        if esquema.get("formatos") and fmt not in esquema["formatos"]:
            problemas.append(f"#{i} {nombre}: la plantilla no está pensada para {fmt} (admite {esquema['formatos']})")
        datos = entrada.get("datos", {})
        for campo in esquema.get("obligatorios", {}):
            if datos.get(campo) in (None, "", []):
                problemas.append(f"#{i} {nombre}: falta el campo obligatorio '{campo}'")
        pend = []
        buscar_pendientes(datos, pend)
        if pend and not a.permitir_pendientes:
            problemas.append(f"#{i} {nombre}: hay [A CONFIRMAR] en {', '.join(pend)}")
        faltan = []
        datos = resolver_imagenes(datos, dir_spec, dir_build, faltan)
        for f in faltan:
            problemas.append(f"#{i} {nombre}: no existe la imagen {f}")
        if logo:
            datos["_logo"] = os.path.relpath(logo.resolve(), dir_build.resolve())
            datos["_logo_claro"] = os.path.relpath((logo_claro or logo).resolve(), dir_build.resolve())
        trabajos.append((i, nombre, html, datos, fmt, bool(entrada.get("transparente"))))

    if problemas:
        error("el spec no está listo:\n  - " + "\n  - ".join(problemas))

    paginas, transparente = [], False
    for i, nombre, html, datos, fmt, transp in trabajos:
        if a.solo and a.solo != i:
            continue
        ancho, alto = FORMATOS[fmt]
        html_path = dir_build / f"{i:02d}_{nombre}.html"
        html_path.write_text(montar_html(html, datos, ancho, alto, dir_build), encoding="utf-8")
        paginas.append((html_path, dir_final / f"{slug}_{i:02d}.png", ancho, alto))
        transparente = transparente or transp
    renderizar(paginas, transparente)
    for _, png, _, _ in paginas:
        print(f"PNG    {png}")

    todas = sorted(dir_final.glob(f"{slug}_[0-9][0-9].png"))[: len(trabajos)]
    if todas:
        destino = dir_final / f"{slug}_vista.jpg"
        vista_previa(todas, destino)
        print(f"VISTA  {destino}")


if __name__ == "__main__":
    main()
