# Hootsuite (recomendado: por MCP "Perch")

> **Sin probar todavía con una cuenta real.** Hootsuite no publica la lista de herramientas de su MCP. La primera vez que se conecte, lista las herramientas, apunta aquí cuáles sirven para listar cuentas, programar y subir imágenes, y cómo se usan. Mejora este archivo con lo que veas.

## Conectar
- Necesitas una cuenta de Hootsuite con acceso al MCP (los planes concretos no están publicados).
- **Claude (web o escritorio):** Ajustes → Conectores → Añadir conector personalizado → `https://mcp.hootsuite.com/perch` → iniciar sesión con tu espacio de Hootsuite.
- **Claude Code:** `claude mcp add --transport http hootsuite https://mcp.hootsuite.com/perch` y `/mcp` para iniciar sesión.

Hootsuite tiene otros servidores para la bandeja de entrada (`/nest`), la escucha (`/lumen`) y la defensa de marca por empleados (`/parliament`). Para programar basta Perch.

## Qué se sabe (web de Hootsuite, nov-2026)
- Guarda y actualiza borradores, crea borradores programados y programa posts.
- **Puede subir imágenes** y usar la biblioteca de contenidos: probablemente no haga falta Cloudinary. Compruébalo y, si es así, `imagenes.proveedor: programador`.
- Hootsuite dice que "la revisión humana sigue formando parte del proceso": puede que los posts queden pendientes de aprobación. Compruébalo con el primer post.
- Revisa estadísticas (impresiones, interacción, alcance). Que lea posts antiguos con su texto no está confirmado.

## Leer el histórico
Si alguna herramienta devuelve los posts publicados con su texto, úsala y guárdalos en `marca/_analisis/posts/historial.jsonl` (campos del paso 2 de `workflows/configurar.md`). Si no, pide a la persona que pegue sus mejores posts.

## Programar
Con las herramientas que muestre el conector, siguiendo `workflows/programar.md`. Primer post: como borrador, y que la persona lo compruebe en Hootsuite antes de programar de verdad.

## Por API (alternativa)
> Escrito con la especificación oficial de la API (nov-2026) pero **sin probar todavía con una cuenta real**.

Diferencias con el MCP que hay que explicar antes de elegirla:
- **Hay que registrarse como desarrollador y esperar a que Hootsuite apruebe la cuenta** (avisan por correo). La API es gratis para quien tenga ese acceso; qué planes de Hootsuite la permiten no está publicado.
- **No hay borradores**: todo lo que se envía se publica a su hora. Para probar, programa a una cuenta de pruebas o con mucha antelación y bórralo desde Hootsuite.
- **Sube las imágenes él mismo**: no hace falta servicio de imágenes (`imagenes.proveedor: programador`).
- **Histórico**: solo lo publicado con Hootsuite y sin métricas. Sus métricas por post son un complemento de pago (Advanced Analytics) y **no incluyen LinkedIn**.
- Hay que programar con al menos 5 minutos de antelación (15 con vídeo). No publica en TikTok, YouTube ni Bluesky por API.
- Que varias imágenes en un mensaje salgan como carrusel en Instagram o LinkedIn no está documentado: compruébalo con el primer post.

**Conectar:**
1. developer.hootsuite.com → crear cuenta de desarrollador → esperar la aprobación.
2. Crear una app. En su configuración de seguridad, añadir como dirección de retorno (redirect URI): `http://localhost:8765/callback`.
3. Copiar client id y client secret → `.env` → `HOOTSUITE_CLIENT_ID=` y `HOOTSUITE_CLIENT_SECRET=`.
4. `config/ajustes.yaml`: `programador.nombre: hootsuite`, `via: api`, `imagenes.proveedor: programador`.
5. `.venv/bin/python3 tools/hootsuite_login.py`: se abre el navegador, la persona inicia sesión y acepta. La sesión se guarda en `.hootsuite_token.json` (no se sube a git) y se renueva sola.
6. Comprobar: `.venv/bin/python3 tools/programar.py --cuentas`. LinkedIn sale como `linkedin` (perfil) y `linkedincompany` (página): pon la cuenta correcta en `publicar.yaml`.

**Programar:** `publicar.yaml` con las imágenes como archivos locales y `tools/programar.py` (ensayo, después `--confirmar`).
