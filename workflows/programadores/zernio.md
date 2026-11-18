# Zernio (recomendado: por API)

Zernio se llamaba antes Late (getlate.dev); las claves antiguas (`late_…`) siguen funcionando.

> Los scripts están escritos con la documentación oficial (nov-2026) pero **sin probar todavía con una cuenta real**. El primer post, como borrador (`borrador: true`), y comprobarlo en Zernio.

## Por qué API y no MCP
- Por API, `programar.py` **sube las imágenes directamente a Zernio**: no hace falta Cloudinary. Por MCP, Zernio te da un enlace para subir el archivo en una web, y eso te saca de la conversación.
- Por API, `historial.py` lee el **histórico real** de la cuenta (también lo publicado fuera de Zernio), unos 12 meses, con métricas.
- La API protege contra el doble envío (`Idempotency-Key`): si algo falla y se repite, no se publica dos veces.

## Conectar (API)
1. Crea la cuenta en zernio.com y conecta allí tus redes. Gratis hasta 2 cuentas.
2. En el panel de Zernio, crea una clave de API.
3. Pégala en `.env` → `ZERNIO_API_KEY=` (nunca en el chat).
4. `config/ajustes.yaml`: `programador.nombre: zernio`, `via: api`, `imagenes.proveedor: programador`.
5. Comprobar: `.venv/bin/python3 tools/programar.py --cuentas`.

Instagram necesita cuenta Business o Creator. Carruseles de hasta 20 imágenes; cada una de hasta 8 MB, JPEG o PNG.

## Conectar (MCP, alternativa)
Ajustes → Conectores → `https://mcp.zernio.com/mcp`. Herramientas: `accounts_list`, `posts_create`, `posts_list`, `posts_update`… Por MCP hace falta un servicio de imágenes y pasar las URLs en `media_urls`.

## Leer el histórico
`.venv/bin/python3 tools/historial.py --dias 365`. Si da error 402, tu plan no incluye estadísticas: pide a la persona sus mejores posts.

## Programar
1. Escribe `posts/<slug>/publicar.yaml` (formato en la cabecera de `tools/programar.py`) con el copy final por red, la fecha y las imágenes locales.
2. Ensayo: `.venv/bin/python3 tools/programar.py --post posts/<slug>/publicar.yaml` y enséñaselo.
3. Con el OK: el mismo comando con `--confirmar`.

La hora va en la zona de la marca (Zernio la recibe junto a la zona horaria).
