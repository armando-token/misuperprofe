🧠 NOTA PARA CURSOR:

Este proyecto usa **FastMCP v2.0.4**, lanzado en abril 2025.  
Evita usar decoradores obsoletos como `@register_tool`, respuestas antiguas como `ToolResponse`, o estructuras de MCP anteriores a 2024.  
Consulta `memory_bank/tech_context.md` antes de generar código si tienes dudas sobre la versión.

La tarea debe ser compatible con esta versión actual del protocolo.

# 🛠 Tarea activa

## 🎯 Objetivo:
Implementar el recurso `/resource/metricas_por_materia` que devuelva un resumen por materia de lo que el alumno respondió correctamente o incorrectamente.

## 🔗 Dependencias:
- `models/resultado.py`
- `schemas/metricas.py`
- `db/session.py`
- Saber qué curso y materia están relacionados con cada pregunta.

## 🧩 Subtareas:
1. Crear esquema `MetricasPorMateria` con porcentaje, curso, correctas.
2. Agregar función agregada en SQLAlchemy con `group_by(curso, correcta)`.
3. Exponer en `resources/metricas.py` bajo `/resource/metricas_por_materia?alumno_id={id}`.
4. Probar con `curl` o `pytest`.

## ✅ Validación:
- `pytest tests/test_metricas.py`
- El endpoint devuelve algo como:
```json
[
  { "materia": "Biología", "aciertos": 12, "errores": 3 },
  { "materia": "Química", "aciertos": 5, "errores": 7 }
]