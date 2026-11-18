---
name: empezar
description: Configura el programador de redes paso a paso para una persona no técnica: instala lo necesario, conecta su programador (Metricool, Hootsuite, Zernio, Buffer o Postiz), lee sus posts publicados y su web, y escribe la voz y la guía visual de la marca. Usar cuando digan "/empezar", "empezar", "configurar", "montar el sistema", o cuando falte algo de la configuración.
---

Vas a configurar el sistema con la persona. Sigue `workflows/configurar.md` paso a paso; léelo completo antes de empezar.

1. Ejecuta `python3 tools/estado.py` (o `.venv/bin/python3 tools/estado.py` si ya existe `.venv`) para ver qué está hecho. Empieza por el primer paso pendiente; no repitas lo que ya está.
2. Saluda en una o dos frases: qué vais a hacer ("conectar tu programador, aprender cómo escribes a partir de lo que ya has publicado y preparar tus plantillas") y cuánto se tarda (unos 20-30 minutos). Se puede parar y seguir otro día.
3. Haz el Paso 0 (instalar) sin preguntar nada técnico: solo avisa de que tarda un par de minutos.
4. A partir de ahí, **una pregunta cada vez**, explicando para qué sirve cada paso en una línea.
5. Nunca pidas claves en el chat: van al archivo `.env`.
6. Al terminar cada paso, una línea de lo hecho. Al final, `tools/estado.py` y propón `/nuevo-post`.
