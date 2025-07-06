## Estructura de carpetas
- `app/` contiene routers, tools, models, db, config.
- `scripts/` carga Markdown y preguntas (montado en /app/scripts en Docker).
- `tests/` usa Pytest para endpoints.
- `content/{curso}/` contiene teoría (.md) y preguntas (.md o .csv).

## Convenciones
- Las rutas MCP se exponen con `/resource` y `/tool`.
- Toda teoría se consulta por `curso` y `capitulo`.
- Preguntas están asociadas a capítulos.

## Tips
- Nunca hard-codear dominios ni rutas.
- Las respuestas deben ser siempre en español.

## Cambios
- `content/{curso}/` contiene solo teoría (.md). No se deben crear archivos de preguntas manuales.
- Las preguntas se generan dinámicamente a partir de la teoría, no se almacenan manualmente.

## Nuevos patrones y robustez (mayo 2025)
- El motor semántico nunca debe devolver capítulos sin contenido: si el capítulo principal está vacío, busca el subcapítulo de definición general (por ejemplo, 'Definición de biología').
- Si existe un subcapítulo de definición, se prioriza como respuesta ante preguntas generales.
- Nunca modificar el texto ni la estructura de los archivos .md críticos; toda mejora se hace en la lógica o en la base de datos.