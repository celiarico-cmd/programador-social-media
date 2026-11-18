"""
Añade los UTMs a los enlaces de un post, para saber en Google Analytics (o similar) qué visitas vienen de cada post.

    utm_source   = la red (linkedin, instagram…)
    utm_medium   = config/ajustes.yaml → utm.medium (por defecto "social")
    utm_campaign = la campaña o sección del post
    utm_content  = el slug del post

Uso:
    # un enlace
    python3 tools/utm.py --red linkedin --campana lanzamiento --contenido taller-masa-madre https://mitienda.com/talleres
    # todos los enlaces de un texto (copy de un post): imprime el texto con los enlaces ya marcados
    python3 tools/utm.py --red instagram --campana lanzamiento --contenido taller-masa-madre --archivo posts/<slug>/copy.md

Respeta los parámetros que ya tenga el enlace y no duplica UTMs si ya están. Solo marca enlaces de los dominios de
config/ajustes.yaml → utm.dominios (si la lista está vacía, marca todos).
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import yaml

RAIZ = Path(__file__).resolve().parent.parent
URL = re.compile(r"https?://[^\s<>\"')\]]+")


def ajustes_utm():
    ruta = RAIZ / "config" / "ajustes.yaml"
    cfg = (yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}) if ruta.exists() else {}
    return cfg.get("utm", {}) or {}


def limpiar(valor):
    return re.sub(r"[^a-z0-9_-]+", "-", valor.strip().lower()).strip("-")


def marcar(url, red, campana, contenido, medium, dominios):
    final = ""
    while url and url[-1] in ".,;:!?":       # puntuación pegada al final de la frase
        final = url[-1] + final
        url = url[:-1]
    p = urlparse(url)
    host = p.netloc.lower().removeprefix("www.")
    if dominios and not any(host == d or host.endswith("." + d) for d in dominios):
        return url + final
    params = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.startswith("utm_")]
    params += [("utm_source", red), ("utm_medium", medium), ("utm_campaign", campana), ("utm_content", contenido)]
    return urlunparse(p._replace(query=urlencode(params))) + final


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?")
    ap.add_argument("--red", required=True, help="linkedin, instagram, facebook, x, tiktok, threads…")
    ap.add_argument("--campana", required=True, help="campaña o sección del post")
    ap.add_argument("--contenido", required=True, help="slug del post")
    ap.add_argument("--archivo", type=Path, help="texto en el que marcar todos los enlaces")
    a = ap.parse_args()

    cfg = ajustes_utm()
    medium = cfg.get("medium") or "social"
    dominios = [d.lower().removeprefix("www.") for d in (cfg.get("dominios") or [])]
    red, campana, contenido = limpiar(a.red), limpiar(a.campana), limpiar(a.contenido)

    if a.archivo:
        texto = a.archivo.read_text(encoding="utf-8")
        print(URL.sub(lambda m: marcar(m.group(0), red, campana, contenido, medium, dominios), texto))
    elif a.url:
        print(marcar(a.url, red, campana, contenido, medium, dominios))
    else:
        sys.exit("Pasa un enlace o --archivo")


if __name__ == "__main__":
    main()
