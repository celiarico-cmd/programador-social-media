# Workflow: copywriter

## Objetivo
Escribir el copy de un post para cada red y los textos que van dentro de las imágenes, a partir de un brief con hechos reales. Entrega **3 variantes** para la red principal, la adaptación a las demás redes y los textos de slide en `posts/<slug>/copy.md`. Nunca programa: eso lo hace `/nuevo-post` cuando la persona elige.

## Lectura obligatoria (en cada post, no de memoria)
1. `marca/hechos.md`: lo que no esté ahí ni en el brief no se afirma.
2. `marca/voz.md`: entero, incluidas las correcciones aprendidas (sección 7) y las preguntas abiertas.
3. `marca/posts_que_funcionan/`: para coger el tono y ver qué ha funcionado, **no para copiar frases**. Fíjate sobre todo en "Por qué funcionó".
4. `posts/<slug>/brief.md`.
5. Si la marca ya ha publicado posts parecidos (misma serie, mismo tipo), el último publicado: el gancho tiene que ser distinto.

## Inputs (el brief)
- Qué se cuenta y para qué (objetivo del post).
- **Hechos con fuente**: nombres, cargos, fechas, cifras, citas literales y enlaces.
- Redes y formato previsto (carrusel, imagen única, solo texto).
- Fecha de publicación (o `[A CONFIRMAR]`).

Si falta un hecho que el post necesita, se escribe `[A CONFIRMAR: qué falta]` en el sitio exacto y se pregunta. **Nunca se rellena con algo plausible.**

## Principio: primero el gancho y la historia, después el dato
1. **Gancho**: una afirmación o una escena, en 15 palabras como mucho, que pare el scroll de alguien que no conoce la marca. Sin jerga del sector.
2. **Historia**: una persona o una situación concreta. Frases cortas, una idea por línea.
3. **Dato al final**, sosteniendo la historia.

Antes de entregar: *¿se lee como una historia que alguien elegiría seguir leyendo, o como un resumen?* Si es lo segundo, reescribe.

### El corte del "…ver más"
En el móvil solo se ven los primeros **~140 caracteres** en LinkedIn y **~125** en Instagram. Ese trozo tiene que abrir una pregunta que se responde justo después del corte. La palabra técnica o de nicho va después del corte, no antes.

### Fórmulas de IA prohibidas
Delatan un texto automático y la gente deja de leer:
- "No es X, es Y" y sus variantes: como mucho una vez por post.
- Tríadas ("rápido, sencillo y eficaz") y listas de tres por costumbre.
- Preguntas retóricas como primera línea ("¿Alguna vez te has preguntado…?").
- Arranques de manual: "En el mundo actual…", "En [marca] creemos que…", "Hoy queremos compartir…".
- Cierres de moraleja genérica ("Porque al final, lo que importa es…").
- Palabras infladas: "revolucionario", "potenciar", "sinergia", "apasionante", "viaje".
- Emojis como viñetas en cada línea.
En su lugar: una escena corta y un cierre práctico.

### Otras reglas
- La marca no es la protagonista del gancho ni del cierre: se habla del cliente, del lector o de la persona del post.
- No adornes un dato para que suene mejor. Si el brief dice "visitó a 3 clientes", no es "recorrió el país".
- **Etiquetas**: toda persona o empresa que salga en el copy y tenga perfil se marca con `@Nombre` en el borrador. La sintaxis de cada programador se pone al programar.
- **Un solo CTA.** El enlace se marca como `[ENLACE: destino]`. Dónde va (cuerpo, primer comentario, "enlace en la bio") lo dice `marca/voz.md`.

## Proceso
1. **Leer** todo lo de "Lectura obligatoria".
2. **Idioma**: el de `config/ajustes.yaml → marca.idioma`, salvo que el brief diga otro.
3. **Tres variantes** para la red principal, con ganchos distintos: A historia, B cita real (si la hay) o dato, C afirmación fuerte o anuncio. Largo y hashtags según `marca/voz.md`.
4. **Adaptación a las demás redes** de la variante A (o de la que la persona prefiera). Cada red, nativa: no un recorte de la otra.
5. **Textos de slide** para el diseñador: una fila por campo, con la plantilla prevista (`.venv/bin/python3 tools/construir_visual.py --lista`) y `**negrita**` en la idea clave. Portada: 2-3 líneas. Slides de texto: 60 palabras como mucho.
6. **Autorrevisión** con la checklist. Si algo falla, reescribe antes de entregar.
7. **Entregar** `copy.md` y recomendar una variante en una línea.

## Formato de `copy.md`
```markdown
# <Título del post> — copy v1 (<fecha>)
Redes: LinkedIn, Instagram · Idioma: es · Formato: carrusel 4:5

## Variante A — historia
<copy>
Caracteres: <n>

## Variante B — cita / dato
…
## Variante C — afirmación / anuncio
…

## Instagram (adaptación de A)
<caption>
<hashtags>

## Textos de slide
| # | Plantilla | Campo | Texto |
|---|---|---|---|
| 1 | portada | titulo | Nadie te enseña a **esperar** |

## Recomendación
<variante y motivo en una línea>

## Pendiente de confirmar
- [ ] …
```

## Checklist antes de entregar
- [ ] Todo nombre, cifra, fecha, cita y enlace sale del brief o de `marca/hechos.md`.
- [ ] Los primeros ~140 caracteres abren una pregunta y se entienden sin contexto.
- [ ] Ninguna fórmula de IA de la lista.
- [ ] Un solo CTA. Enlaces marcados como `[ENLACE: …]`.
- [ ] Largo, emojis y hashtags según `marca/voz.md` para cada red.
- [ ] Ninguna corrección de la sección 7 de `marca/voz.md` se ha vuelto a cometer.
- [ ] Los textos de slide caben (portada ≤ 3 líneas).

## Cuando la persona corrige
Cada corrección que valga para otros posts se apunta con fecha en `marca/voz.md → 7. Correcciones aprendidas`, en una línea y con el porqué. Si es un hecho nuevo, va a `marca/hechos.md`. Así no vuelve a pasar.
