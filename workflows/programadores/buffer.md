# Buffer (recomendado: por MCP)

> Escrito con la documentación oficial (nov-2026) pero **sin probar todavía con una cuenta real**. El primer post, como borrador, y comprobarlo en Buffer.

## Por qué MCP
Buffer **no recibe archivos** ni por API ni por MCP: en los dos casos hace falta un servicio de imágenes. Su histórico solo incluye lo publicado a través de Buffer, también en los dos casos. Así que por API no se gana nada importante, y por MCP no hay que buscar ninguna clave.

## Conectar (MCP)
- **Claude (web o escritorio):** Ajustes → Conectores → Añadir conector personalizado → `https://mcp.buffer.com/mcp` → iniciar sesión en Buffer.
- **Claude Code:** `claude mcp add --transport http buffer https://mcp.buffer.com/mcp` y `/mcp`.

Herramientas: `list_channels`, `create_post`, `edit_post`, `list_posts`, `get_post`, `get_aggregated_post_metrics`…
Comprobar: `list_channels` muestra tus redes.
Las conexiones por MCP comparten el límite de peticiones de la API (plan gratis: 1.000 al mes por canal).

## Conectar (API, alternativa)
Solo el propietario de la organización puede crear la clave: publish.buffer.com/settings/api → `.env` → `BUFFER_API_KEY=`. Después `config/ajustes.yaml`: `programador.nombre: buffer`, `via: api`. Comprobar: `.venv/bin/python3 tools/programar.py --cuentas`.

## Leer el histórico
Solo lo publicado con Buffer (lo guarda 2 años), con métricas.
- MCP: `list_posts` con estado `sent` e `includeMetrics`.
- API: `.venv/bin/python3 tools/historial.py`.
Si publicaba de otra forma, que pegue sus mejores posts.

## Programar
- Imágenes: primero `tools/subir_imagenes.py` y luego sus URLs.
- MCP: `create_post` por canal, con el texto, la fecha y las URLs de las imágenes. Lee la descripción de la herramienta para los campos exactos.
- API: `publicar.yaml` con las URLs en `imagenes` y `tools/programar.py` (ensayo, después `--confirmar`).
- **Buffer trabaja en hora UTC**: el script convierte solo; por MCP, comprueba en Buffer que la hora sale bien.
