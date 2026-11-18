# Workflow: configurar el sistema (/empezar)

## Objetivo
Dejar el sistema listo para crear y programar posts **sin que la persona tenga que saber nada técnico**. Claude instala, pregunta, explica y escribe los archivos. La persona solo decide y, cuando hace falta, inicia sesión o copia una clave.

## Cómo se habla con la persona
- Es probable que no sea técnica. Nada de jerga sin explicar: "MCP" se explica la primera vez ("una conexión directa entre Claude y tu programador; inicias sesión y listo").
- **Una pregunta cada vez**, con opciones cuando se pueda. Nunca un formulario.
- Antes de cada paso, una línea de para qué sirve. Al acabar, qué queda.
- **Nunca pidas que pegue una clave en el chat.** Las claves van al archivo `.env`: ábreselo (o dile cómo) y que la pegue allí.
- Se puede parar en cualquier momento. `.venv/bin/python3 tools/estado.py` (o `/estado`) dice siempre por dónde se va.
- Lo que no se pueda deducir no bloquea: se apunta en "Preguntas abiertas" y se sigue.

## Paso 0 · Instalar (lo hace Claude, sin preguntar nada técnico)
1. Comprueba Python: `python3 --version` (hace falta 3.10 o más). Si no está:
   - Mac: que instale las herramientas de Apple con `xcode-select --install` (sale una ventana: "Instalar") o el instalador de python.org.
   - Windows: el instalador de python.org, marcando "Add Python to PATH".
2. Crea el entorno e instala todo:
   ```bash
   python3 -m venv .venv
   .venv/bin/python3 -m pip install -r tools/requirements.txt
   .venv/bin/python3 -m playwright install chromium
   ```
   (En Windows: `.venv\Scripts\python` en lugar de `.venv/bin/python3`.) Tarda un par de minutos: avísalo.
3. `cp .env.ejemplo .env` si no existe.
4. `.venv/bin/python3 tools/estado.py` para confirmar.

## Paso 1 · El programador
**Pregunta:** "¿Qué programador de redes usas ahora (o cuál prefieres)? Metricool, Hootsuite, Zernio, Buffer, Postiz… Si no usas ninguno, te ayudo a elegir."

Si no usa ninguno: recomienda **Metricool** (plan gratis, 20 posts al mes, y lee el histórico de la cuenta) o **Buffer** (plan gratis, muy sencillo). Que se dé de alta y conecte allí sus redes antes de seguir.

Según el que use, **explica sus opciones** con la tabla y recomienda una:

| Programador | MCP (inicias sesión desde Claude) | API (una clave en `.env`) | ¿Recibe las imágenes él mismo? | ¿Lee tus posts ya publicados? |
|---|---|---|---|---|
| **Metricool** | ✅ cualquier plan, también el gratis | solo planes Advanced y Custom | ❌ hace falta Cloudinary/R2/ImageKit | ✅ histórico real con métricas, por MCP y por API (LinkedIn hasta 12 meses; Instagram 30 días al conectar) |
| **Hootsuite** | ✅ (Perch) | ✅ con una app aprobada por Hootsuite; **sin borradores** | ✅ por API; por MCP sin comprobar | por API solo lo publicado con Hootsuite, sin métricas; por MCP sin documentar |
| **Zernio** | ✅ | ✅ gratis hasta 2 cuentas | **por API sí** (por MCP te manda a una web: no) | **por API**, histórico real ~12 meses con métricas |
| **Buffer** | ✅ | ✅ todos los planes | ❌ hace falta Cloudinary/R2/ImageKit | solo lo publicado con Buffer |
| **Postiz** | ✅ | ✅ | **por API sí** | solo lo publicado con Postiz |

Cómo explicarlo en dos frases:
- **MCP** = inicias sesión una vez desde los ajustes de Claude y ya está. Lo más fácil.
- **API** = copias una clave a un archivo. Un paso más, pero en Zernio, Postiz y Hootsuite te ahorra el servicio de imágenes, y deja la puerta abierta a automatizar.

Recomendación por defecto:
- **Metricool → MCP** (funciona en el plan gratis). API solo si ya tiene Advanced y quiere automatizar.
- **Hootsuite → MCP.** Su API pide registrar una app y esperar a que Hootsuite la apruebe, y no tiene borradores.
- **Zernio y Postiz → API** (se ahorra el servicio de imágenes y, en Zernio, se lee el histórico).
- **Buffer → MCP** (por API no gana nada importante).

Guarda la elección en `config/ajustes.yaml → programador.nombre` y `programador.via`, y si el programador recibe las imágenes, `imagenes.proveedor: programador`.

**Conectar:** sigue `workflows/programadores/<nombre>.md → Conectar`.
- Por MCP, la persona añade el conector desde Claude (Ajustes → Conectores; en Claude Code, `claude mcp add` o `/mcp`) e inicia sesión. Comprueba que funciona llamando a la herramienta de listar cuentas.
- Por API, la persona copia la clave a `.env` (Hootsuite: además `tools/hootsuite_login.py`). Comprueba con `.venv/bin/python3 tools/programar.py --cuentas`.
Enseña las cuentas conectadas y pregunta en cuáles va a publicar → `config/ajustes.yaml → redes`.

## Paso 2 · Los posts ya publicados
Para qué: "Voy a leer lo que ya has publicado para aprender cómo escribes. Así no tienes que explicármelo."

- **Por MCP:** sigue `workflows/programadores/<nombre>.md → Leer el histórico`.
- **Por API:** `.venv/bin/python3 tools/historial.py --dias 365`.
- **Hootsuite, o Buffer/Postiz si publicaba de otra forma:** pide que pegue en el chat sus 5-10 mejores posts (o capturas), con los resultados si los sabe.

Todo acaba en `marca/_analisis/posts/historial.jsonl` (un post por línea: `red, fecha, texto, url, imagen, impresiones, alcance, reacciones, comentarios, compartidos, engagement`).

Después:
1. Ordena por resultados (engagement o reacciones + comentarios por impresión; si no hay métricas, pregunta cuáles cree que fueron mejor).
2. Crea un archivo por cada uno de los **5-10 mejores** en `marca/posts_que_funcionan/` con `_plantilla.md`, rellenando "Por qué funcionó" con lo que observas (gancho, largo, formato, persona protagonista…).
3. Enséñale la lista y pregunta si está de acuerdo o quiere cambiar alguno. Si los peores tienen algo en común, apúntalo: también enseña.

## Paso 3 · La web
**Pregunta:** "¿Cuál es tu web? Si hay una página de 'quiénes somos' o de servicios, pásamela también."

`.venv/bin/python3 tools/analizar_web.py <url> [<url2> …]` → `marca/_analisis/web/`.
Mira las capturas (Read) y el `resumen.json`. El color de acento suele ser el del botón principal. Comprueba el logo a ojo: si no es el bueno o no se encontró, pídelo (SVG o PNG con fondo transparente) y guárdalo como `marca/logos/logo.svg|png`. Si hay versión clara para fondos oscuros: `logo_claro.svg|png`.

Si tiene guía de marca, Figma o Canva con sus diseños, pídelo también: manda sobre lo que se deduce de la web. Las plantillas propias se hacen después con `workflows/crear_plantilla.md`.

## Paso 4 · El borrador de la marca
Escribe, quitando la línea "PENDIENTE" de cada archivo:
- `marca/voz.md` a partir de los posts (sobre todo los mejores): tuteo, largo, emojis, hashtags, cómo empiezan y acaban, palabras que repite.
- `marca/hechos.md` a partir del texto de la web: qué es, servicios, cifras con su fuente, enlaces. Nada que no salga de una fuente.
- `marca/guia_visual.md` a partir del análisis de la web y de las imágenes de los posts.
- `plantillas/_marca.css`: colores, fuentes (la línea `@import` de Google Fonts o `@font-face` con archivos en `marca/fuentes/`) y quita la línea "PENDIENTE".

Al final de cada archivo, una sección:
```markdown
## Preguntas abiertas
- [ ] ¿Se puede nombrar al equipo en los posts?
```
con lo que no se pudo deducir. Haz las 2-3 más importantes ahora en el chat; el resto pueden esperar (`/estado` las cuenta).

**Prueba de fuego** (si diseña en el chat; ver Paso 4b): construye una pieza de ejemplo con las plantillas (`posts/_prueba/visual/spec.json` con portada, texto y cierre, usando un texto real de la web) y enséñasela. Si los colores o la letra no convencen, corrige `_marca.css` y repite. Borra `posts/_prueba/` al terminar.

## Paso 4b · Dónde diseñas
**Pregunta:** "¿Dónde haces ahora las imágenes de tus posts?"
- **"No tengo nada" o "hazlas tú"** → `diseno.modo: chat`. Las plantillas HTML ya están adaptadas en el paso 4.
- **Canva** → `diseno.modo: canva`. Explica las dos formas (rellenar su plantilla o descargar lo que ella diseñe) y lo que permite su plan: `workflows/disenar_canva.md → Conectar`. Pide los enlaces de sus plantillas habituales y apúntalos en `marca/guia_visual.md`.
- **Figma** → `diseno.modo: figma`, avisando de que hace falta un plan de pago: `workflows/disenar_figma.md → Conectar`.
- **Otra herramienta** → `diseno.modo: chat` para lo que se haga aquí y, para lo suyo, que deje los PNG en `posts/<slug>/visual/final/`.

Si quiere que sus diseños de Canva o Figma también se puedan hacer en el chat, ofrece convertir los que más usa en plantillas (`workflows/crear_plantilla.md`). No es obligatorio.

## Paso 5 · Imágenes (solo si el programador no las recibe)
Si `imagenes.proveedor` no es `programador`, explica: "Tu programador necesita las imágenes en una dirección de internet. Las subimos a un servicio gratuito; ojo, quedan públicas desde que se suben."

| Servicio | Para quién | Qué hace falta en `.env` |
|---|---|---|
| **Cloudinary** (recomendado) | cualquiera; plan gratis amplio | `CLOUDINARY_URL` (Cloudinary → Settings → API Keys → "API environment variable") |
| **Cloudflare R2** | si ya usas Cloudflare | cuenta, clave, bucket y URL pública (`.env.ejemplo`); `pip install boto3` |
| **ImageKit** | alternativa a Cloudinary | `IMAGEKIT_PRIVATE_KEY` (Developer options) |

Guarda `imagenes.proveedor`. Prueba con una imagen de `posts/_prueba/` (`tools/subir_imagenes.py --slug prueba …`) y abre la URL.

## Paso 6 · Calendario (opcional)
"¿Llevas un calendario de contenidos o un tablero de tareas (Notion, Google Sheets, Airtable, Trello, Asana, ClickUp, monday…)? Puedo apuntar ahí cada post programado." Si sí → `workflows/calendario.md`. Si no, se deja vacío y listo.
Si trabaja en equipo y usa Slack, ofrece avisar en un canal de cada post programado (`avisos.slack_canal`).

## Paso 7 · UTMs
Pregunta el dominio de su web → `utm.dominios`, y si tiene campañas o secciones fijas → `utm.campanas`. Explica en una frase: "A cada enlace le añado una etiqueta para que en Google Analytics veas qué visitas vienen de cada post."

## Final
`.venv/bin/python3 tools/estado.py`. Si todo está en verde, propón el primer post con `/nuevo-post`.
