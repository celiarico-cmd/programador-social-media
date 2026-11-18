"""
Crea la entrada de un post en tu calendario de contenidos: Notion, Airtable o Google Sheets
(config/ajustes.yaml → calendario.herramienta). Trello, Asana, ClickUp y monday se usan por MCP desde el chat:
ver workflows/calendario.md.

Qué columna es cada cosa (título, fecha, redes, estado, enlace, copy) se dice una vez en
config/ajustes.yaml → calendario.columnas. Para ver las columnas de tu calendario:
    python3 tools/calendario.py --ver

Crear la entrada (sin --crear solo enseña lo que haría):
    python3 tools/calendario.py --titulo "Taller de masa madre" --fecha "2026-12-01 10:00" \
        --redes linkedin instagram --copy posts/<slug>/copy_final.md --enlace https://... \
        --imagenes https://.../01.jpg https://.../02.jpg --crear

No duplica: si ya hay una entrada con el mismo título y la misma fecha, avisa y no crea otra.
Nunca modifica entradas existentes.

Claves en .env según la herramienta:
    notion    NOTION_TOKEN
    airtable  AIRTABLE_TOKEN
    sheets    GOOGLE_SERVICE_ACCOUNT_FILE (ruta al JSON de la cuenta de servicio; pip install google-auth)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

import requests
import yaml
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


def salir(msg):
    sys.exit(f"Error: {msg}")


def ajustes():
    cfg = yaml.safe_load((RAIZ / "config" / "ajustes.yaml").read_text(encoding="utf-8")) or {}
    return cfg.get("calendario") or {}, (cfg.get("marca") or {}).get("zona_horaria") or "Europe/Madrid"


def env(var, herramienta):
    v = os.environ.get(var, "").strip()
    if not v:
        salir(f"Falta {var} en .env (ver workflows/calendario.md → {herramienta})")
    return v


# ============================== Notion ==============================
class Notion:
    API, VERSION = "https://api.notion.com/v1", "2022-06-28"

    def __init__(self, cfg, zona):
        self.base = (cfg.get("notion") or {}).get("base_id") or salir("Falta calendario.notion.base_id en ajustes.yaml")
        self.h = {"Authorization": f"Bearer {env('NOTION_TOKEN', 'notion')}", "Notion-Version": self.VERSION,
                  "Content-Type": "application/json"}
        self.zona = zona

    def req(self, metodo, ruta, **kw):
        r = requests.request(metodo, self.API + ruta, headers=self.h, timeout=60, **kw)
        if r.status_code == 404:
            salir("Notion no encuentra la base: revisa el id y compártela con tu integración (… → Conexiones)")
        if r.status_code >= 400:
            salir(f"Notion respondió {r.status_code}: {r.text[:400]}")
        return r.json()

    def columnas(self):
        props = self.req("GET", f"/databases/{self.base}")["properties"]
        out = {}
        for n, p in props.items():
            ops = [o["name"] for o in p.get(p["type"], {}).get("options", [])] if p["type"] in ("select", "multi_select", "status") else []
            out[n] = (p["type"], ops)
        return out

    def valor(self, tipo, v):
        if tipo == "title":
            return {"title": [{"text": {"content": str(v)[:2000]}}]}
        if tipo == "rich_text":
            return {"rich_text": [{"text": {"content": str(v)[:2000]}}]}
        if tipo == "date":
            f = str(v).replace(" ", "T")
            return {"date": {"start": f, "time_zone": self.zona} if "T" in f else {"start": f}}
        if tipo in ("select", "status"):
            return {tipo: {"name": str(v)}}
        if tipo == "multi_select":
            return {"multi_select": [{"name": str(x)} for x in (v if isinstance(v, list) else [v])]}
        if tipo == "url":
            return {"url": str(v)}
        if tipo == "files":
            return {"files": [{"name": u.rsplit("/", 1)[-1][:100], "type": "external", "external": {"url": u}} for u in v]}
        salir(f"Tipo de columna de Notion '{tipo}' no soportado")

    def existe(self, col_titulo, titulo, col_fecha, dia):
        f = {"and": [{"property": col_titulo, "title": {"equals": titulo}}, {"property": col_fecha, "date": {"equals": dia}}]}
        return bool(self.req("POST", f"/databases/{self.base}/query", json={"filter": f, "page_size": 1})["results"])

    def crear(self, datos, tipos, copy, imagenes):
        props = {col: self.valor(tipos[col][0], v) for col, v in datos.items()}
        hijos = [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": p[:2000]}}]}}
                 for p in copy.split("\n\n") if p.strip()]
        hijos += [{"object": "block", "type": "image", "image": {"type": "external", "external": {"url": u}}} for u in imagenes]
        return self.req("POST", "/pages", json={"parent": {"database_id": self.base}, "properties": props,
                                                "children": hijos[:100]}).get("url")


# ============================== Airtable ==============================
class Airtable:
    API = "https://api.airtable.com/v0"

    def __init__(self, cfg, zona):
        a = cfg.get("airtable") or {}
        self.base, self.tabla = a.get("base_id"), a.get("tabla")
        if not (self.base and self.tabla):
            salir("Faltan calendario.airtable.base_id y tabla en ajustes.yaml")
        self.h = {"Authorization": f"Bearer {env('AIRTABLE_TOKEN', 'airtable')}", "Content-Type": "application/json"}
        self.zona = zona

    def req(self, metodo, url, **kw):
        r = requests.request(metodo, url, headers=self.h, timeout=60, **kw)
        if r.status_code >= 400:
            salir(f"Airtable respondió {r.status_code}: {r.text[:400]}")
        return r.json()

    def columnas(self):
        tablas = self.req("GET", f"{self.API}/meta/bases/{self.base}/tables")["tables"]
        t = next((t for t in tablas if self.tabla in (t["name"], t["id"])), None) or salir(f"No existe la tabla '{self.tabla}'")
        return {f["name"]: (f["type"], [c["name"] for c in (f.get("options") or {}).get("choices", [])]) for f in t["fields"]}

    def valor(self, tipo, v):
        if tipo == "multipleSelects":
            return v if isinstance(v, list) else [v]
        if tipo == "multipleAttachments":
            return [{"url": u} for u in v]
        if tipo == "dateTime":
            return str(v).replace(" ", "T") + (":00" if len(str(v)) == 16 else "")
        return v if not isinstance(v, list) else ", ".join(v)

    def existe(self, col_titulo, titulo, col_fecha, dia):
        t = titulo.replace("'", "\\'")
        formula = f"AND({{{col_titulo}}}='{t}', DATETIME_FORMAT({{{col_fecha}}}, 'YYYY-MM-DD')='{dia}')"
        d = self.req("GET", f"{self.API}/{self.base}/{quote(self.tabla)}", params={"filterByFormula": formula, "maxRecords": 1})
        return bool(d.get("records"))

    def crear(self, datos, tipos, copy, imagenes):
        campos = {col: self.valor(tipos[col][0], v) for col, v in datos.items()}
        d = self.req("POST", f"{self.API}/{self.base}/{quote(self.tabla)}", json={"fields": campos, "typecast": True})
        return f"https://airtable.com/{self.base}/{d.get('id')}"


# ============================== Google Sheets ==============================
class Sheets:
    API = "https://sheets.googleapis.com/v4/spreadsheets"

    def __init__(self, cfg, zona):
        s = cfg.get("sheets") or {}
        self.hoja, self.pestana = s.get("hoja_id"), s.get("pestana") or "Calendario"
        if not self.hoja:
            salir("Falta calendario.sheets.hoja_id en ajustes.yaml")
        ruta = env("GOOGLE_SERVICE_ACCOUNT_FILE", "sheets")
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account
        except ImportError:
            salir("Falta google-auth: .venv/bin/python3 -m pip install google-auth")
        cred = service_account.Credentials.from_service_account_file(
            ruta, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        cred.refresh(Request())
        self.h = {"Authorization": f"Bearer {cred.token}"}

    def req(self, metodo, ruta, **kw):
        r = requests.request(metodo, self.API + ruta, headers=self.h, timeout=60, **kw)
        if r.status_code == 403:
            salir("Google no deja abrir la hoja: compártela (Editor) con el correo de la cuenta de servicio")
        if r.status_code >= 400:
            salir(f"Google Sheets respondió {r.status_code}: {r.text[:400]}")
        return r.json()

    def filas(self):
        return self.req("GET", f"/{self.hoja}/values/{quote(self.pestana)}").get("values", [])

    def columnas(self):
        cab = (self.filas() or [[]])[0]
        return {c: ("texto", []) for c in cab}

    def existe(self, col_titulo, titulo, col_fecha, dia):
        f = self.filas()
        if not f:
            return False
        i, j = f[0].index(col_titulo), f[0].index(col_fecha)
        return any(len(r) > max(i, j) and r[i] == titulo and r[j].startswith(dia) for r in f[1:])

    def crear(self, datos, tipos, copy, imagenes):
        cab = self.filas()[0]
        fila = [(", ".join(datos[c]) if isinstance(datos.get(c), list) else datos.get(c, "")) for c in cab]
        self.req("POST", f"/{self.hoja}/values/{quote(self.pestana)}:append",
                 params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"}, json={"values": [fila]})
        return f"https://docs.google.com/spreadsheets/d/{self.hoja}"


HERRAMIENTAS = {"notion": Notion, "airtable": Airtable, "sheets": Sheets}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ver", action="store_true", help="enseña las columnas de tu calendario")
    ap.add_argument("--titulo")
    ap.add_argument("--fecha", help="AAAA-MM-DD o 'AAAA-MM-DD HH:MM' (hora de tu zona)")
    ap.add_argument("--redes", nargs="*", default=[])
    ap.add_argument("--estado")
    ap.add_argument("--copy", type=Path, help="archivo con el copy final")
    ap.add_argument("--enlace")
    ap.add_argument("--imagenes", nargs="*", default=[], help="URLs públicas de las imágenes")
    ap.add_argument("--crear", action="store_true", help="crearla de verdad")
    a = ap.parse_args()

    cfg, zona = ajustes()
    nombre = (cfg.get("herramienta") or "").lower()
    if nombre not in HERRAMIENTAS:
        salir("calendario.herramienta debe ser notion, airtable o sheets. Las demás se usan por MCP (workflows/calendario.md).")
    h = HERRAMIENTAS[nombre](cfg, zona)
    tipos = h.columnas()
    if a.ver:
        for col, (tipo, ops) in tipos.items():
            print(f"- {col}  ({tipo})" + (f"  opciones: {', '.join(ops)}" if ops else ""))
        return
    if not (a.titulo and a.fecha):
        salir("Faltan --titulo y --fecha")

    cols = cfg.get("columnas") or {}
    copy = a.copy.read_text(encoding="utf-8") if a.copy else ""
    valores = {"titulo": a.titulo, "fecha": a.fecha, "redes": a.redes or None, "estado": a.estado or cfg.get("estado_inicial"),
               "enlace": a.enlace, "copy": copy or None, "imagenes": a.imagenes or None}
    datos = {}
    for clave, v in valores.items():
        col = cols.get(clave)
        if not v or not col:
            if clave in ("titulo", "fecha") and not col:
                salir(f"Falta calendario.columnas.{clave} en ajustes.yaml")
            continue
        if col not in tipos:
            salir(f"La columna '{col}' no existe en tu calendario. Míralas con --ver.")
        datos[col] = v

    dia = a.fecha.split(" ")[0]
    if h.existe(cols["titulo"], a.titulo, cols["fecha"], dia):
        print(f"Ya existe '{a.titulo}' el {dia}. No se crea otra ni se toca la existente.")
        return
    if not a.crear:
        print(f"[prueba] Se crearía en {nombre}:")
        print(json.dumps(datos, indent=2, ensure_ascii=False)[:3000])
        print("[prueba] Repite con --crear para crearla.")
        return
    print(f"Creada: {h.crear(datos, tipos, copy, a.imagenes)}")


if __name__ == "__main__":
    main()
