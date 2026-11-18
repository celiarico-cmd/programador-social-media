# Workflow: diseño

## Objetivo
Convertir los textos de slide del copywriter y las fotos del post en imágenes PNG listas para programar. Todo es borrador hasta que la persona lo aprueba.

## Dónde se diseña (`config/ajustes.yaml → diseno.modo`)
| Modo | Quién diseña | Workflow |
|---|---|---|
| `chat` | el diseñador, con las plantillas HTML de `plantillas/` y `tools/construir_visual.py` | este |
| `canva` | el diseñador rellena las plantillas de Canva de la persona, o la persona diseña y se descarga | `workflows/disenar_canva.md` |
| `figma` | igual, en Figma (plan de pago) | `workflows/disenar_figma.md` |

En cualquier modo, la persona puede decir en un post concreto "este lo hago yo": entonces solo se descarga. Las reglas de abajo (fotos, checklist) valen para los tres.

## Las fotos las da la persona
Las fotos de cada post las aporta la persona (en el chat o en una carpeta) y van en `posts/<slug>/fotos/`. **Nunca fotos de banco ni generadas o recreadas con IA**, aunque falte una: se pide. Si una foto tiene menos de 1080 px de lado corto, se avisa; ampliarla con IA solo con su OK.

## Lectura obligatoria
1. `marca/guia_visual.md`, incluidas las correcciones aprendidas.
2. `posts/<slug>/brief.md` y `copy.md` (tabla "Textos de slide").
3. `.venv/bin/python3 tools/construir_visual.py --lista`: campos obligatorios y opcionales de cada plantilla.

## Plantillas que vienen con el repo
| Plantilla | Para qué |
|---|---|
| `portada` | primera slide del carrusel o post de una imagen; con o sin foto |
| `texto` | slide intermedia: una idea, con número y foto opcionales |
| `cita` | frase literal de una persona real, con su nombre y su foto |
| `frase` | una frase grande (opinión, dato, anuncio corto) |
| `cierre` | última slide: conclusión o CTA, con el logo |

Formatos: `4:5` (feed de Instagram y LinkedIn, el más seguro), `3:4`, `1:1`, `9:16` (stories y reels), `16:9`.
Marcado de texto: `**negrita**`, `[[palabra]]` (color de acento), `_cursiva_` y `\n` para salto de línea.

Las plantillas de la marca (creadas desde Figma, Canva o una referencia) se añaden con `workflows/crear_plantilla.md`.

## Proceso (modo `chat`)
1. **Fotos.** Las de `posts/<slug>/fotos/`. Si falta alguna, se pide (ver arriba).
2. **Escribir `posts/<slug>/visual/spec.json`** con los textos del copywriter tal cual (misma negrita):
   ```json
   {"slug": "taller-masa-madre", "formato": "4:5", "slides": [
     {"plantilla": "portada", "datos": {"titulo": "Nadie te enseña a **esperar**", "foto": "../fotos/01.jpg"}},
     {"plantilla": "texto", "datos": {"numero": 1, "texto": "…", "flecha": true}},
     {"plantilla": "cierre", "datos": {"texto": "Reserva tu plaza **este sábado**"}}
   ]}
   ```
3. **Construir**: `.venv/bin/python3 tools/construir_visual.py --spec posts/<slug>/visual/spec.json`. El script para si falta un campo, si una foto no existe o si queda un `[A CONFIRMAR]`. Para un boceto con huecos, `--permitir-pendientes` (salen en rojo); nunca se entrega así.
4. **Mirar el resultado**: `final/<slug>_vista.jpg` y al menos una slide a tamaño real. Ajustar con los campos opcionales (`encuadre`, `velo`, `tamano`, `posicion`…) antes de pensar en tocar la plantilla.
5. **Entregar** la ruta de la vista previa y las decisiones tomadas. Si piden cambios, editar el spec y rehacer solo lo necesario con `--solo N`.

## Checklist antes de entregar
- [ ] El texto se lee en miniatura de móvil y no tapa caras.
- [ ] Ninguna cara cortada por el borde.
- [ ] Negrita solo en la idea clave, no en frases enteras.
- [ ] Nombres, fechas y cifras iguales que en el copy aprobado.
- [ ] Ninguna URL dentro de la imagen.
- [ ] Flecha de "desliza" en la portada de los carruseles.
- [ ] Formato correcto para la red (4:5 o 3:4 en el feed, 9:16 en stories).
- [ ] Ninguna corrección aprendida de `marca/guia_visual.md` se ha vuelto a cometer.

## Pieza sin plantilla
Si ninguna plantilla encaja, copia la más cercana a `posts/<slug>/visual/` y adáptala allí, sin tocar `plantillas/`. Si la misma pieza se repite en dos posts, propón convertirla en plantilla (`workflows/crear_plantilla.md`).

## Reglas aprendidas (válidas para cualquier marca)
- **Si cambias una foto, rehaz todas las slides que la usan**, no solo una.
- **Para comparar alternativas, usa siempre la misma receta**: si una opción cambia otra cosa sin querer, la comparación engaña.
- **Si se edita una imagen con IA (ampliar, quitar fondo), se enseña el resultado tal cual** con sus defectos. Decide la persona; no lo "arregles" por tu cuenta.
- **Las imágenes generadas con IA se inventan el texto pequeño** (pantallas, carteles). No las uses donde ese texto se lea.
- **Revisa los exports de Canva o Figma**: a veces traen franjas o líneas en el borde que hay que recortar.

## Cuando la persona corrige
Si la corrección vale para todas las piezas (color, tamaño, posición), apúntala con fecha en `marca/guia_visual.md → Correcciones aprendidas` y **propón** el cambio en la plantilla. No lo hagas sin su OK.

## Problemas típicos
- **"Falta el navegador Chromium"**: `.venv/bin/python3 -m playwright install chromium`.
- **La fuente no carga** (sin conexión o nombre mal escrito en `_marca.css`): la imagen sale con otra letra. No la entregues; corrige y repite.
- **Foto vertical en un hueco horizontal**: prueba `encuadre` (p. ej. `"50% 20%"`). Si ninguna posición salva las caras, pide otra foto.
- **Texto demasiado largo**: devuélvelo al copywriter para acortarlo. No bajes la letra por debajo de ~34 px.
