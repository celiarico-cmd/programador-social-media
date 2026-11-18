"""
Programa un post por API en Metricool, Hootsuite, Zernio, Buffer o Postiz (config/ajustes.yaml → programador,
con via: api). Si tu programador está conectado por MCP, se programa desde el chat: ver workflows/programadores/.

Sin --confirmar NO programa nada: enseña exactamente lo que enviaría. Programar solo con el OK de la persona.

Uso:
    python3 tools/programar.py --cuentas                              # cuentas conectadas en tu programador
    python3 tools/programar.py --post posts/<slug>/publicar.yaml      # ensayo: enseña lo que haría
    python3 tools/programar.py --post posts/<slug>/publicar.yaml --confirmar

publicar.yaml (lo escribe Claude con el copy y las imágenes aprobados):
    fecha: "2026-12-01 10:00"          # hora local (marca.zona_horaria)
    borrador: false                    # true = se guarda como borrador en el programador, sin fecha de publicación
    imagenes:                          # en orden de carrusel; archivos locales o URLs públicas
      - visual/final/<slug>_01.png
    redes:
      linkedin:
        texto: |
          ...
        cuenta: ""                     # solo si tienes varias cuentas de esa red (id que da --cuentas)
      instagram:
        texto: |
          ...

Crea una publicación por red (cada red con su texto). Para no programar dos veces lo mismo, guarda lo que ya se
programó en posts/<slug>/programado.json y se niega a repetirlo.
"""

import argparse
import hashlib
import io
import json
import mimetypes
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yaml
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
CLAVES = {"zernio": "ZERNIO_API_KEY", "buffer": "BUFFER_API_KEY", "postiz": "POSTIZ_API_KEY",
          "metricool": "METRICOOL_USER_TOKEN"}
# Nombre de cada red en este repo → nombre en cada programador
REDES = {
    "metricool": {"linkedin": "linkedin", "instagram": "instagram", "facebook": "facebook", "x": "twitter",
                  "tiktok": "tiktok", "threads": "threads", "bluesky": "bluesky", "pinterest": "pinterest", "youtube": "youtube"},
    "hootsuite": {"linkedin": "linkedin", "instagram": "instagram", "facebook": "facebook", "x": "twitter",
                  "threads": "threads", "pinterest": "pinterest"},
    "zernio": {"linkedin": "linkedin", "instagram": "instagram", "facebook": "facebook", "x": "twitter",
               "tiktok": "tiktok", "threads": "threads", "bluesky": "bluesky", "pinterest": "pinterest", "youtube": "youtube"},
    "buffer": {"linkedin": "linkedin", "instagram": "instagram", "facebook": "facebook", "x": "twitter",
               "tiktok": "tiktok", "threads": "threads", "bluesky": "bluesky", "pinterest": "pinterest", "youtube": "youtube"},
    "postiz": {"linkedin": "linkedin", "instagram": "instagram", "facebook": "facebook", "x": "x",
               "tiktok": "tiktok", "threads": "threads", "bluesky": "bluesky", "pinterest": "pinterest", "youtube": "youtube"},
}


def salir(msg):
    sys.exit(f"Error: {msg}")


def ajustes():
    return yaml.safe_load((RAIZ / "config" / "ajustes.yaml").read_text(encoding="utf-8")) or {}


def clave(nombre, variable=None):
    variable = variable or CLAVES[nombre]
    k = os.environ.get(variable, "").strip()
    if not k:
        salir(f"Falta {variable} en .env. Ver workflows/programadores/{nombre}.md")
    return k


def jpeg_si_png(ruta):
    """PNG → JPEG q90 (más ligero y lo que acepta Instagram)."""
    if ruta.suffix.lower() != ".png":
        return ruta.name, ruta.read_bytes(), mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
    from PIL import Image
    buf = io.BytesIO()
    Image.open(ruta).convert("RGB").save(buf, "JPEG", quality=90, optimize=True)
    return ruta.stem + ".jpg", buf.getvalue(), "image/jpeg"


# ============================== Zernio ==============================
class Zernio:
    BASE = "https://zernio.com/api/v1"

    def __init__(self, cfg):
        self.h = {"Authorization": f"Bearer {clave('zernio')}"}

    def req(self, metodo, ruta, **kw):
        r = requests.request(metodo, self.BASE + ruta, headers={**self.h, **kw.pop("headers", {})}, timeout=120, **kw)
        if r.status_code >= 400:
            salir(f"Zernio respondió {r.status_code}: {r.text[:400]}")
        return r.json() if r.content else {}

    def cuentas(self):
        d = self.req("GET", "/accounts")
        lista = d.get("accounts", d if isinstance(d, list) else [])
        return [{"id": a.get("_id") or a.get("id"), "red": a.get("platform"),
                 "nombre": a.get("displayName") or a.get("username") or a.get("name")} for a in lista]

    def subir(self, ruta):
        nombre, datos, mime = jpeg_si_png(ruta)
        p = self.req("POST", "/media/presign", json={"filename": nombre, "contentType": mime})
        r = requests.put(p["uploadUrl"], data=datos, headers={"Content-Type": mime}, timeout=300)
        if r.status_code >= 400:
            salir(f"Zernio no aceptó la subida de {ruta.name}: {r.status_code}")
        return p["publicUrl"]

    def programar(self, cuenta, red, texto, media, fecha_local, zona, borrador, clave_unica):
        cuerpo = {"content": texto, "platforms": [{"platform": REDES["zernio"][red], "accountId": cuenta}],
                  "mediaItems": [{"url": u, "type": "video" if u.lower().endswith((".mp4", ".mov")) else "image"} for u in media]}
        if borrador:
            cuerpo["isDraft"] = True
        else:
            cuerpo.update({"scheduledFor": fecha_local.strftime("%Y-%m-%dT%H:%M:%S"), "timezone": zona})
        return cuerpo, lambda: self.req("POST", "/posts", json=cuerpo, headers={"Idempotency-Key": clave_unica})


# ============================== Buffer ==============================
class Buffer:
    URL = "https://api.buffer.com"

    def __init__(self, cfg):
        self.h = {"Authorization": f"Bearer {clave('buffer')}", "Content-Type": "application/json"}

    def gql(self, query, variables=None):
        r = requests.post(self.URL, headers=self.h, json={"query": query, "variables": variables or {}}, timeout=120)
        d = r.json() if r.content else {}
        if r.status_code >= 400 or d.get("errors"):
            salir(f"Buffer respondió {r.status_code}: {json.dumps(d.get('errors') or d)[:400]}")
        return d["data"]

    def cuentas(self):
        orgs = self.gql("query { account { organizations { id name } } }")["account"]["organizations"]
        out = []
        for o in orgs:
            q = "query($o: OrganizationId!) { channels(input: {organizationId: $o}) { id name displayName service } }"
            for c in self.gql(q, {"o": o["id"]})["channels"]:
                out.append({"id": c["id"], "red": c["service"], "nombre": c.get("displayName") or c.get("name")})
        return out

    def subir(self, ruta):
        salir("Buffer no recibe archivos: sube antes las imágenes con tools/subir_imagenes.py y pon sus URLs en publicar.yaml")

    def programar(self, cuenta, red, texto, media, fecha_local, zona, borrador, clave_unica):
        entrada = {"text": texto, "channelId": cuenta, "schedulingType": "automatic",
                   "assets": [{"image": {"url": u}} for u in media]}
        if borrador:
            entrada["saveToDraft"] = True
        else:
            entrada.update({"mode": "customScheduled",
                            "dueAt": fecha_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")})
        q = ("mutation($i: CreatePostInput!) { createPost(input: $i) { "
             "... on PostActionSuccess { post { id dueAt } } ... on MutationError { message } } }")

        def enviar():
            r = self.gql(q, {"i": entrada})["createPost"]
            if r.get("message"):
                salir(f"Buffer no creó el post: {r['message']}")
            return r
        return entrada, enviar


# ============================== Postiz ==============================
class Postiz:
    def __init__(self, cfg):
        propia = ((cfg.get("programador") or {}).get("postiz_url") or "").rstrip("/")
        self.base = f"{propia}/api/public/v1" if propia else "https://api.postiz.com/public/v1"
        self.h = {"Authorization": clave("postiz")}          # Postiz: la clave tal cual, sin "Bearer"

    def req(self, metodo, ruta, **kw):
        r = requests.request(metodo, self.base + ruta, headers=self.h, timeout=120, **kw)
        if r.status_code >= 400:
            salir(f"Postiz respondió {r.status_code}: {r.text[:400]}")
        return r.json() if r.content else {}

    def cuentas(self):
        return [{"id": i["id"], "red": i.get("identifier") or i.get("providerIdentifier"), "nombre": i.get("name")}
                for i in self.req("GET", "/integrations")]

    def subir(self, ruta):
        nombre, datos, mime = jpeg_si_png(ruta)
        d = self.req("POST", "/upload", files={"file": (nombre, datos, mime)})
        return {"id": d["id"], "path": d["path"]}

    def programar(self, cuenta, red, texto, media, fecha_local, zona, borrador, clave_unica):
        tipo_red = next((c["red"] for c in self.cuentas() if c["id"] == cuenta), red)
        ajustes_red = {"__type": tipo_red}
        if red == "instagram":
            ajustes_red["post_type"] = "post"
        if any(not isinstance(m, dict) for m in media):
            salir("Postiz necesita las imágenes como archivos locales en publicar.yaml (las sube él), no URLs")
        imagenes = media
        cuerpo = {"type": "draft" if borrador else "schedule",
                  "date": fecha_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                  "shortLink": False, "tags": [],
                  "posts": [{"integration": {"id": cuenta}, "value": [{"content": texto, "image": imagenes}],
                             "settings": ajustes_red}]}
        return cuerpo, lambda: self.req("POST", "/posts", json=cuerpo)



# ============================== Metricool ==============================
class Metricool:
    """API REST de Metricool: solo en los planes Advanced y Custom (por MCP funciona en cualquier plan)."""
    BASE = "https://app.metricool.com/api"
    CAMPOS = {"linkedin": "linkedinCompany", "instagram": "instagram", "facebook": "facebook", "twitter": "twitter",
              "tiktok": "tiktok", "threads": "threads", "bluesky": "bluesky", "pinterest": "pinterest", "youtube": "youtube"}

    def __init__(self, cfg):
        self.h = {"X-Mc-Auth": clave("metricool")}
        self.user = clave("metricool", "METRICOOL_USER_ID")
        self.blog = str((cfg.get("programador") or {}).get("metricool_brand_id") or "").strip()
        if not self.blog:
            salir("Falta programador.metricool_brand_id en config/ajustes.yaml (es el blogId de la URL de Metricool)")
        self.zona = (cfg.get("marca") or {}).get("zona_horaria") or "Europe/Madrid"

    def req(self, metodo, ruta, params=None, **kw):
        params = {"userId": self.user, "blogId": self.blog, **(params or {})}
        r = requests.request(metodo, self.BASE + ruta, headers=self.h, params=params, timeout=120, **kw)
        if r.status_code in (401, 403):
            salir("Metricool rechaza la clave. ¿Es correcta? ¿Tu plan incluye API (Advanced o Custom)?")
        if r.status_code >= 400:
            salir(f"Metricool respondió {r.status_code}: {r.text[:400]}")
        return r.json() if r.content and "json" in r.headers.get("Content-Type", "") else r.text

    def cuentas(self):
        marca = next((b for b in self.req("GET", "/admin/simpleProfiles") if str(b.get("id")) == self.blog), None)
        if not marca:
            salir(f"La marca {self.blog} no aparece en tu cuenta de Metricool")
        return [{"id": red, "red": red, "nombre": f"{marca.get('label')} · {marca.get(campo)}"}
                for red, campo in self.CAMPOS.items() if marca.get(campo)]

    def subir(self, ruta):
        salir("Metricool necesita las imágenes en una URL pública: súbelas antes con tools/subir_imagenes.py")

    def programar(self, cuenta, red, texto, media, fecha_local, zona, borrador, clave_unica):
        urls = []
        for u in media:   # Metricool copia cada imagen a su almacenamiento; si no, el post sale sin imagen
            r = self.req("GET", "/actions/normalize/image/url", params={"url": u})
            urls.append(r.get("data", r) if isinstance(r, dict) else str(r).strip().strip('"'))
        cuerpo = {"publicationDate": {"dateTime": fecha_local.strftime("%Y-%m-%dT%H:%M:%S"), "timezone": zona},
                  "text": texto, "providers": [{"network": REDES["metricool"][red]}], "media": urls,
                  "draft": borrador, "autoPublish": True}
        if red == "linkedin":
            cuerpo["linkedinData"] = {"type": "post", "publishImagesAsPDF": False}
        if red == "instagram":
            cuerpo["instagramData"] = {"type": "POST"}
        return cuerpo, lambda: self.req("POST", "/v2/scheduler/posts", json=cuerpo)


# ============================== Hootsuite ==============================
class Hootsuite:
    """API REST de Hootsuite. Hace falta una app aprobada en developer.hootsuite.com y tools/hootsuite_login.py."""
    BASE = "https://platform.hootsuite.com"
    TOKEN = RAIZ / ".hootsuite_token.json"

    def __init__(self, cfg):
        self.id_app = clave("hootsuite", "HOOTSUITE_CLIENT_ID")
        self.secreto = clave("hootsuite", "HOOTSUITE_CLIENT_SECRET")
        if not self.TOKEN.exists():
            salir("Falta iniciar sesión en Hootsuite: .venv/bin/python3 tools/hootsuite_login.py")
        self.tok = json.loads(self.TOKEN.read_text(encoding="utf-8"))
        if self.tok.get("caduca", 0) < datetime.now().timestamp() + 60:
            self.renovar()

    def renovar(self):
        r = requests.post(self.BASE + "/oauth2/token", auth=(self.id_app, self.secreto), timeout=60,
                          data={"grant_type": "refresh_token", "refresh_token": self.tok["refresh_token"]})
        if r.status_code >= 400:
            salir("La sesión de Hootsuite ha caducado: .venv/bin/python3 tools/hootsuite_login.py")
        d = r.json()
        self.tok = {"access_token": d["access_token"], "refresh_token": d.get("refresh_token", self.tok["refresh_token"]),
                    "caduca": datetime.now().timestamp() + int(d.get("expires_in", 3600))}
        self.TOKEN.write_text(json.dumps(self.tok), encoding="utf-8")

    def req(self, metodo, ruta, **kw):
        r = requests.request(metodo, self.BASE + ruta, timeout=120,
                             headers={"Authorization": f"Bearer {self.tok['access_token']}"}, **kw)
        if r.status_code >= 400:
            salir(f"Hootsuite respondió {r.status_code}: {r.text[:400]}")
        return r.json() if r.content else {}

    def cuentas(self):
        return [{"id": str(c["id"]), "red": c.get("type", "").lower(), "nombre": c.get("socialNetworkUsername")}
                for c in self.req("GET", "/v1/me/socialProfiles").get("data", [])]

    def subir(self, ruta):
        import time
        nombre, datos, mime = jpeg_si_png(ruta)
        d = self.req("POST", "/v1/media", json={"sizeBytes": len(datos), "mimeType": mime})["data"]
        r = requests.put(d["uploadUrl"], data=datos, timeout=300,
                         headers={"Content-Type": mime, "Content-Length": str(len(datos))})
        if r.status_code >= 400:
            salir(f"Hootsuite no aceptó la subida de {ruta.name}: {r.status_code}")
        for _ in range(60):
            if self.req("GET", f"/v1/media/{d['id']}")["data"].get("state") == "READY":
                return d["id"]
            time.sleep(2)
        salir(f"Hootsuite no terminó de procesar {ruta.name}")

    def programar(self, cuenta, red, texto, media, fecha_local, zona, borrador, clave_unica):
        if borrador:
            salir("La API de Hootsuite no tiene borradores: todo lo que se envía se publica. Quita 'borrador: true'.")
        if any(isinstance(m, str) and m.startswith("http") for m in media):
            salir("Hootsuite necesita las imágenes como archivos locales en publicar.yaml (las sube él), no URLs")
        cuerpo = {"text": texto, "socialProfileIds": [cuenta], "emailNotification": False,
                  "scheduledSendTime": fecha_local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "media": [{"id": m} for m in media]}
        return cuerpo, lambda: self.req("POST", "/v1/messages", json=cuerpo)


PROGRAMADORES = {"metricool": Metricool, "hootsuite": Hootsuite, "zernio": Zernio, "buffer": Buffer, "postiz": Postiz}


def elegir_cuenta(cuentas, red, nombre_prog, indicada):
    if indicada:
        if not any(c["id"] == indicada for c in cuentas):
            salir(f"La cuenta '{indicada}' no está entre las conectadas. Míralas con --cuentas.")
        return indicada
    buscada = REDES[nombre_prog][red]
    candidatas = [c for c in cuentas if (c["red"] or "").lower().startswith(buscada)]
    if not candidatas:
        salir(f"No hay ninguna cuenta de {red} conectada en {nombre_prog}. Conéctala allí primero.")
    if len(candidatas) > 1:
        lista = "\n".join(f"  {c['id']}  {c['red']}  {c['nombre']}" for c in candidatas)
        salir(f"Hay varias cuentas de {red}. Pon cuál en publicar.yaml → redes.{red}.cuenta:\n{lista}")
    return candidatas[0]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cuentas", action="store_true")
    ap.add_argument("--post", type=Path)
    ap.add_argument("--confirmar", action="store_true", help="programar de verdad")
    a = ap.parse_args()

    cfg = ajustes()
    prog = (cfg.get("programador") or {})
    nombre = (prog.get("nombre") or "").lower()
    if nombre not in PROGRAMADORES or (prog.get("via") or "").lower() != "api":
        salir("Este script es para programadores conectados por API (config/ajustes.yaml → programador.via: api). "
              "Con MCP se programa desde el chat: ver workflows/programadores/.")
    p = PROGRAMADORES[nombre](cfg)

    if a.cuentas:
        for c in p.cuentas():
            print(f"{c['id']}  {c['red']:<14} {c['nombre']}")
        return
    if not a.post:
        salir("Falta --post (o usa --cuentas)")

    spec = yaml.safe_load(a.post.read_text(encoding="utf-8"))
    dir_post = a.post.parent
    zona = (cfg.get("marca") or {}).get("zona_horaria") or "Europe/Madrid"
    borrador = bool(spec.get("borrador"))
    try:
        fecha = datetime.strptime(str(spec["fecha"]), "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(zona))
    except (KeyError, ValueError):
        salir("publicar.yaml → fecha debe ser 'AAAA-MM-DD HH:MM'")
    if not borrador and fecha <= datetime.now(ZoneInfo(zona)):
        salir(f"La fecha {spec['fecha']} ya ha pasado")
    for red, d in (spec.get("redes") or {}).items():
        if red not in REDES[nombre]:
            salir(f"Red '{red}' desconocida ({', '.join(REDES[nombre])})")
        if "[A CONFIRMAR" in (d.get("texto") or "") or not (d.get("texto") or "").strip():
            salir(f"El texto de {red} está vacío o tiene [A CONFIRMAR]")

    registro_ruta = dir_post / "programado.json"
    registro = json.loads(registro_ruta.read_text(encoding="utf-8")) if registro_ruta.exists() else {}
    imagenes = []
    for ref in spec.get("imagenes") or []:
        if str(ref).startswith("http"):
            imagenes.append(str(ref))
            continue
        ruta = (dir_post / ref) if not os.path.isabs(ref) else Path(ref)
        if not ruta.exists():
            salir(f"No existe la imagen {ruta}")
        imagenes.append(ruta)

    cuentas = p.cuentas()
    plan = []
    for red, d in spec["redes"].items():
        if red in registro:
            print(f"= {red}: ya programado el {registro[red]['cuando']} (id {registro[red].get('id')}). No se repite.")
            continue
        plan.append((red, d["texto"].strip(), elegir_cuenta(cuentas, red, nombre, d.get("cuenta"))))

    if not plan:
        print("Nada que programar.")
        return
    if not a.confirmar:
        print(f"[ensayo] {nombre} · {'BORRADOR' if borrador else spec['fecha'] + ' ' + zona} · {len(imagenes)} imagen(es)")
        for red, texto, cuenta in plan:
            print(f"\n--- {red} (cuenta {cuenta}) · {len(texto)} caracteres ---\n{texto}")
        print("\n[ensayo] No se ha programado nada. Con el OK de la persona, repite con --confirmar.")
        return

    if nombre == "hootsuite" and not borrador:
        minimo = 5 if not any(str(m).lower().endswith((".mp4", ".mov")) for m in imagenes) else 15
        if (fecha - datetime.now(ZoneInfo(zona))).total_seconds() < minimo * 60:
            salir(f"Hootsuite pide programar con al menos {minimo} minutos de antelación")
    media = [m if isinstance(m, str) else p.subir(m) for m in imagenes]
    for red, texto, cuenta in plan:
        unica = hashlib.sha256(f"{dir_post.name}|{red}|{spec['fecha']}".encode()).hexdigest()[:32]
        _, enviar = p.programar(cuenta, red, texto, media, fecha, zona, borrador, unica)
        respuesta = enviar()
        ident = json.dumps(respuesta)[:200]
        for k in ("_id", "id"):
            if isinstance(respuesta, dict) and k in (respuesta.get("post") or respuesta):
                ident = (respuesta.get("post") or respuesta)[k]
        registro[red] = {"cuando": datetime.now().isoformat(timespec="seconds"), "fecha": spec["fecha"],
                         "borrador": borrador, "id": ident}
        registro_ruta.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"+ {red}: {'guardado como borrador' if borrador else 'programado para ' + spec['fecha']} (id {ident})")


if __name__ == "__main__":
    main()
