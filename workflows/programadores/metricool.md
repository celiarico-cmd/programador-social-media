# Metricool (recomendado: por MCP)

Probado a fondo: es el que usaba el proyecto del que sale este repo.

## Conectar
- **Claude (web o escritorio):** Ajustes → Conectores → Añadir conector personalizado → `https://ai.metricool.com/mcp` → iniciar sesión en Metricool.
- **Claude Code:** `claude mcp add --transport http metricool https://ai.metricool.com/mcp` y después `/mcp` para iniciar sesión.

Funciona en **todos los planes, también el gratuito** (20 posts programados al mes).

Comprobar: `getBrandSettings` devuelve las marcas con su `blogId` (= brandId) y su zona horaria. Guárdalos en `config/ajustes.yaml → programador.metricool_brand_id` y `marca.zona_horaria`. Mira qué redes tiene conectadas.

Metricool **no recibe archivos**: hace falta un servicio de imágenes (`imagenes.proveedor`: cloudinary, r2 o imagekit).

## Leer el histórico
Metricool guarda las estadísticas de cada red, también de lo publicado fuera de Metricool. Al conectar una cuenta trae: LinkedIn (página) hasta 12 meses, perfil personal ~3 meses, Instagram 30 días; desde entonces sigue guardando.

1. Por cada red: `getAnalyticsAvailableMetrics(network=<red>, connector="posts")`. Elige los campos de fecha con hora, texto, URL, imagen, impresiones, alcance, reacciones/likes, comentarios, compartidos y engagement. En LinkedIn son `LIPO02, LIPO04, LIPO08, LIPO07, LIPO12, LIPO13, LIPO10, LIPO18, LIPO9999`; en las demás redes, mira los suyos.
2. `getAnalyticsDataByMetrics(brandId, from, to, metrics=[…])` por tramos de 1-3 meses.
3. Guarda cada post en `marca/_analisis/posts/historial.jsonl` con los campos normalizados: `red, fecha, texto, url, imagen, impresiones, alcance, reacciones, comentarios, compartidos, engagement`.

## Programar
`createScheduledPost(blogId, date, info)`. `info` es un JSON con:
- `publicationDate`: `{"dateTime": "AAAA-MM-DDTHH:MM:SS", "timezone": "<zona de la marca>"}`
- `providers`: `[{"network": "linkedin"}]`, `[{"network": "instagram"}]`… **Un post por red** cuando el texto cambia de una a otra.
- `text`: el copy final de esa red.
- `media`: las URLs públicas de `subir_imagenes.py`, en orden. Varias = carrusel.
- `firstCommentText`: el enlace con UTMs, si la voz dice que va en el primer comentario.
- `autoPublish: true`, `draft: false`. Con `autoPublish: false` Metricool **no publica**: solo manda un aviso al móvil.
- `linkedinData`: `{"type": "post"}`. Para carrusel de documento (PDF): `{"type": "post", "documentTitle": "<título>", "publishImagesAsPDF": true}`.
- `instagramData`: tipo `POST`, `REEL` o `STORY`. Lee la descripción de la herramienta antes de rellenarlo; no adivines.

Antes: `getScheduledPosts` en ±3 días para no duplicar. Para sugerir hora: `getBestTimeToPostByNetwork`.

## Lo aprendido
- **El id del post cambia solo** al poco de crearlo (el `uuid` no). Antes de cualquier `updateScheduledPost`, vuelve a sacar el id con `getScheduledPosts`. Al editar hay que enviar el contenido completo.
- **Enlaces de Google Drive como `media`**: fallan en carruseles ("Failed to normalize media"), cada vez en una imagen distinta. Con Cloudinary pasan a la primera. Usa siempre un servicio de imágenes.
- **Carruseles de Instagram de más de 10 imágenes**: Metricool no los programa.
- **Menciones en LinkedIn**: "@Nombre" a secas sale como texto plano. La sintaxis que funciona es `@[urn:li:organization:<id>|<Nombre exacto>]` para empresas y `@[urn:li:person:<id>|<Nombre exacto>]` para personas. El id de persona no se puede calcular: etiqueta a la persona una vez desde el editor web de Metricool, lee el post con `getScheduledPosts` y apunta su id para la próxima. Truco: en el buscador de @ del editor, busca por el identificador de la URL del perfil (lo que va tras `/in/`).
- **Al hacer `updateScheduledPost`**, conserva las menciones tal como vienen o se pierden.
- **Música en reels** (`instagramData.audioConfiguration`): solo con Instagram vinculado a una página de Facebook en Metricool y con `autoPublish: true`.

## Por API (alternativa, planes Advanced y Custom)
Solo merece la pena si ya tiene Advanced y quiere scripts (p. ej. para automatizar). Hace lo mismo que el MCP.

> Escrito con la especificación oficial de la API (nov-2026) pero **sin probar todavía con una cuenta real**. El primer post, como borrador.

**Conectar:**
1. Metricool → Ajustes de la cuenta → API → copia el token → `.env` → `METRICOOL_USER_TOKEN=`. Si lo regeneras, el anterior deja de funcionar al momento.
2. `userId` y `blogId` salen en la URL de Metricool con la marca abierta → `.env` → `METRICOOL_USER_ID=` y `config/ajustes.yaml → programador.metricool_brand_id`.
3. `config/ajustes.yaml`: `programador.nombre: metricool`, `via: api`. Imágenes: hace falta un servicio de imágenes, igual que por MCP.
4. Comprobar: `.venv/bin/python3 tools/programar.py --cuentas` (las redes conectadas a la marca).

**Histórico:** `.venv/bin/python3 tools/historial.py` (endpoints `/v2/analytics/posts/<red>`). Si alguna red no devuelve JSON, se avisa y se puede leer por MCP.

**Programar:** `posts/<slug>/publicar.yaml` con las URLs de las imágenes y `tools/programar.py` (ensayo, después `--confirmar`). El script pasa cada imagen por el normalizador de Metricool (`/actions/normalize/image/url`): sin ese paso, el post puede salir sin imagen.
