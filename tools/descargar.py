"""
Descarga las imágenes finales de un post desde los enlaces que dan Canva (export-design) o Figma (download_assets),
las guarda en orden de carrusel y genera la tira de vista previa, igual que si se hubieran hecho en el chat.

Uso:
    python3 tools/descargar.py --slug <slug> --carpeta posts/<slug>/visual/final <url1> <url2> …

Si un enlace es un .zip (Canva exporta así varias páginas), lo descomprime y ordena las páginas por nombre.
Los enlaces de exportación caducan (Canva: 24 h): descárgalos en cuanto se generen.
"""

import argparse
import io
import sys
import zipfile
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construir_visual import vista_previa  # noqa: E402

EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "video/mp4": ".mp4", "application/pdf": ".pdf"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--carpeta", type=Path, required=True)
    a = ap.parse_args()
    a.carpeta.mkdir(parents=True, exist_ok=True)

    piezas = []   # (bytes, extensión)
    for url in a.urls:
        r = requests.get(url, timeout=300)
        if r.status_code >= 400:
            sys.exit(f"No se pudo descargar ({r.status_code}). ¿Ha caducado el enlace? Vuelve a exportar. {url[:80]}")
        tipo = r.headers.get("Content-Type", "").split(";")[0]
        if tipo in ("application/zip", "application/x-zip-compressed") or r.content[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                for nombre in sorted(n for n in z.namelist() if not n.endswith("/")):
                    piezas.append((z.read(nombre), Path(nombre).suffix.lower() or ".png"))
        else:
            piezas.append((r.content, EXT.get(tipo, Path(url.split("?")[0]).suffix.lower() or ".png")))

    imagenes = []
    for i, (datos, ext) in enumerate(piezas, 1):
        destino = a.carpeta / f"{a.slug}_{i:02d}{ext}"
        destino.write_bytes(datos)
        print(f"{ext[1:].upper():<5}  {destino}")
        if ext in (".png", ".jpg", ".jpeg", ".webp"):
            imagenes.append(destino)
            im = Image.open(destino)
            if im.width < 1080:
                print(f"       ojo: mide {im.width}×{im.height} px; para redes conviene 1080 de ancho")
    if imagenes:
        vista = a.carpeta / f"{a.slug}_vista.jpg"
        vista_previa(imagenes, vista)
        print(f"VISTA  {vista}")


if __name__ == "__main__":
    main()
