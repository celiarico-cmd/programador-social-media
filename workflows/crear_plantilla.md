# Workflow: crear una plantilla de la marca

## Objetivo
Convertir un diseño que la persona ya usa (en Figma, en Canva, en otra herramienta o en posts ya publicados) en una plantilla HTML de `plantillas/` que el diseñador rellena con cualquier texto y foto, siempre igual.

## La clave: qué cambia y qué se repite
En una pieza de redes, **lo que cambia en cada post** suele ser la **foto** y el **texto**: serán los campos de la plantilla. **Lo que se repite** (el fondo, los degradados, las formas, el logo, los márgenes, las etiquetas fijas) va dentro de la plantilla y no se toca.

Hay que saberlo antes de dibujar nada, de la forma más fiable que se tenga:

| Lo que hay | Cómo se separa | Fiabilidad |
|---|---|---|
| **Frame de Figma** | `tools/figma.py capas <url>`: cada capa dice si es FOTO (relleno de imagen), TEXTO, DEGRADADO (con sus colores exactos), FORMA o VECTOR | exacta |
| **Diseño de Canva** | `get-design-dataset` (Pro: campos con nombre, imagen o texto) y `read-design` para el resto | buena para foto y texto; degradados por confirmar |
| **Solo imágenes** (Canva sin Pro, otra herramienta, posts publicados) | `tools/comparar_referencias.py` con **2-3 piezas de la misma familia**: lo que difiere entre ellas es variable (foto o texto), lo que coincide es fijo; además detecta degradados y sus colores | buena; revisar siempre a ojo |

Pide siempre **2 o 3 ejemplos de la misma pieza con textos y fotos distintos**. Con uno solo no se puede saber qué es fijo.

## Proceso
1. **Separar** fijo y variable con la tabla de arriba.
   - `comparar_referencias.py` deja `mapa.png` (rojo = foto, azul = texto, verde = fijo) en `marca/_analisis/plantillas/<nombre>/`. Míralo (Read).
   - Límite: si la foto ocupa toda la pieza, el texto que va encima queda dentro de la zona "foto". Sepáralo mirando la imagen.
   - Un texto que es igual en todas las piezas (el nombre de una serie, "Nuevo episodio") sale como fijo: decide con la persona si debe ser un campo.
2. **Confirmar con la persona** en una lista corta: "Campos que cambian: foto (abajo, 70 % del ancho), nombre, cargo, número. Fijo: fondo con degradado verde #0B3532 → #020606, etiqueta 'The Podcast', flecha." Corrige lo que diga.
3. **Medir lo fijo**: tamaño, márgenes, tipografía y tamaño de cada texto, colores y degradados (de Figma, exactos; de imagen, los que da el análisis, comprobados con un cuentagotas en Python/PIL).
4. **Partir de la plantilla más parecida** de `plantillas/` (cópiala con un nombre nuevo, p. ej. `plantillas/podcast.html`). Mantén:
   - el bloque `esquema` con `descripcion`, `formatos`, `obligatorios` (los campos variables) y `opcionales`;
   - los marcadores `/*CSS*/`, `/*JS*/` y `/*DATOS*/{}`, y `listo()` al final.
5. **Lo fijo en CSS** usando las variables de `_marca.css` (`var(--color-acento)`, `var(--fuente-titulos)`…) siempre que coincidan. Degradados con `linear-gradient` o `radial-gradient` y sus colores medidos. Las formas sencillas, en CSS. Las ilustraciones, texturas o formas complejas, exportadas de Figma o Canva a `marca/` (SVG o PNG) y puestas como imagen fija.
6. **Comparar**: construye la plantilla con los mismos textos y la misma foto de una de las referencias y pon las dos imágenes una al lado de la otra. Ajusta hasta que coincidan. Enséñaselo.
7. **Probar con casos extremos**: titular muy corto y muy largo, foto vertical y horizontal. Si se rompe, limita el texto en la `descripcion` del campo o ajusta tamaños.
8. **Documentar** en `workflows/diseno.md → Plantillas` una línea con su nombre y para qué sirve.

## Reglas
- El logo, siempre de `marca/logos/`: nunca dibujado a mano ni recreado en CSS.
- Nunca se cambia una plantilla existente sin el OK de la persona: afecta a todos los posts futuros.
- Composiciones complicadas (recortes de personas, máscaras, fundidos sobre partes de la foto): mejor prepararlas en Python/PIL y que el HTML solo ponga el texto encima. Las máscaras CSS en el navegador sin ventana no siempre salen igual.
- Si la persona prefiere seguir diseñando en Canva o Figma, no hace falta plantilla HTML: ver `workflows/disenar_canva.md` o `workflows/disenar_figma.md`.
