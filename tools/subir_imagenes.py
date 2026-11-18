"""
Sube las imágenes finales de un post y devuelve una URL pública (https) por archivo, en el mismo orden.
Los programadores (Metricool, Hootsuite, Zernio, Buffer, Postiz) descargan las imágenes desde esas URLs.

Proveedor: el que diga config/ajustes.yaml → imagenes.proveedor
    cloudinary  .env: CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
    r2          .env: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_PUBLIC_URL
    imagekit    .env: IMAGEKIT_PRIVATE_KEY, IMAGEKIT_URL_ENDPOINT

Los PNG se convierten a JPEG (calidad 90) antes de subir: pesan unas 5 veces menos e Instagram solo publica JPEG.
Los vídeos (.mp4, .mov) se suben tal cual.

OJO: las URLs son públicas desde el momento de la subida, aunque el post aún no se haya publicado.

Uso:
    python3 tools/subir_imagenes.py --slug <slug> posts/<slug>/visual/final/<slug>_0*.png [--prueba] [--json salida.json]
"""

import argparse
import base64
import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
VIDEO = {".mp4": "video/mp4", ".mov": "video/quicktime"}
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}


def ajustes():
    ruta = RAIZ / "config" / "ajustes.yaml"
    return (yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}) if ruta.exists() else {}


def falta(*variables):
    sys.exit(f"Faltan en .env: {', '.join(variables)}. Escribe /empezar en el chat y Claude te guía para conseguirlas.")


def preparar(ruta):
    """(nombre, bytes, mime) listos para subir; PNG → JPEG q90 en memoria."""
    ext = ruta.suffix.lower()
    if ext == ".png":
        from PIL import Image
        buf = io.BytesIO()
        Image.open(ruta).convert("RGB").save(buf, "JPEG", quality=90, optimize=True, progressive=True)
        return ruta.stem + ".jpg", buf.getvalue(), "image/jpeg"
    if ext in VIDEO:
        return ruta.name, ruta.read_bytes(), VIDEO[ext]
    return ruta.name, ruta.read_bytes(), MIME.get(ext, "application/octet-stream")


# ---------- Cloudinary ----------
def cloudinary(ruta, carpeta):
    url = os.environ.get("CLOUDINARY_URL", "").strip()
    if not url:
        falta("CLOUDINARY_URL")
    u = urlparse(url)
    if u.scheme != "cloudinary" or not (u.username and u.password and u.hostname):
        sys.exit("CLOUDINARY_URL mal escrita: debe ser cloudinary://<api_key>:<api_secret>@<cloud_name> (sin los < >)")
    params = {"public_id": f"{carpeta}/{ruta.stem}", "overwrite": "false", "timestamp": str(int(time.time()))}
    firma = "&".join(f"{k}={params[k]}" for k in sorted(params)) + u.password
    params["signature"] = hashlib.sha1(firma.encode()).hexdigest()
    params["api_key"] = u.username
    nombre, datos, mime = preparar(ruta)
    tipo = "video" if ruta.suffix.lower() in VIDEO else "image"
    r = requests.post(f"https://api.cloudinary.com/v1_1/{u.hostname}/{tipo}/upload",
                      data=params, files={"file": (nombre, datos, mime)}, timeout=300)
    if r.status_code != 200:
        sys.exit(f"Cloudinary rechazó {ruta.name}: {r.status_code} {r.text[:300]}")
    d = r.json()
    return d["secure_url"], bool(d.get("existing"))


# ---------- Cloudflare R2 ----------
def r2(ruta, carpeta):
    nombres = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_PUBLIC_URL"]
    v = {n: os.environ.get(n, "").strip() for n in nombres}
    if not all(v.values()):
        falta(*[n for n in nombres if not v[n]])
    try:
        import boto3
    except ImportError:
        sys.exit("Falta boto3 para R2: pip install boto3")
    s3 = boto3.client("s3", endpoint_url=f"https://{v['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                      aws_access_key_id=v["R2_ACCESS_KEY_ID"], aws_secret_access_key=v["R2_SECRET_ACCESS_KEY"],
                      region_name="auto")
    nombre, datos, mime = preparar(ruta)
    clave = f"{carpeta}/{nombre}"
    try:
        s3.head_object(Bucket=v["R2_BUCKET"], Key=clave)
        existe = True                       # no se sobrescribe: mismo nombre = misma imagen
    except Exception:
        s3.upload_fileobj(io.BytesIO(datos), v["R2_BUCKET"], clave, ExtraArgs={"ContentType": mime})
        existe = False
    return f"{v['R2_PUBLIC_URL'].rstrip('/')}/{clave}", existe


# ---------- ImageKit ----------
def imagekit(ruta, carpeta):
    clave = os.environ.get("IMAGEKIT_PRIVATE_KEY", "").strip()
    if not clave:
        falta("IMAGEKIT_PRIVATE_KEY")
    auth = base64.b64encode(f"{clave}:".encode()).decode()     # clave privada como usuario, contraseña vacía
    nombre, datos, mime = preparar(ruta)
    r = requests.post("https://upload.imagekit.io/api/v1/files/upload",
                      headers={"Authorization": f"Basic {auth}"},
                      files={"file": (nombre, datos, mime)},
                      data={"fileName": nombre, "folder": f"/{carpeta}", "useUniqueFileName": "false",
                            "overwriteFile": "false"}, timeout=300)
    if r.status_code != 200:
        sys.exit(f"ImageKit rechazó {ruta.name}: {r.status_code} {r.text[:300]}")
    return r.json()["url"], False


PROVEEDORES = {"cloudinary": cloudinary, "r2": r2, "imagekit": imagekit}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archivos", nargs="+", type=Path, help="imágenes en el orden del carrusel")
    ap.add_argument("--slug", required=True, help="nombre corto del post (carpeta donde se guardan)")
    ap.add_argument("--prueba", action="store_true", help="solo enseña lo que subiría")
    ap.add_argument("--json", type=Path, help="guarda las URLs en este archivo")
    a = ap.parse_args()

    cfg = ajustes().get("imagenes", {}) or {}
    proveedor = (cfg.get("proveedor") or "").strip()
    if proveedor not in PROVEEDORES:
        sys.exit("Falta elegir dónde se suben las imágenes (config/ajustes.yaml → imagenes.proveedor: "
                 "cloudinary | r2 | imagekit). Escribe /empezar en el chat.")
    carpeta = f"{cfg.get('carpeta') or 'redes'}/{a.slug}"

    faltan = [f for f in a.archivos if not f.is_file()]
    if faltan:
        sys.exit("No existen: " + ", ".join(map(str, faltan)))
    if a.prueba:
        for f in a.archivos:
            print(f"[prueba] {f} → {proveedor}:{carpeta}/{f.stem}" + (" (PNG → JPEG)" if f.suffix.lower() == ".png" else ""))
        return

    urls = []
    for f in a.archivos:
        url, existia = PROVEEDORES[proveedor](f, carpeta)
        print(f"{'= ya estaba' if existia else '+ subida  '}  {url}")
        urls.append({"archivo": str(f), "url": url})
    if urls:
        print("\nSi cambias una imagen ya subida, guárdala con otro nombre (p. ej. _v2): con el mismo nombre se devuelve la antigua.")
    if a.json:
        a.json.write_text(json.dumps(urls, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON  {a.json}")


if __name__ == "__main__":
    main()
