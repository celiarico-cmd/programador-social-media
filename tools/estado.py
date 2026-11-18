"""
¿Qué falta por montar? Revisa cada pieza del sistema y dice cuál es el siguiente paso.
Solo lee; no cambia nada. Funciona aunque todavía no esté instalado nada (solo usa Python).

Uso:
    python3 tools/estado.py
"""

import importlib.util
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCA = RAIZ / "marca"
POR_API = {"zernio": ["ZERNIO_API_KEY"], "buffer": ["BUFFER_API_KEY"], "postiz": ["POSTIZ_API_KEY"],
           "metricool": ["METRICOOL_USER_TOKEN", "METRICOOL_USER_ID"],
           "hootsuite": ["HOOTSUITE_CLIENT_ID", "HOOTSUITE_CLIENT_SECRET"]}
CALENDARIO = {"notion": ["NOTION_TOKEN"], "airtable": ["AIRTABLE_TOKEN"], "sheets": ["GOOGLE_SERVICE_ACCOUNT_FILE"]}
IMAGENES = {
    "cloudinary": ["CLOUDINARY_URL"],
    "r2": ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_PUBLIC_URL"],
    "imagekit": ["IMAGEKIT_PRIVATE_KEY"],
}


def leer_env():
    env = {}
    ruta = RAIZ / ".env"
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def pendiente(ruta):
    return not ruta.exists() or "PENDIENTE" in ruta.read_text(encoding="utf-8")[:400]


def preguntas_abiertas():
    total = 0
    for ruta in (MARCA / "voz.md", MARCA / "hechos.md", MARCA / "guia_visual.md"):
        if ruta.exists():
            m = re.search(r"## Preguntas abiertas(.*?)(\n## |\Z)", ruta.read_text(encoding="utf-8"), re.S)
            if m:
                total += len(re.findall(r"^- \[ \]", m.group(1), re.M))
    return total


def main():
    pasos = []   # (hecho: bool | None, texto, siguiente_paso)

    # 1. Entorno
    venv = (RAIZ / ".venv").exists()
    faltan = [m for m in ("yaml", "dotenv", "requests", "PIL", "playwright") if importlib.util.find_spec(m) is None]
    chromium = False
    if "playwright" not in faltan:
        try:   # la versión exacta de Chromium que pide esta versión de Playwright
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                chromium = Path(p.chromium.executable_path).exists()
        except Exception:
            chromium = False
    entorno = venv and not faltan and chromium
    pasos.append((entorno, "Programas instalados (Python, librerías y navegador para las imágenes)",
                  "instalar el entorno (workflows/configurar.md, paso 0)"))
    if faltan and "yaml" in faltan:
        imprimir(pasos)
        return

    import yaml
    ruta_aj = RAIZ / "config" / "ajustes.yaml"
    aj = (yaml.safe_load(ruta_aj.read_text(encoding="utf-8")) or {}) if ruta_aj.exists() else {}
    env = leer_env()
    prog = (aj.get("programador") or {})
    nombre, via = (prog.get("nombre") or "").lower(), (prog.get("via") or "").lower()

    # 2. Programador
    pasos.append((bool(nombre and via), f"Programador elegido{f': {nombre} por {via.upper()}' if nombre and via else ''}",
                  "elegir programador y forma de conexión (workflows/configurar.md, paso 1)"))
    # 3. Conexión
    if nombre and via == "api":
        claves = POR_API.get(nombre, [])
        ok = bool(claves) and all(env.get(c) for c in claves)
        if nombre == "hootsuite":
            ok = ok and (RAIZ / ".hootsuite_token.json").exists()
        if nombre == "metricool":
            ok = ok and bool(prog.get("metricool_brand_id"))
        pasos.append((ok, f"Conexión con {nombre} por API",
                      f"conectar {nombre} por API (workflows/programadores/{nombre}.md)"))
    elif nombre and via == "mcp":
        extra = nombre != "metricool" or bool(prog.get("metricool_brand_id"))
        pasos.append((None if extra else False, f"Conector de {nombre} añadido en Claude (lo comprueba Claude en el chat)",
                      f"conectar {nombre} (workflows/programadores/{nombre}.md)"))

    # 4. Posts publicados
    posts = [p for p in (MARCA / "posts_que_funcionan").glob("*.md") if not p.name.startswith(("_", "LEEME"))]
    historico = any((MARCA / "_analisis" / "posts").glob("*")) if (MARCA / "_analisis" / "posts").exists() else False
    pasos.append((len(posts) >= 3 or historico, f"Posts publicados recogidos ({len(posts)} en posts_que_funcionan)",
                  "descargar o pegar posts ya publicados (workflows/configurar.md, paso 2)"))
    # 5. Web
    pasos.append(((MARCA / "_analisis" / "web" / "resumen.json").exists(), "Web analizada",
                  "analizar la web de la marca (workflows/configurar.md, paso 3)"))
    # 6. Marca
    for archivo, texto in (("voz.md", "Voz de la marca"), ("hechos.md", "Hechos de la marca"), ("guia_visual.md", "Guía visual")):
        pasos.append((not pendiente(MARCA / archivo), texto, "escribir el borrador de la marca (workflows/configurar.md, paso 4)"))
    pasos.append((not pendiente(RAIZ / "plantillas" / "_marca.css"), "Plantillas con tus colores y fuentes",
                  "adaptar las plantillas (workflows/configurar.md, paso 4)"))
    logo = any((MARCA / "logos").glob("logo.*"))
    pasos.append((logo, "Logo en marca/logos/", "guardar el logo como marca/logos/logo.svg o .png"))

    # 7. Imágenes
    prov = ((aj.get("imagenes") or {}).get("proveedor") or "").lower()
    if prov == "programador":
        pasos.append((True, "Imágenes: las recibe el propio programador", ""))
    else:
        claves = IMAGENES.get(prov, [])
        ok = bool(prov in IMAGENES and all(env.get(c) for c in claves))
        pasos.append((ok, f"Alojamiento de imágenes{f' ({prov})' if prov else ''}",
                      "configurar dónde se suben las imágenes (workflows/configurar.md, paso 5)"))

    # 8. Calendario (opcional)
    cal = aj.get("calendario") or {}
    herr = (cal.get("herramienta") or "").lower()
    if herr in CALENDARIO:
        cols = cal.get("columnas") or {}
        ok = all(env.get(c) for c in CALENDARIO[herr]) and bool(cols.get("titulo") and cols.get("fecha"))
        pasos.append((ok, f"Calendario: {herr}", f"conectar {herr} (workflows/calendario.md)"))
    elif herr:
        pasos.append((None, f"Calendario: {herr} por MCP (lo comprueba Claude en el chat)", ""))

    # 9. Diseño fuera del chat (opcional)
    modo = ((aj.get("diseno") or {}).get("modo") or "chat").lower()
    if modo != "chat":
        pasos.append((None, f"Diseño en {modo} (lo comprueba Claude en el chat)", ""))

    imprimir(pasos, preguntas_abiertas())


def imprimir(pasos, preguntas=0):
    print("Estado del sistema\n")
    for hecho, texto, _ in pasos:
        print(f"  {'✅' if hecho else ('🔎' if hecho is None else '⬜')}  {texto}")
    siguiente = next((s for h, _, s in pasos if h is False), None)
    if preguntas:
        print(f"\n  ❓ {preguntas} preguntas abiertas sobre la marca (no bloquean; se pueden responder en cualquier momento)")
    print("\nSiguiente paso: " + (siguiente or "¡todo listo! Pide tu primer post con /nuevo-post"))


if __name__ == "__main__":
    main()
