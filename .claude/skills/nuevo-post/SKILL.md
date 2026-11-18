---
name: nuevo-post
description: Crea un post de principio a fin desde el chat: brief, copy (agente copywriter), imágenes (agente disenador, en el chat, Canva o Figma), UTMs, subida de imágenes, programación en el programador de la persona y entrada en su calendario. Usar cuando digan "/nuevo-post", "quiero publicar…", "hazme un post de…", "programa un post".
---

Antes de nada, `.venv/bin/python3 tools/estado.py`. Si falta configuración, dilo y propón `/empezar`. No sigas con la marca a medias.

## 1. Brief (tú, con la persona)
Pregunta lo justo, de una en una: qué se cuenta, para qué (objetivo), en qué redes, si hay fotos (que las deje en el chat o en una carpeta) y cuándo se publica. Busca en `marca/hechos.md` lo que ya se sabe en vez de preguntarlo.

Crea `posts/<AAAA-MM-DD>_<slug>/brief.md` con los hechos y su fuente. Lo que falte, `[A CONFIRMAR]`. Las fotos, en `posts/<…>/fotos/`.

## 2. Copy → agente `copywriter`
Pásale la ruta del brief. Enseña a la persona las variantes y su recomendación. Itera con el agente hasta que elija.
Si la persona corrige algo que vale para el futuro, asegúrate de que queda apuntado en `marca/voz.md`.

## 3. Imágenes → agente `disenador`
(Si el post lleva imágenes.) Pásale la ruta del post y la variante elegida. Enseña la vista previa (`final/<slug>_vista.jpg`) con la herramienta Read y ofrece ver cada slide. Itera hasta el OK.

## 4. Cerrar
Escribe `posts/<…>/copy_final.md` con el texto final de cada red y los enlaces con UTMs (`tools/utm.py`). Confirma fecha y hora.

## 5. Programar
Sigue `workflows/programar.md` y `workflows/programadores/<programador>.md`. **Antes de programar, enseña el resumen completo y espera el sí explícito.**

## 6. Calendario y aviso
Si `calendario.herramienta` está relleno, crea la entrada (`workflows/calendario.md`). Si `avisos.slack_canal` está relleno, avisa al equipo.

## 7. Cierre
Una línea: qué se ha programado, dónde y para cuándo, y el id o enlace del programador.
