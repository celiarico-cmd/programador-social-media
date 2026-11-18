# Programador de social media — instrucciones para Claude

Este repositorio permite a cualquier persona, también sin conocimientos técnicos, crear y programar sus posts de redes sociales desde una sola conversación: copy, imágenes, enlaces con UTMs, programación y calendario.

## Lo primero en cada conversación
Si la persona saluda, pregunta qué es esto o pide un post, ejecuta `python3 tools/estado.py` (o `.venv/bin/python3 tools/estado.py` si existe `.venv`).
- Si falta configuración, explícale en dos frases qué es esto y ofrece `/empezar`. No crees posts con la marca sin rellenar.
- Si está todo, ofrece `/nuevo-post`.

## Con quién hablas
Lo más probable es que la persona **no sea técnica**. Habla en español llano, una pregunta cada vez, y explica cualquier término la primera vez que salga. Tú instalas, ejecutas y escribes los archivos; ella decide.

## Cómo está organizado (arquitectura WAT)
- **Workflows** (`workflows/`): las instrucciones paso a paso de cada tarea. Léelas antes de hacerla, no trabajes de memoria.
- **Agentes**: tú coordinas. El copy lo escribe el subagente `copywriter` y las imágenes el subagente `disenador`.
- **Tools** (`tools/`): scripts de Python que hacen el trabajo repetible siempre igual. Se ejecutan con `.venv/bin/python3 tools/<script>.py`.

Si cada paso lo hiciera la IA a mano con un 90 % de acierto, tras cinco pasos estaríamos en un 59 %. Por eso lo repetible va en scripts.

| Tarea | Workflow | Script |
|---|---|---|
| Configurar todo | `workflows/configurar.md` (`/empezar`) | `estado.py`, `analizar_web.py`, `historial.py` |
| Crear un post | `/nuevo-post` | — |
| Copy | `workflows/copywriter.md` | — |
| Imágenes (en el chat, Canva o Figma) | `workflows/diseno.md`, `disenar_canva.md`, `disenar_figma.md` | `construir_visual.py`, `descargar.py`, `figma.py` |
| Plantilla nueva desde Figma/Canva/imágenes | `workflows/crear_plantilla.md` | `comparar_referencias.py`, `figma.py capas` |
| Programar | `workflows/programar.md` + `workflows/programadores/<nombre>.md` | `utm.py`, `subir_imagenes.py`, `programar.py` (API), `hootsuite_login.py` |
| Calendario (Notion, Sheets, Airtable, Trello…) | `workflows/calendario.md` | `calendario.py` |

## Dónde está cada cosa
- `marca/`: **de aquí beben los agentes**. `voz.md`, `hechos.md` (la única fuente de hechos), `guia_visual.md`, `posts_que_funcionan/`, `logos/`, `fuentes/`. `marca/_analisis/` guarda lo que se descargó de la web y de los posts.
- `plantillas/`: plantillas HTML de las imágenes. Colores y fuentes de la marca, solo en `_marca.css`.
- `config/ajustes.yaml`: programador, redes, imágenes, UTMs, Notion. Sin secretos.
- `.env`: las claves secretas. Nunca en otro sitio, nunca en el chat, nunca en git.
- `posts/<AAAA-MM-DD>_<slug>/`: cada post (brief, copy, fotos, visual, programado.json).

## Reglas que no se negocian
1. **Nunca se programa ni se publica nada sin el OK explícito de la persona en ese momento**, después de enseñarle el resumen (red, fecha y hora, texto, imágenes). Tampoco posts de prueba en la cuenta real: para probar, borradores.
2. **Nunca se toca lo que ya está programado** en su programador, ni una tarjeta existente de Notion, salvo que la persona dé el cambio exacto.
3. **Nunca se inventan fechas, cifras, nombres, citas ni enlaces.** Si falta, `[A CONFIRMAR]` y se pregunta.
4. **UTMs en todos los enlaces** (`tools/utm.py`).
5. **Las claves no se piden en el chat**: van a `.env`.
6. **Las URLs de las imágenes subidas son públicas desde la subida.** Una pieza que no pueda verse antes de tiempo no se sube antes de tiempo.
7. **Las fotos de los posts las da la persona.** Nunca fotos de banco ni generadas o recreadas con IA.
8. Si una herramienta de IA de imagen (ampliar, quitar fondo, generar) da un resultado con defectos, se enseña tal cual. Decide la persona.

## Aprender de cada corrección
Cada corrección de la persona va **al archivo que la aplica**, con fecha:
- copy y tono → `marca/voz.md` (sección 7)
- hechos sobre la marca → `marca/hechos.md`
- diseño → `marca/guia_visual.md` (y, con su OK, la plantilla)
- algo de un programador (un límite, un error, un truco) → `workflows/programadores/<nombre>.md`
Los agentes solo leen el repositorio: lo que no se apunta, se olvida.

Si un script falla: lee el error entero, arréglalo, pruébalo otra vez (si gasta dinero o publica algo, pregunta antes) y apunta lo aprendido en el workflow.
