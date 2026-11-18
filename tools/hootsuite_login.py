"""
Inicia sesión en la API de Hootsuite una sola vez y guarda la sesión en .hootsuite_token.json (no se sube a GitHub).
Después tools/programar.py e historial.py la renuevan solos.

Antes (una vez), en developer.hootsuite.com:
  1. Crea una cuenta de desarrollador y espera a que Hootsuite la apruebe (te avisan por correo).
  2. Crea una app y, en su configuración de seguridad, añade esta dirección de retorno (redirect URI):
         http://localhost:8765/callback
  3. Copia su client id y su client secret a .env → HOOTSUITE_CLIENT_ID y HOOTSUITE_CLIENT_SECRET.

Uso:
    python3 tools/hootsuite_login.py
Se abre el navegador; inicia sesión en Hootsuite y acepta. La ventana dirá cuándo puedes cerrarla.
"""

import json
import os
import secrets
import sys
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
BASE = "https://platform.hootsuite.com"
RETORNO = "http://localhost:8765/callback"
TOKEN = RAIZ / ".hootsuite_token.json"


def main():
    id_app = os.environ.get("HOOTSUITE_CLIENT_ID", "").strip()
    secreto = os.environ.get("HOOTSUITE_CLIENT_SECRET", "").strip()
    if not (id_app and secreto):
        sys.exit("Faltan HOOTSUITE_CLIENT_ID y HOOTSUITE_CLIENT_SECRET en .env (ver workflows/programadores/hootsuite.md)")

    estado = secrets.token_urlsafe(16)
    recibido = {}

    class Retorno(BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(urlparse(self.path).query)
            recibido.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Listo. Ya puedes cerrar esta ventana y volver a Claude.</h2>".encode())

        def log_message(self, *a):
            pass

    url = f"{BASE}/oauth2/auth?" + urlencode({"response_type": "code", "client_id": id_app, "redirect_uri": RETORNO,
                                              "scope": "offline", "state": estado})
    print("Abriendo el navegador para iniciar sesión en Hootsuite…\nSi no se abre, copia esta dirección:\n" + url)
    webbrowser.open(url)
    servidor = HTTPServer(("localhost", 8765), Retorno)
    while "code" not in recibido and "error" not in recibido:
        servidor.handle_request()
    if recibido.get("error"):
        sys.exit(f"Hootsuite no autorizó el acceso: {recibido.get('error')}")
    if recibido.get("state") != estado:
        sys.exit("La respuesta no coincide con la petición (state). Vuelve a intentarlo.")

    r = requests.post(f"{BASE}/oauth2/token", auth=(id_app, secreto), timeout=60,
                      data={"grant_type": "authorization_code", "code": recibido["code"], "redirect_uri": RETORNO})
    if r.status_code >= 400:
        sys.exit(f"Hootsuite no dio la sesión: {r.status_code} {r.text[:300]}")
    d = r.json()
    TOKEN.write_text(json.dumps({"access_token": d["access_token"], "refresh_token": d.get("refresh_token"),
                                 "caduca": datetime.now().timestamp() + int(d.get("expires_in", 3600))}), encoding="utf-8")
    print("Sesión guardada. Comprueba tus cuentas con: .venv/bin/python3 tools/programar.py --cuentas")


if __name__ == "__main__":
    main()
