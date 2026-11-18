# Workflow: calendario de contenidos (opcional)

## Objetivo
Que cada post programado quede apuntado en la herramienta donde la persona lleva su calendario, con fecha, redes, copy, enlace e imágenes. **Solo se crean entradas nuevas; nunca se modifica una existente** salvo que la persona dé el cambio exacto. Si no usa ninguna herramienta, se salta este paso.

## Qué herramienta (en /empezar)
"¿Dónde llevas el calendario de contenidos o las tareas del equipo?"

| Herramienta | Cómo | Qué necesita |
|---|---|---|
| **Notion** | script `tools/calendario.py` | `NOTION_TOKEN` |
| **Google Sheets** | script, o el conector de Google de Claude | cuenta de servicio (`GOOGLE_SERVICE_ACCOUNT_FILE`) |
| **Airtable** | script | `AIRTABLE_TOKEN` |
| **Trello, Asana, ClickUp, monday** | su MCP, desde el chat | iniciar sesión en el conector |
| Ninguna | — | — |

Se guarda en `config/ajustes.yaml → calendario.herramienta`.

## Conectar

### Notion
1. notion.so/profile/integrations → "Nueva integración" → nombre "Programador de redes", tipo interna → copiar el secreto → `.env` → `NOTION_TOKEN=`.
2. Abrir el calendario en Notion → `…` → Conexiones → añadir "Programador de redes".
3. Copiar el enlace de la base: el id son los 32 caracteres antes de `?v=` → `calendario.notion.base_id`.
Si la empresa bloquea las integraciones internas, usa el conector de Notion de Claude con las mismas columnas, comprobando antes que la entrada no exista.

### Google Sheets
La forma más sencilla, si la persona tiene el **conector de Google Sheets en Claude**: usarlo directamente (añadir una fila con las columnas de la cabecera, comprobando antes que no exista). No hace falta nada más.

Por script (para quien no tenga el conector):
1. console.cloud.google.com → crear proyecto → activar "Google Sheets API" → Credenciales → Cuenta de servicio → Claves → Añadir clave → JSON. Guardar el archivo en la carpeta del repo (p. ej. `google_cuenta_servicio.json`, que **no** se sube: añádelo a `.gitignore`) → `.env` → `GOOGLE_SERVICE_ACCOUNT_FILE=google_cuenta_servicio.json`.
2. Compartir la hoja (Editor) con el correo de la cuenta de servicio (`…@….iam.gserviceaccount.com`).
3. `calendario.sheets.hoja_id` = el código largo de la URL; `pestana` = el nombre de la pestaña. La primera fila deben ser los nombres de las columnas.
4. `.venv/bin/python3 -m pip install google-auth`.

### Airtable
1. airtable.com/create/tokens → crear token con permisos `data.records:read`, `data.records:write` y `schema.bases:read`, y acceso a la base → `.env` → `AIRTABLE_TOKEN=`.
2. `calendario.airtable.base_id` (empieza por `app`, sale en la URL) y `tabla` (su nombre).

### Trello, Asana, ClickUp, monday
Añadir su conector en Claude (Ajustes → Conectores) e iniciar sesión. Preguntar en qué tablero, proyecto o lista van los posts → `calendario.destino`. Comprobar listando ese destino.

## Columnas
Con la herramienta conectada: `.venv/bin/python3 tools/calendario.py --ver` (o, por MCP, leer el tablero). Rellena `calendario.columnas` con el nombre exacto de la columna para cada dato: `titulo` y `fecha` son obligatorias; `redes`, `estado`, `enlace`, `copy` e `imagenes`, si existen. Pon `estado_inicial` (p. ej. "Programado").

Si no tiene calendario y quiere uno, propón crearlo con estas columnas: Título, Fecha (con hora), Redes (selección múltiple), Estado, Enlace, Copy, Imágenes.

## Crear la entrada (después de programar)
```bash
.venv/bin/python3 tools/calendario.py --titulo "<título corto>" --fecha "AAAA-MM-DD HH:MM" \
    --redes linkedin instagram --copy posts/<slug>/copy_final.md --enlace "<enlace con UTMs>" \
    --imagenes <URLs públicas de las imágenes>
```
Sin `--crear` enseña lo que haría; con `--crear` la crea. Si ya existe una con el mismo título y la misma fecha, no crea otra.

Por MCP (Trello, Asana, ClickUp, monday): busca antes una tarjeta con el mismo título y fecha en `calendario.destino`. Si no existe, créala con el título, la fecha de entrega = fecha de publicación, y en la descripción las redes, el copy, el enlace y las URLs de las imágenes.

## Aviso al equipo (opcional)
Si `avisos.slack_canal` está relleno y el conector de Slack está activo, manda allí una línea por post programado: qué, dónde, cuándo y el enlace a la entrada del calendario. Antes de publicar en un canal, lee su descripción por si ese tipo de mensajes va en otro sitio.
