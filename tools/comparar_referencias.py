"""
Compara 2 o más piezas de la MISMA familia (p. ej. tres portadas de carrusel ya publicadas) para separar lo que
cambia en cada post de lo que se repite siempre. Es el primer paso para convertirlas en una plantilla.

    Lo que cambia (variable)  → suele ser la FOTO o el TEXTO: serán los campos de la plantilla.
    Lo que se repite (fijo)   → fondo, DEGRADADOS, FORMAS, logo, márgenes: van dentro de la plantilla.

Si el diseño viene de Figma, tools/figma.py capas da esto mismo con exactitud (leyendo las capas). Este script es
para cuando solo hay imágenes (Canva, otra herramienta, posts ya publicados). El resultado es una propuesta:
Claude la mira y la confirma con la persona.

Uso:
    python3 tools/comparar_referencias.py ref1.png ref2.png [ref3.png …] [--salida carpeta]

Salida (por defecto en marca/_analisis/plantillas/<nombre de la primera>/):
    mapa.png      la primera pieza con las zonas marcadas: rojo = foto, azul = texto, verde = fijo
    fijo.png      solo lo que se repite (lo variable en gris): base para dibujar la plantilla
    analisis.json zonas variables (posición en px y %, tipo), colores fijos y degradados detectados
"""

import argparse
import json
from collections import Counter, deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
CELDA = 8          # tamaño de la rejilla de análisis, en px
UMBRAL = 18        # diferencia media (0-255) a partir de la cual una celda "cambia" entre piezas


def hexa(rgb):
    return "#" + "".join(f"{int(round(c)):02X}" for c in rgb)


def cargar(rutas):
    base = Image.open(rutas[0]).convert("RGB")
    imgs = [base] + [Image.open(r).convert("RGB").resize(base.size, Image.LANCZOS) for r in rutas[1:]]
    return [np.asarray(i, dtype=np.float32) for i in imgs], base.size


def mapa_variable(arrs):
    """Celdas donde las piezas difieren entre sí."""
    pila = np.stack(arrs)                                  # n, h, w, 3
    dif = np.abs(pila - pila.mean(axis=0)).mean(axis=(0, 3))   # h, w
    h, w = dif.shape
    gh, gw = h // CELDA, w // CELDA
    rej = dif[:gh * CELDA, :gw * CELDA].reshape(gh, CELDA, gw, CELDA).mean(axis=(1, 3))
    m = Image.fromarray(((rej > UMBRAL) * 255).astype(np.uint8))
    m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))   # cerrar huecos entre letras
    return np.asarray(m) > 0


def regiones(mascara, minimo=6):
    """Componentes conexas de la rejilla (BFS). Devuelve listas de celdas."""
    vistas = np.zeros_like(mascara, dtype=bool)
    out = []
    gh, gw = mascara.shape
    for y in range(gh):
        for x in range(gw):
            if mascara[y, x] and not vistas[y, x]:
                cola, celdas = deque([(y, x)]), []
                vistas[y, x] = True
                while cola:
                    cy, cx = cola.popleft()
                    celdas.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < gh and 0 <= nx < gw and mascara[ny, nx] and not vistas[ny, nx]:
                            vistas[ny, nx] = True
                            cola.append((ny, nx))
                if len(celdas) >= minimo:
                    out.append(celdas)
    return out


def tipo_zona(arrs, caja):
    """foto (muchos colores, textura) o texto (casi todo 2-3 colores con bordes duros)."""
    x0, y0, x1, y1 = caja
    votos = []
    for a in arrs:
        zona = a[y0:y1, x0:x1].reshape(-1, 3)
        q = (zona // 32).astype(int)
        cuenta = Counter(map(tuple, q))
        top3 = sum(c for _, c in cuenta.most_common(3)) / max(len(q), 1)
        votos.append("texto" if top3 > 0.80 else "foto")
    return Counter(votos).most_common(1)[0][0]


def mediana(m, k=5):
    """Suaviza una línea de colores (quita picos de texto o líneas finas que se cruzan)."""
    r = k // 2
    return np.array([np.median(m[max(0, i - r): i + r + 1], axis=0) for i in range(len(m))])


def degradado(muestras):
    """Si una línea de colores cambia suave (sin saltos) y bastante de punta a punta, es un degradado."""
    if len(muestras) < 8:
        return None
    m = mediana(np.array(muestras))
    rango = np.abs(m.max(axis=0) - m.min(axis=0)).max()
    salto = np.abs(np.diff(m, axis=0)).max()
    if rango > 20 and salto < max(rango / 4, 6):
        return [hexa(m[0]), hexa(m[len(m) // 2]), hexa(m[-1])]
    return None


def tramo(px, fijo, puntos):
    """El tramo más largo de puntos seguidos que caen en zona fija."""
    mejor, actual = [], []
    gh, gw = fijo.shape
    for y, x in puntos:
        if 0 <= y < gh and 0 <= x < gw and fijo[y, x]:
            actual.append(px[y, x])
        else:
            mejor, actual = (actual if len(actual) > len(mejor) else mejor), []
    return actual if len(actual) > len(mejor) else mejor


def analizar_fijo(a, fijo):
    """Colores dominantes de lo fijo y degradados (vertical, horizontal y radial desde el punto más claro)."""
    gh, gw = fijo.shape
    px = a[:gh * CELDA, :gw * CELDA].reshape(gh, CELDA, gw, CELDA, 3).mean(axis=(1, 3))
    grupos = {}
    for c in px[fijo]:
        grupos.setdefault(tuple((c // 16).astype(int)), []).append(c)
    total = max(int(fijo.sum()), 1)
    dominantes = [{"color": hexa(np.mean(v, axis=0)), "porcentaje": round(100 * len(v) / total, 1)}
                  for v in sorted(grupos.values(), key=len, reverse=True)[:6]]

    # Fondo: suavizar mucho para que textos y formas pequeñas no cuenten, y buscar el punto más claro
    lum = np.where(fijo, px.mean(axis=2), np.nan)
    suave = np.asarray(Image.fromarray(np.nan_to_num(lum, nan=np.nanmedian(lum)).astype(np.uint8)).filter(ImageFilter.MedianFilter(9)))
    cy, cx = np.unravel_index(np.argmax(suave), suave.shape)
    lineas = {
        "vertical (arriba → abajo)": [[(y, x) for y in range(gh)] for x in (gw // 10, gw // 2, gw - gw // 10)],
        "horizontal (izquierda → derecha)": [[(y, x) for x in range(gw)] for y in (gh // 10, gh // 2, gh - gh // 10)],
        f"radial (desde {round(100 * cx / gw)} % ancho, {round(100 * cy / gh)} % alto, hacia fuera)":
            [[(int(cy + (ey - cy) * t / 60), int(cx + (ex - cx) * t / 60)) for t in range(61)]
             for ey, ex in ((0, 0), (0, gw - 1), (gh - 1, 0), (gh - 1, gw - 1))],
    }
    grads = {}
    for nombre, opciones in lineas.items():
        hallados = [g for g in (degradado(tramo(px, fijo, pts)) for pts in opciones) if g]
        if len(hallados) >= (2 if nombre.startswith("radial") else 1):
            grads[nombre] = hallados[0]
    if any(k.startswith("radial") for k in grads) and len(grads) > 1:
        grads = {k: v for k, v in grads.items() if k.startswith("radial")}   # un radial explica también las otras
    return dominantes, grads


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("imagenes", nargs="+", type=Path)
    ap.add_argument("--salida", type=Path)
    a = ap.parse_args()
    if len(a.imagenes) < 2:
        raise SystemExit("Hacen falta al menos 2 piezas de la misma familia (mejor 3).")

    arrs, (w, h) = cargar(a.imagenes)
    salida = a.salida or RAIZ / "marca" / "_analisis" / "plantillas" / a.imagenes[0].stem
    salida.mkdir(parents=True, exist_ok=True)

    var = mapa_variable(arrs)
    zonas = []
    for celdas in regiones(var):
        ys, xs = [c[0] for c in celdas], [c[1] for c in celdas]
        caja = (min(xs) * CELDA, min(ys) * CELDA, (max(xs) + 1) * CELDA, (max(ys) + 1) * CELDA)
        zonas.append({"tipo": tipo_zona(arrs, caja), "caja_px": list(caja),
                      "caja_pct": [round(100 * caja[0] / w, 1), round(100 * caja[1] / h, 1),
                                   round(100 * caja[2] / w, 1), round(100 * caja[3] / h, 1)],
                      "area_pct": round(100 * len(celdas) / var.size, 1)})
    zonas.sort(key=lambda z: (z["caja_px"][1], z["caja_px"][0]))
    dominantes, grads = analizar_fijo(arrs[0], ~var)

    # mapa.png y fijo.png
    base = Image.fromarray(arrs[0].astype(np.uint8))
    capa = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    gh, gw = var.shape
    for y in range(gh):
        for x in range(gw):
            if not var[y, x]:
                d.rectangle([x * CELDA, y * CELDA, (x + 1) * CELDA - 1, (y + 1) * CELDA - 1], fill=(0, 200, 90, 50))
    for i, z in enumerate(zonas, 1):
        color = (230, 40, 40, 255) if z["tipo"] == "foto" else (40, 90, 230, 255)
        d.rectangle(z["caja_px"], outline=color, width=6)
        d.text((z["caja_px"][0] + 10, z["caja_px"][1] + 8), f"{i} {z['tipo']}", fill=color)
    Image.alpha_composite(base.convert("RGBA"), capa).convert("RGB").save(salida / "mapa.png")
    fijo = base.copy()
    df = ImageDraw.Draw(fijo)
    for z in zonas:
        df.rectangle(z["caja_px"], fill=(160, 160, 160))
    fijo.save(salida / "fijo.png")

    resultado = {"piezas": [str(p) for p in a.imagenes], "tamano": [w, h], "zonas_variables": zonas,
                 "colores_fijos": dominantes, "degradados_fijos": grads,
                 "nota": "Propuesta automática. Confirma a ojo con mapa.png: un texto que no cambia entre piezas "
                         "(p. ej. el nombre de una serie) sale como fijo; una foto que se repite, también. Si la foto "
                         "ocupa toda la pieza, el texto que va encima queda dentro de la zona 'foto': sepáralo mirando "
                         "la imagen o leyendo las capas en Figma/Canva."}
    (salida / "analisis.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f"\nMapa: {salida / 'mapa.png'}")


if __name__ == "__main__":
    main()
