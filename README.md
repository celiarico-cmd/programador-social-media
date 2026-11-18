# Programador de social media

**Crea y programa los posts de tu marca desde una sola conversación con Claude.**

Le cuentas qué quieres publicar y Claude:
1. escribe el texto con **la voz de tu marca**, aprendida de lo que ya has publicado;
2. diseña las imágenes con **tus colores, tus fuentes y tus plantillas**, en el propio chat o en tu **Canva** o **Figma** (o descarga lo que diseñes tú allí);
3. añade los **UTMs** a los enlaces para que sepas qué visitas trae cada post;
4. lo **programa** en tu programador de siempre (Metricool, Hootsuite, Zernio, Buffer o Postiz);
5. y, si quieres, lo apunta en **tu calendario** (Notion, Google Sheets, Airtable, Trello, Asana, ClickUp o monday) y avisa al equipo en Slack.

No hace falta saber programar. El propio repositorio te guía para montarlo todo. Y nada se publica sin que digas que sí.

---

## Cómo empezar (3 pasos)

### 1. Lo que necesitas
- Una cuenta de **Claude** de pago (Pro o superior) con **Claude Code**: está en la app de escritorio de Claude (pestaña "Code"), en VS Code o en la terminal.
- Una cuenta en tu **programador de redes**. Si no tienes ninguno, durante la configuración te ayudamos a elegir (Metricool y Buffer tienen plan gratis).

### 2. Descarga el repositorio
- **Opción fácil:** arriba en esta página, botón verde **"Code" → "Download ZIP"**, y descomprímelo donde quieras.
- **Si usas GitHub:** botón **"Use this template"** → crea tu copia **privada**. Privada, porque ahí irán la voz, los hechos y los posts de tu marca.

### 3. Ábrelo en Claude Code y escribe `/empezar`
Abre la carpeta en Claude Code y escribe:

```
/empezar
```

Claude instala lo necesario, te hace una pregunta cada vez y en unos 20-30 minutos lo tienes listo. Puedes parar cuando quieras: con `/estado` ves por dónde vas.

Después, para cada post:

```
/nuevo-post
```

---

## Qué pasa en `/empezar`

1. **Tu programador.** Te pregunta cuál usas y te explica las dos formas de conectarlo (abajo), con una recomendación.
2. **Lo que ya has publicado.** Si tu programador lo permite, descarga tus posts con sus resultados. Si no, se los pegas. Con eso aprende cómo escribes y elige tus mejores posts como referencia.
3. **Tu web.** La analiza para sacar colores, tipografías, logo y los datos de tu marca.
4. **El borrador de tu marca.** Escribe tu guía de voz, tus hechos y tu guía visual, y adapta las plantillas. Lo que no pueda deducir lo deja como "pregunta abierta": no te bloquea, lo vas respondiendo cuando quieras.
5. **Dónde diseñas**: en el chat, en Canva o en Figma.
6. **Imágenes, calendario y UTMs**: solo lo que necesites.

## Programadores: MCP o API

Hay dos formas de conectar tu programador con Claude:
- **MCP**: inicias sesión desde los ajustes de Claude y listo. Lo más fácil.
- **API**: copias una clave a un archivo. Un paso más, pero en algunos programadores te ahorra un servicio de imágenes y permite automatizar.

| Programador | MCP | API | ¿Recibe las imágenes él mismo? | ¿Lee tus posts ya publicados? | Recomendado |
|---|---|---|---|---|---|
| **Metricool** | ✅ en todos los planes | planes Advanced y Custom | ❌ | ✅ el histórico real, con métricas | MCP |
| **Hootsuite** | ✅ | con app aprobada por Hootsuite; sin borradores | ✅ por API | por API, solo lo publicado con Hootsuite | MCP |
| **Zernio** | ✅ | ✅ gratis hasta 2 cuentas | ✅ por API | ✅ por API, ~12 meses, con métricas | API |
| **Buffer** | ✅ | ✅ | ❌ | solo lo publicado con Buffer | MCP |
| **Postiz** | ✅ | ✅ | ✅ por API | solo lo publicado con Postiz | API |

Si tu programador no recibe las imágenes, se suben antes a un servicio gratuito: **Cloudinary** (recomendado), **Cloudflare R2** o **ImageKit**. Las imágenes quedan en una dirección pública desde que se suben.

¿Usas otro programador? Se puede añadir: copia uno de `workflows/programadores/` y adáptalo.

## Diseño: en el chat, en Canva o en Figma

| Dónde | Qué hace Claude | Qué necesitas |
|---|---|---|
| **En el chat** | Rellena las plantillas HTML del repo con tus colores y fuentes | Nada |
| **Canva** | Rellena tus plantillas de Canva o descarga lo que diseñes tú | El conector de Canva (cualquier plan; el relleno por campos, Pro) |
| **Figma** | Lo mismo en Figma | Plan de pago de Figma |

Las fotos de cada post las pones tú: nunca usa fotos de banco ni generadas con IA.

**Tus diseños como plantillas.** Pásale 2 o 3 piezas de la misma serie (o el enlace de Figma) y Claude separa lo que cambia en cada post (la foto, el texto) de lo que se repite (fondo, degradados, formas, logo) para convertirlo en una plantilla que se rellena sola.

## Calendario (opcional)
Si llevas un calendario de contenidos, cada post programado se apunta solo: **Notion, Google Sheets o Airtable** (con script) o **Trello, Asana, ClickUp o monday** (con su conector). Y, si quieres, un aviso al equipo en **Slack**.

## Qué hay dentro

```
marca/                 ← tu marca: de aquí beben los agentes
  voz.md                 cómo escribe tu marca
  hechos.md              lo único que se puede afirmar (cifras, nombres, enlaces)
  guia_visual.md         colores, fuentes, fotos, composición
  posts_que_funcionan/   tus mejores posts y por qué funcionaron
  logos/  fuentes/
plantillas/            plantillas de las imágenes (portada, texto, cita, frase, cierre) + _marca.css
posts/                 cada post: brief, copy, fotos, imágenes finales
config/ajustes.yaml    tus elecciones (programador, redes, diseño, calendario…)
.env                   tus claves secretas (se crea en /empezar; nunca se sube a GitHub)
workflows/             las instrucciones que sigue Claude en cada tarea
tools/                 los scripts que hacen el trabajo repetible
.claude/               los agentes (copywriter, diseñador) y los comandos (/empezar, /nuevo-post, /estado)
```

## Preguntas frecuentes

**¿Puede publicar algo sin que yo lo vea?**
No. Antes de programar te enseña el texto, las imágenes, la red, la fecha y la hora, y espera tu "sí". Además, nunca toca lo que ya tengas programado.

**¿Se inventa cosas?**
Está hecho para que no. Solo afirma lo que esté en `marca/hechos.md` o en lo que le cuentes para el post. Si falta un dato, escribe `[A CONFIRMAR]` y te pregunta.

**¿Mejora con el uso?**
Sí. Cada corrección que le hagas ("no empieces así", "este color no") se apunta en tu guía de voz o en tu guía visual, y no vuelve a pasar.

**¿Puedo seguir diseñando en Canva o Figma?**
Sí. Claude puede rellenar tus plantillas allí o, si prefieres diseñar tú, solo descarga las imágenes y se encarga del resto. También puede convertir tus diseños en plantillas que se rellenan en el chat.

**¿Dónde están mis datos?**
En tu ordenador, en esta carpeta. Las claves, en `.env`, que nunca se sube a GitHub. Lo único que sale fuera es lo que publicas y las imágenes que se suben para programar.

**¿Cuánto cuesta?**
El repositorio es gratis. Pagas tu plan de Claude y, si lo tienes, tu programador (varios tienen plan gratis).

---

Nace de un sistema real de gestión de redes. Las reglas de copy y diseño que trae (el corte del "…ver más", las fórmulas de IA que hay que evitar, no inventar datos, no programar nada sin OK) salen de meses de correcciones.

Licencia MIT.
