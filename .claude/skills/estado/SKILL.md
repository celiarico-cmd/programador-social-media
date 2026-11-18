---
name: estado
description: Dice qué está configurado, qué falta y cuál es el siguiente paso del programador de redes, y cuántas preguntas sobre la marca quedan abiertas. Usar cuando digan "/estado", "¿qué falta?", "¿por dónde iba?".
---

1. Ejecuta `.venv/bin/python3 tools/estado.py` (si no existe `.venv`, `python3 tools/estado.py`).
2. Si hay conectores MCP marcados con 🔎, compruébalos tú llamando a su herramienta de listar cuentas.
3. Resume en pocas líneas lo que está listo y lo que falta, en lenguaje llano.
4. Si hay preguntas abiertas en `marca/voz.md`, `marca/hechos.md` o `marca/guia_visual.md`, ofrece responder 2 o 3 ahora.
5. Propón el siguiente paso (`/empezar` si falta configuración; `/nuevo-post` si está todo).
