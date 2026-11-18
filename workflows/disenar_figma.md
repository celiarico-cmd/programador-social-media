# Workflow: diseñar en Figma

Para quien ya diseña en Figma. Dos formas, que se pueden mezclar post a post:
- **Descargar**: la persona diseña y Claude exporta los frames a PNG para programarlos.
- **Rellenar**: Claude duplica el frame plantilla, cambia los textos (y la foto) y lo exporta.

## Antes de empezar: el plan de Figma
En el **plan gratuito** la API y el MCP de Figma dejan muy pocas llamadas al mes (unas 20): no da para el día a día. Hace falta un plan de pago con asiento **Full** o **Dev**. Dilo claro antes de elegir este modo.

## Conectar
- **Para exportar y leer capas (API):** Figma → Settings → Security → Personal access tokens → crear uno con permiso "File content: read" → `.env` → `FIGMA_TOKEN=`.
- **Para rellenar (MCP, opcional):** Ajustes → Conectores → Figma (o `claude mcp add --transport http figma https://mcp.figma.com/mcp`). Escribir en archivos necesita plan Professional o superior y permiso de edición. Antes de usar `use_figma`, carga el skill `figma:figma-use` si está disponible.

## Descargar lo que diseña la persona
1. Pide el enlace del frame (o del grupo de frames del carrusel): clic derecho → Copiar enlace.
2. Exporta:
   ```bash
   # un frame por slide, en orden
   .venv/bin/python3 tools/figma.py exportar "<url slide 1>" "<url slide 2>" --slug <slug> --carpeta posts/<slug>/visual/final
   # o un frame que contiene todas las slides
   .venv/bin/python3 tools/figma.py exportar "<url del contenedor>" --hijos --slug <slug> --carpeta posts/<slug>/visual/final
   ```
   `--escala 1` da el tamaño real del frame (si mide 1080 de ancho, sale a 1080). Si el frame es más pequeño, `--escala 2`.
3. Enseña la vista previa y sigue con `workflows/programar.md`.

Sin token: la persona exporta ella los PNG (Export → PNG) y los deja en `posts/<slug>/visual/final/`.

## Rellenar su plantilla (MCP)
1. La plantilla es un frame del archivo de la persona. Guarda su enlace en `marca/guia_visual.md → Plantillas de Figma`.
2. `tools/figma.py capas <url>` para ver qué capas son TEXTO y FOTO.
3. Con `use_figma`: duplicar el frame (`clone()`), ponerlo junto al original, cargar las fuentes y cambiar los textos (`characters`).
4. La foto: el MCP no añade imágenes nuevas por sí solo (Figma, nov-2026). Prueba `upload_assets` o, si no funciona, pide a la persona que arrastre la foto al hueco en el frame duplicado. **Apunta aquí lo que funcione.**
5. Exporta el frame duplicado con `tools/figma.py exportar` y revisa la imagen. Nunca toques el frame original.

## Lo que se aprende
Apunta aquí, con fecha, lo que descubras (límites, trucos, errores).
