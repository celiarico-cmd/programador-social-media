"""
Descarga los posts ya publicados de la marca, con sus métricas, desde el programador por API.
Con eso /empezar aprende la voz de la marca y elige los "posts que funcionan".

Qué trae cada uno por API (según su documentación, nov-2026):
    metricool  histórico real de la cuenta (también lo publicado fuera de Metricool), con métricas
    zernio     histórico real de la cuenta, unos 12 meses, con métricas
    buffer     solo lo publicado a través de Buffer (2 años), con métricas
    postiz     solo lo publicado a través de Postiz, sin métricas
    hootsuite  solo lo publicado a través de Hootsuite, sin métricas (sus métricas son un complemento de pago
               y no incluyen LinkedIn)
Si tu programador está conectado por MCP, se lee desde el chat (ver workflows/configurar.md, paso 2).

Uso:
    python3 tools/historial.py [--dias 365]

Salida: marca/_analisis/posts/historial.jsonl, un post por línea, siempre con los mismos campos:
    red, fecha, texto, url, imagen, impresiones, alcance, reacciones, comentarios, compartidos, engagement
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from programar import PROGRAMADORES, ajustes, salir  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "marca" / "_analisis" / "posts" / "historial.jsonl"


def fila(**kw):
    campos = ["red", "fecha", "texto", "url", "imagen", "impresiones", "alcance", "reacciones", "comentarios",
              "compartidos", "engagement"]
    return {c: kw.get(c) for c in campos}


def zernio(p, desde, hasta):
    out = []
    for cuenta in p.cuentas():
        pagina = 1
        while True:
            d = p.req("GET", "/analytics", params={"source": "all", "accountId": cuenta["id"], "page": pagina, "limit": 100,
                                                   "fromDate": desde.date().isoformat(), "toDate": hasta.date().isoformat()})
            posts = d.get("posts") or d.get("data") or []
            for x in posts:
                m = x.get("analytics") or x.get("metrics") or x
                media = x.get("mediaItems") or []
                out.append(fila(red=cuenta["red"], fecha=x.get("publishedAt"), texto=x.get("content"),
                                url=x.get("platformPostUrl"), imagen=(media[0].get("url") if media else None),
                                impresiones=m.get("impressions"), alcance=m.get("reach"), reacciones=m.get("likes"),
                                comentarios=m.get("comments"), compartidos=m.get("shares"),
                                engagement=m.get("engagementRate")))
            total_paginas = (d.get("pagination") or {}).get("pages") or 1
            if not posts or pagina >= total_paginas:
                break
            pagina += 1
    return out


def buffer(p, desde, hasta):
    out = []
    orgs = p.gql("query { account { organizations { id } } }")["account"]["organizations"]
    q = """query($o: OrganizationId!, $after: String) {
      posts(first: 100, after: $after, input: {organizationId: $o, filter: {status: [sent]}}) {
        edges { node { text sentAt externalLink channelService assets { thumbnail } metrics { type value } } }
        pageInfo { hasNextPage endCursor } } }"""
    for o in orgs:
        cursor = None
        while True:
            d = p.gql(q, {"o": o["id"], "after": cursor})["posts"]
            for e in d["edges"]:
                n = e["node"]
                if n.get("sentAt") and n["sentAt"] < desde.isoformat():
                    continue
                m = {x["type"].lower(): x["value"] for x in (n.get("metrics") or [])}
                assets = n.get("assets") or []
                out.append(fila(red=n.get("channelService"), fecha=n.get("sentAt"), texto=n.get("text"),
                                url=n.get("externalLink"), imagen=(assets[0].get("thumbnail") if assets else None),
                                impresiones=m.get("impressions"), alcance=m.get("reach"), reacciones=m.get("reactions"),
                                comentarios=m.get("comments"), compartidos=m.get("shares")))
            if not d["pageInfo"]["hasNextPage"]:
                break
            cursor = d["pageInfo"]["endCursor"]
    return out


def postiz(p, desde, hasta):
    d = p.req("GET", "/posts", params={"startDate": desde.isoformat(), "endDate": hasta.isoformat()})
    posts = d.get("posts", d) if isinstance(d, dict) else d
    return [fila(red=(x.get("integration") or {}).get("providerIdentifier"), fecha=x.get("publishDate"),
                 texto=x.get("content"), url=x.get("releaseURL"))
            for x in posts if x.get("state") == "PUBLISHED"]


def metricool(p, desde, hasta):
    out = []
    for c in p.cuentas():
        try:
            d = p.req("GET", f"/v2/analytics/posts/{c['red']}", params={
                "from": desde.strftime("%Y-%m-%dT00:00:00"), "to": hasta.strftime("%Y-%m-%dT23:59:59"), "timezone": p.zona})
        except SystemExit as e:
            print(f"Aviso: no se pudo leer {c['red']}: {e}")
            continue
        if not isinstance(d, dict):
            print(f"Aviso: {c['red']} no devolvió JSON (¿CSV?); se omite. Léelo por MCP si lo necesitas.")
            continue
        for x in d.get("data") or []:
            g = lambda *ks: next((x[k] for k in ks if x.get(k) not in (None, "")), None)  # noqa: E731
            out.append(fila(red=c["red"], fecha=g("publishedAt", "created", "date"), texto=g("content", "comment", "text"),
                            url=g("url", "link"), imagen=g("imageUrl", "picture", "thumbnail"),
                            impresiones=g("impressions", "impressionsTotal"), alcance=g("reach"),
                            reacciones=g("likes", "reactions"), comentarios=g("comments"), compartidos=g("shares"),
                            engagement=g("engagement")))
    return out


def hootsuite(p, desde, hasta):
    out, inicio = [], desde
    while inicio < hasta:                       # la API deja pedir como mucho 4 semanas cada vez
        fin = min(inicio + timedelta(days=27), hasta)
        cursor = None
        while True:
            params = {"startTime": inicio.strftime("%Y-%m-%dT%H:%M:%SZ"), "endTime": fin.strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "state": "SENT", "limit": 100}
            if cursor:
                params["cursor"] = cursor
            d = p.req("GET", "/v1/messages", params=params)
            for m in d.get("data", []):
                out.append(fila(red=str(m.get("socialProfile", {}).get("type", "")).lower() or None,
                                fecha=m.get("sendTime") or m.get("scheduledSendTime"), texto=m.get("text"),
                                url=m.get("postUrl")))
            cursor = (d.get("metadata") or {}).get("cursor", {}).get("next") if isinstance(d.get("metadata"), dict) else None
            if not cursor:
                break
        inicio = fin
    return out


LECTORES = {"metricool": metricool, "hootsuite": hootsuite, "zernio": zernio, "buffer": buffer, "postiz": postiz}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=365)
    a = ap.parse_args()

    prog = ajustes().get("programador") or {}
    nombre = (prog.get("nombre") or "").lower()
    if nombre not in LECTORES or (prog.get("via") or "").lower() != "api":
        salir("Este script es para programadores conectados por API. Por MCP, el histórico se lee desde el chat.")
    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(days=a.dias)
    try:
        posts = LECTORES[nombre](PROGRAMADORES[nombre](ajustes()), desde, hasta)
    except requests.RequestException as e:
        salir(f"No se pudo conectar con {nombre}: {e}")
    posts = [x for x in posts if (x["texto"] or "").strip()]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8") as f:
        for x in sorted(posts, key=lambda x: x["fecha"] or "", reverse=True):
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    redes = {}
    for x in posts:
        redes[x["red"]] = redes.get(x["red"], 0) + 1
    print(f"{len(posts)} posts guardados en {SALIDA.relative_to(RAIZ)}  ({', '.join(f'{k}: {v}' for k, v in redes.items())})")
    if nombre in ("buffer", "postiz", "hootsuite"):
        print(f"Ojo: {nombre} solo conoce lo publicado a través de {nombre}. Si publicabas de otra forma, faltan posts:"
              " pega los mejores en el chat.")


if __name__ == "__main__":
    main()
