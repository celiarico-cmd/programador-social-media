"""
Figma por API: leer las capas de un diseño (para crear plantillas) y exportar frames a PNG (para programarlos).
Necesita FIGMA_TOKEN en .env: Figma → Settings → Security → Personal access tokens, con permiso "File content: read".
En el plan gratuito de Figma la API deja muy pocas llamadas al mes: en la práctica hace falta un plan de pago.

Uso:
    # Capas: qué es foto (cambia en cada post), texto, degradado, forma o vector (se repiten)
    python3 tools/figma.py capas "https://www.figma.com/design/<clave>/<nombre>?node-id=12-34"

    # Exportar uno o varios frames a PNG, en el orden dado (p. ej. las slides de un carrusel)
    python3 tools/figma.py exportar "<url del frame 1>" "<url del frame 2>" … --slug <slug> --carpeta posts/<slug>/visual/final

Con un enlace a un frame que contiene varias slides, --hijos exporta cada frame hijo en orden (izquierda → derecha,
arriba → abajo).
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
API = "https://api.figma.com/v1"


def salir(msg):
    sys.exit(f"Error: {msg}")


def cabecera():
    t = os.environ.get("FIGMA_TOKEN", "").strip()
    if not t:
        salir("Falta FIGMA_TOKEN en .env (ver workflows/disenar_figma.md)")
    return {"X-Figma-Token": t}


def pedir(ruta, **params):
    r = requests.get(API + ruta, headers=cabecera(), params=params, timeout=120)
    if r.status_code == 429:
        salir("Figma ha cortado por límite de llamadas (en el plan gratuito son muy pocas al mes)")
    if r.status_code in (403, 404):
        salir("Figma no deja ver el archivo: ¿el enlace es correcto y tu cuenta tiene acceso?")
    if r.status_code >= 400:
        salir(f"Figma respondió {r.status_code}: {r.text[:300]}")
    return r.json()


def leer_url(url):
    u = urlparse(url)
    m = re.search(r"/(?:design|file)/([A-Za-z0-9]+)(?:/branch/([A-Za-z0-9]+))?", u.path)
    if not m:
        salir(f"No parece un enlace de Figma: {url}")
    clave = m.group(2) or m.group(1)
    nodo = (parse_qs(u.query).get("node-id") or [None])[0]
    return clave, nodo.replace("-", ":") if nodo else None


def color(c, opacidad=1):
    a = round(c.get("a", 1) * opacidad, 2)
    h = "#" + "".join(f"{round(c[k] * 255):02X}" for k in "rgb")
    return h if a >= 1 else f"{h} ({int(a * 100)} %)"


def describir_relleno(f):
    t = f.get("type")
    if t == "IMAGE":
        return "foto"
    if t == "SOLID":
        return f"color {color(f['color'], f.get('opacity', 1))}"
    if t and t.startswith("GRADIENT_"):
        paradas = " → ".join(color(s["color"]) for s in f.get("gradientStops", []))
        tipo = {"GRADIENT_LINEAR": "lineal", "GRADIENT_RADIAL": "radial", "GRADIENT_ANGULAR": "angular",
                "GRADIENT_DIAMOND": "diamante"}.get(t, t)
        return f"degradado {tipo}: {paradas}"
    return t.lower() if t else "?"


def capas(nodo, origen, nivel=0, out=None):
    out = [] if out is None else out
    if nodo.get("visible") is False:
        return out
    caja = nodo.get("absoluteBoundingBox") or {}
    x = round(caja.get("x", 0) - origen[0])
    y = round(caja.get("y", 0) - origen[1])
    pos = f"[{x},{y} {round(caja.get('width', 0))}×{round(caja.get('height', 0))}]"
    rellenos = [f for f in nodo.get("fills", []) if f.get("visible", True)]
    tipo = nodo["type"]
    if tipo == "TEXT":
        st = nodo.get("style", {})
        clase = "TEXTO"
        detalle = (f"\"{nodo.get('characters', '')[:60]}\" · {st.get('fontFamily')} {st.get('fontWeight')} "
                   f"{st.get('fontSize')}px" + (f" · {describir_relleno(rellenos[0])}" if rellenos else ""))
    elif any(f.get("type") == "IMAGE" for f in rellenos):
        clase, detalle = "FOTO", "imagen (suele cambiar en cada post)"
    elif tipo in ("VECTOR", "BOOLEAN_OPERATION", "STAR", "LINE", "REGULAR_POLYGON"):
        clase, detalle = "VECTOR", "forma vectorial (logo, icono, ilustración)"
    elif any(f.get("type", "").startswith("GRADIENT_") for f in rellenos):
        clase, detalle = "DEGRADADO", "; ".join(describir_relleno(f) for f in rellenos)
    elif rellenos and tipo in ("RECTANGLE", "ELLIPSE", "FRAME", "COMPONENT", "INSTANCE"):
        clase, detalle = "FORMA" if tipo != "FRAME" else "MARCO", "; ".join(describir_relleno(f) for f in rellenos)
    else:
        clase, detalle = tipo.lower(), ""
    efectos = [e["type"].lower() for e in nodo.get("effects", []) if e.get("visible", True)]
    if efectos:
        detalle += f" · efectos: {', '.join(efectos)}"
    if nodo.get("cornerRadius"):
        detalle += f" · radio {nodo['cornerRadius']}"
    out.append(f"{'  ' * nivel}{clase:<10} {nodo.get('name', '')!r} {pos} {detalle}".rstrip())
    for hijo in nodo.get("children", []):
        capas(hijo, origen, nivel + 1, out)
    return out


def cmd_capas(url):
    clave, nodo = leer_url(url)
    if not nodo:
        salir("El enlace no apunta a un frame: en Figma, clic derecho en el frame → Copiar enlace")
    d = pedir(f"/files/{clave}/nodes", ids=nodo)["nodes"][nodo]["document"]
    caja = d.get("absoluteBoundingBox") or {}
    print(f"Frame '{d.get('name')}' · {round(caja.get('width', 0))}×{round(caja.get('height', 0))} px\n")
    print("\n".join(capas(d, (caja.get("x", 0), caja.get("y", 0)))))
    print("\nFOTO = campo variable de la plantilla · TEXTO = campo variable si cambia entre posts · "
          "DEGRADADO, FORMA, VECTOR, MARCO = parte fija del diseño")


def cmd_exportar(urls, slug, carpeta, escala, hijos):
    pedidos = []
    for url in urls:
        clave, nodo = leer_url(url)
        if not nodo:
            salir(f"El enlace no apunta a un frame: {url}")
        if hijos:
            d = pedir(f"/files/{clave}/nodes", ids=nodo, depth=1)["nodes"][nodo]["document"]
            frames = [h for h in d.get("children", []) if h["type"] in ("FRAME", "COMPONENT", "INSTANCE")]
            frames.sort(key=lambda h: (round(h["absoluteBoundingBox"]["y"] / 50), h["absoluteBoundingBox"]["x"]))
            pedidos += [(clave, h["id"]) for h in frames]
        else:
            pedidos.append((clave, nodo))
    carpeta.mkdir(parents=True, exist_ok=True)
    por_archivo = {}
    for clave, nodo in pedidos:
        por_archivo.setdefault(clave, []).append(nodo)
    urls_img = {}
    for clave, nodos in por_archivo.items():
        urls_img.update(pedir(f"/images/{clave}", ids=",".join(nodos), format="png", scale=escala)["images"])
    for i, (_, nodo) in enumerate(pedidos, 1):
        u = urls_img.get(nodo)
        if not u:
            salir(f"Figma no pudo exportar el frame {nodo}")
        destino = carpeta / f"{slug}_{i:02d}.png"
        destino.write_bytes(requests.get(u, timeout=300).content)
        print(f"PNG    {destino}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capas")
    c.add_argument("url")
    e = sub.add_parser("exportar")
    e.add_argument("urls", nargs="+")
    e.add_argument("--slug", required=True)
    e.add_argument("--carpeta", type=Path, required=True)
    e.add_argument("--escala", type=float, default=1, help="1 = tamaño real del frame (1080 px si el frame mide 1080)")
    e.add_argument("--hijos", action="store_true", help="exporta cada frame hijo del enlace, en orden")
    a = ap.parse_args()
    if a.cmd == "capas":
        cmd_capas(a.url)
    else:
        cmd_exportar(a.urls, a.slug, a.carpeta, a.escala, a.hijos)


if __name__ == "__main__":
    main()
