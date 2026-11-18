# Workflow: diseñar en Canva

Para quien ya diseña en Canva. Dos formas, que se pueden mezclar post a post:
- **Rellenar**: Claude copia la plantilla de Canva de la persona, cambia la foto y los textos y exporta los PNG.
- **Descargar**: la persona diseña ella misma y Claude solo descarga los PNG para programarlos.

## Conectar
- **Claude (web o escritorio):** Ajustes → Conectores → Canva → iniciar sesión.
- **Claude Code:** `/mcp` y añadir el servidor de Canva si no aparece.

Qué deja hacer cada plan (documentación de Canva, nov-2026):
| | Gratis | Pro, Business, Enterprise |
|---|---|---|
| Copiar, editar (textos, cambiar foto) y exportar PNG | ✅ calidad estándar | ✅ calidad máxima |
| Rellenar por campos con nombre (autofill, plantillas de marca) | ❌ | ✅ |
| PNG con fondo transparente | ❌ | ✅ |

Comprobar: `search-designs` encuentra sus diseños.

## Descargar lo que diseña la persona
1. Pide el enlace del diseño (Compartir → Copiar enlace) o su nombre, y búscalo con `search-designs` (o `resolve-shortlink` si es un enlace corto).
2. `get-export-formats` para ver qué admite y luego `export-design` en **PNG**, con `width: 1080` y, si tiene Pro, `export_quality: "pro"`. Si el carrusel tiene varias páginas, todas en orden.
3. **Descarga en el momento** (los enlaces caducan en 24 h):
   ```bash
   .venv/bin/python3 tools/descargar.py --slug <slug> --carpeta posts/<slug>/visual/final <url1> <url2> …
   ```
4. Enseña `final/<slug>_vista.jpg` y sigue con `workflows/programar.md` como cualquier post.

Si no quiere conectar Canva, puede descargar ella los PNG (Compartir → Descargar → PNG) y dejarlos en `posts/<slug>/visual/final/`.

## Rellenar su plantilla
1. **La plantilla**: el diseño de Canva que usa como base para ese tipo de post. Su enlace se guarda en `marca/guia_visual.md → Plantillas de Canva` (nombre, para qué sirve, enlace, qué campos tiene).
2. **Subir la foto** del post: tiene que estar en una URL pública. Súbela con `tools/subir_imagenes.py` y luego `upload-asset-from-url` → `asset_id`.
3. **Con autofill (Pro)**, si la plantilla tiene los campos con nombre: `get-design-dataset` (o `get-brand-template-dataset`) para ver los campos y `autofill-design` con los textos y el `asset_id`. Devuelve un diseño nuevo.
4. **Sin autofill**: `copy-design` (nunca edites el original) → `edit-design` en una transacción abierta (`keep_open`):
   - textos: `replace_text` en cada caja (o `find_and_replace_text` si la plantilla tiene textos de ejemplo fijos, como "TITULAR");
   - foto: `update_fill` del elemento de imagen con el `asset_id`;
   - enseña la vista previa y, **con el OK**, `commit`. Si no, `cancel`.
5. Exporta y descarga como en "Descargar".
6. **Revisa siempre la imagen descargada** (Read): textos que no caben, foto mal encuadrada. Si algo falla, se ajusta en Canva o se avisa a la persona; no se "arregla" por fuera.

## Lo que se aprende
Apunta aquí, con fecha, lo que descubras: qué campos tiene cada plantilla, límites del conector, errores (`license_required` = un elemento de pago en una cuenta sin Pro).
