# Workflow: programar un post

## Objetivo
Dejar programado en el programador de la persona un post **ya cerrado**: copy final, imágenes finales y fecha y hora confirmadas. Sin duplicar nada y sin tocar lo que ya esté programado.

## Reglas que no se negocian
1. **Nada se programa sin el OK explícito de la persona en ese momento**, después de enseñarle el resumen: red, cuenta, fecha y hora, texto completo e imágenes (la vista previa).
2. **Nunca se toca un post ya programado** (por la persona o por otro) salvo que ella dé el cambio exacto.
3. **Nunca se programa una prueba en la cuenta real.** Para probar, borrador (`borrador: true`) y se borra después desde el programador.
4. **Nunca se inventa la hora.** Se puede sugerir (algunos programadores dan la mejor hora), pero la elige la persona.
5. Si algo falla a medias, **antes de reintentar se comprueba qué se ha creado**. Máximo 2 reintentos.

## Proceso
1. **Comprobar que el post está cerrado**: `posts/<slug>/copy.md` con la variante elegida, imágenes en `posts/<slug>/visual/final/`, fecha y hora confirmadas, sin `[A CONFIRMAR]`.
2. **UTMs** en todos los enlaces, uno por red:
   ```bash
   .venv/bin/python3 tools/utm.py --red linkedin --campana <campaña> --contenido <slug> <url>
   ```
3. **Duplicados**: mirar lo programado en el programador ±3 días alrededor de la fecha y `posts/<slug>/programado.json`. Si ya existe, parar y avisar.
4. **Imágenes** (si el programador no las recibe él mismo):
   ```bash
   .venv/bin/python3 tools/subir_imagenes.py --slug <slug> posts/<slug>/visual/final/<slug>_0*.png --json posts/<slug>/imagenes.json
   ```
   En el orden del carrusel. Si una imagen cambia después de subirla, súbela con otro nombre (`_v2`): con el mismo nombre se devuelve la antigua.
5. **Resumen y OK**: enséñalo todo y espera el sí.
6. **Programar** según `workflows/programadores/<nombre>.md`.
7. **Apuntar** el id que devuelve el programador en `posts/<slug>/programado.json` (el script de API lo hace solo) y, si hay calendario, crear la entrada (`workflows/calendario.md`).

## Cosas que pasan en todas las redes
- **Instagram solo publica JPEG**: los scripts convierten los PNG solos.
- **Instagram necesita cuenta profesional** (Business o Creator) para publicar desde un programador.
- **Las stories con enlace** no se pueden publicar automáticamente con el sticker: la API de Instagram no lo permite. Se programan como recordatorio y la persona añade el enlace desde el móvil.
- **Los posts colaborativos** (coautores en LinkedIn o Instagram) normalmente solo se pueden crear desde la propia red.
- **Carruseles de documento en LinkedIn** (PDF): no todos los programadores los admiten. Míralo en el workflow de cada uno.
