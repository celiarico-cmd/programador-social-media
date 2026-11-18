# Postiz (recomendado: por API)

Postiz es de código abierto: se puede usar en su nube (postiz.com) o instalar en un servidor propio.

> Escrito con la documentación oficial (nov-2026) pero **sin probar todavía con una cuenta real**. El primer post, como borrador (`borrador: true`), y comprobarlo en Postiz.

## Por qué API
Por API, `programar.py` **sube las imágenes directamente a Postiz**: no hace falta Cloudinary. Su MCP solo acepta imágenes que ya estén en una URL pública.

## Conectar (API)
1. En Postiz: Settings → Developers → Public API → copia la clave.
2. Pégala en `.env` → `POSTIZ_API_KEY=` (nunca en el chat).
3. `config/ajustes.yaml`: `programador.nombre: postiz`, `via: api`, `imagenes.proveedor: programador`. Si Postiz está en tu servidor: `programador.postiz_url: https://tu-dominio`.
4. Comprobar: `.venv/bin/python3 tools/programar.py --cuentas`.

Límite: unas 30 publicaciones por hora por API (en un servidor propio se cambia con `API_LIMIT`). De sobra para el día a día.

## Conectar (MCP, alternativa)
`https://mcp.postiz.com/mcp`. Herramientas: `integrationList`, `schedulePostTool`, `postsListTool`, `uploadFromUrlTool`… Necesita un servicio de imágenes.

## Leer el histórico
Solo lo publicado con Postiz, y sin métricas: `.venv/bin/python3 tools/historial.py`. Si publicaba de otra forma, que pegue sus mejores posts.

## Programar
1. `posts/<slug>/publicar.yaml` con el copy por red, la fecha y las imágenes **como archivos locales**.
2. Ensayo: `.venv/bin/python3 tools/programar.py --post posts/<slug>/publicar.yaml` y enséñaselo.
3. Con el OK: el mismo comando con `--confirmar`.

Postiz trabaja en hora UTC; el script convierte solo desde la zona de la marca.
