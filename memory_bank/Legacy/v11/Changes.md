# [REGLA DE ORO CRÍTICA - NUNCA HARDCODEAR LOCALHOST NI OBSESIONARSE CON EL PUERTO 8000]

- Nunca hardcodear 'localhost' en endpoints, variables de entorno, ni en ningún archivo de configuración o código. Siempre usar variables de entorno, nombres de servicio Docker, o la IP/host configurada para el entorno real.
- Nunca obsesionarse ni forzar el uso del puerto 8000. El puerto debe ser configurable y nunca asumido como libre o universal. Antes de usarlo, verificar que no esté ocupado por Docker u otro proceso.
- Toda referencia a endpoints (API, backend, runtime, etc.) debe ser SIEMPRE configurable y nunca fija en el código.
- Esta regla es obligatoria y debe revisarse antes de cualquier despliegue, troubleshooting o refactor.

# [PRIORIDAD JULIO 2025] Plan de alineación arquitectónica con OpenAI Custom GPTs/MCP Server

## Resumen
- OpenAI ya resolvió muchos problemas arquitectónicos: separación de responsabilidades, uso de schema OpenAPI, instrucciones estrictas, encapsulamiento del LLM, discovery automático, etc.
- Nuestra arquitectura es buena, pero debemos alinearnos más estrictamente a estos patrones para evitar ambigüedad y errores históricos.

## Reglas y patrones clave a implementar
- Exponer y consumir un schema OpenAPI real y actualizado en el MCP Server.
- Limitar al LLM y al frontend a solo usar los endpoints definidos en el schema.
- Encapsular el LLM en el backend: nunca debe acceder a la base de datos ni a funciones internas, solo a los endpoints.
- Versionar y documentar las instrucciones para el LLM, igual que OpenAI.
- Implementar discovery automático de tools/endpoints (ej: /mcp/schema).
- Estandarizar las respuestas: siempre estructuradas según el schema.
- Centralizar la autenticación y los headers en el schema y en la lógica del runtime/frontend.
- Mejorar logs y trazabilidad para cada request, error y decisión.

## Tabla comparativa (OpenAI vs. nosotros)
| Aspecto                        | OpenAI Custom GPT + MCP Server         | Nuestra arquitectura actual                | ¿Qué mejorar?                          |
|--------------------------------|----------------------------------------|-------------------------------------------|-----------------------------------------|
| Interfaz de chat               | Custom GPT                             | CopilotKit                                | OK                                      |
| Orquestador (LLM)              | GPT-4o, solo orquesta                  | LLM integrado, a veces con más acceso     | Encapsular y limitar                    |
| Schema OpenAPI                 | Obligatorio, actualizado               | Existe, pero no siempre usado             | Exponer y consumir siempre              |
| Instrucciones                  | Versionadas, estrictas                 | A veces manuales                          | Versionar y documentar                  |
| Llamadas a endpoints           | Solo lo definido en schema             | Puede llamar a cualquier función          | Limitar a schema                        |
| Acceso a base de datos         | Solo backend, nunca LLM                | A veces LLM puede acceder                 | Encapsular LLM                          |
| Autenticación                  | Centralizada en schema                 | Manual o por endpoint                     | Unificar y documentar                   |
| Respuestas                     | Siempre estructuradas                  | A veces libres                            | Estandarizar                            |
| Discovery de tools             | Automático                             | Manual o parcial                          | Implementar discovery                   |
| Logs y trazabilidad            | Exhaustivos                            | Buenos, pero mejorables                   | Añadir más trazabilidad                 |

## Próximos pasos
1. Exponer un schema OpenAPI real y actualizado en el MCP Server.
2. Limitar al LLM y frontend a solo usar los endpoints definidos en el schema.
3. Encapsular el LLM en el backend.
4. Versionar y documentar instrucciones.
5. Implementar discovery automático de tools/endpoints.
6. Estandarizar respuestas.
7. Centralizar autenticación y headers.
8. Mejorar logs y trazabilidad.

---

# [RESUMEN CRÍTICO JULIO 2025]

## Estado actual, logros, errores a evitar y próximos pasos

- Arquitectura: Frontend (React/Vite + CopilotKit), Copilot Runtime, Backend LangGraph/FastAPI, Backend MCP Server (FastAPI), PostgreSQL, Redis, WordPress (autenticación).
- Principios de oro: Nunca duplicar lógica, nunca cargar toda la base de datos en el LLM, toda la lógica de búsqueda/matching en el backend, el agente LangGraph solo orquesta y muestra, autenticación propagada por headers personalizados, documentar todo.
- Logros: Servicios estructurados y funcionales, autenticación robusta con contraseñas de aplicación WP, tools del agente usan solo endpoints inteligentes, endpoints de cursos y teoría funcionales, checklist de arranque documentado, incidentes de memoria resueltos, historial de mensajes recortado, propagación de usuario validada.
- Errores a evitar: No crear endpoints CRUD para el LLM, no replicar lógica de negocio, no modificar sin revisar documentación, no sobrescribir código probado, no buscar/filtrar en toda la base de datos desde el LLM, documentar cada cambio.
- Próximos pasos: Verificar flujo de autenticación end-to-end, probar flujo completo desde frontend, limpiar código redundante, solucionar persistencia de Redis, reforzar seguridad de headers, documentar todo, pruebas exhaustivas antes de refactor.
- Checklist de arranque: Parar/levantar contenedores, verificar puertos, arrancar servicios, probar acceso externo, diagnóstico rápido si falla algo.

---

# Historial de Cambios y Pruebas - Diagnóstico Endpoints MCP Server

## Contexto Inicial (26 de junio de 2025)
- Problema: El chat responde a "hola" y lista cursos, pero falla al consultar capítulos o temas. El agente LangGraph y el frontend funcionan, pero los endpoints REST del MCP Server (FastAPI) parecen ser el cuello de botella.
- Objetivo: Diagnóstico quirúrgico y registro detallado de cada prueba/cambio para evitar repeticiones y pérdida de contexto.
- Archivo creado para control absoluto: `memory_bank/Changes.md`.

## Pruebas y Cambios Realizados

### [1] Verificación de estado de contenedores Docker
- Comando: `docker compose ps`
- Resultado: Todos los servicios principales arriba y saludables.

### [2] Revisión de logs recientes del MCP Server
- Comando: `docker compose logs web --tail=100`
- Resultado: Error de conexión a la base de datos PostgreSQL (intentando conectar a localhost:5432).

### [3] Prueba manual del endpoint /ask desde el contenedor
- Comando: `curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"query": "fotosíntesis"}'`
- Resultado: Fallo de conexión (no responde el endpoint).

### [4] Revisión de configuración de variables de entorno y docker-compose
- Se detecta que el archivo .env existe y fue editado por el usuario, con DB_HOST=db y POSTGRES_DATABASE_URL usando db como host.
- Sin embargo, el error persiste y el MCP Server sigue intentando conectar a localhost:5432.

### [5] Reinicio del servicio web (MCP Server)
- Comando: `docker compose restart web`
- Resultado: El error de conexión a la base de datos persiste.

### [6] Búsqueda de referencias a 'localhost' en el código Python
- Herramienta: grep en todos los archivos *.py
- Hallazgos:
  - Referencias directas a 'http://localhost:8000/ask', 'http://localhost:8000/api/lesson/start', etc. en:
    - app/agents_langgraph_example/agent.py (líneas 93, 115, 142, 175)
    - app/agents/main_agent.py (línea 215)
  - Esto puede estar forzando la conexión a endpoints REST en localhost en vez de usar el nombre de servicio Docker ('web' o la IP interna del contenedor).
- Acción siguiente: Proponer refactor para que las URLs de los endpoints REST usen una variable de entorno o settings, y apunten a la dirección correcta según el entorno (por ejemplo, 'web' o una variable configurable).

### [7] Plan de refactor y prueba manual de endpoints REST
- Acción planificada:
  1. Hacer que las URLs de los endpoints REST sean configurables mediante una variable de entorno (ej: MCP_SERVER_URL).
  2. Modificar todas las herramientas del agente para que usen esta variable en vez de la URL fija con localhost.
  3. Probar el flujo de /ask y otros endpoints usando la nueva configuración.
- Antes de modificar el código, haré una prueba manual cambiando la URL en una herramienta para usar 'http://web:8000/ask' (nombre de servicio Docker) y ver si responde correctamente.

### [8] Prueba manual: cambio temporal de URL en get_theory_for_topic_tool
- Se modificó la función get_theory_for_topic_tool en app/agents_langgraph_example/agent.py para usar 'http://web:8000/ask' en vez de 'http://localhost:8000/ask'.
- Próximo paso: Probar el flujo del chat (preguntar por un tema/capítulo) y observar si el endpoint responde correctamente.
- Si funciona, se procederá a refactorizar todas las herramientas para usar una variable de entorno/configuración.

### [9] Ciclo de pruebas completo tras cambio a localhost
- Se cambiaron todas las URLs de los endpoints REST en las tools del agente a 'http://localhost:8000/...'.
- Se detuvieron todos los procesos previos con `pkill -f "pnpm|python|uvicorn|tsx"`.
- Se levantaron los servicios uno a uno:
  - Frontend: `cd ~/frontend-chat && pnpm install && pnpm run dev -- --host 0.0.0.0 --port 5174`
  - Copilot-runtime: `cd ~/copilot-runtime && pnpm install && pnpm run dev -- --host 0.0.0.0 --port 4000`
  - Backend LangGraph: `cd ~ && poetry install && poetry run python3 app/langgraph_server_example.py`
- Se verificó con `sudo ss -tulpen | grep -E '5174|4000|8001'` que los tres puertos están en estado LISTEN.
- El frontend carga y responde a "hola", pero sigue mostrando error al pedir la lista de cursos o teoría de un tema.
- El log del backend LangGraph muestra: `Error en list_available_courses_tool: [Errno -3] Temporary failure in name resolution`.
- Esto confirma que, aunque los servicios están levantados y los puertos abiertos, el agente sigue sin poder resolver el host de la API MCP Server desde el contenedor/host.
- El problema persiste tras múltiples ciclos de reinicio y verificación.

### [10] Hallazgo crítico: endpoints inexistentes
- Se confirmó que los endpoints `/ask` y `/api/courses` NO existen en el backend FastAPI (MCP Server).
- Las tools del agente intentan llamar a estos endpoints y por eso reciben `404 Not Found`.
- El único router montado en la app principal es `agent_router.py`, que solo expone `/agent/chat`.
- Los endpoints de lecciones existen bajo `/lesson`, pero requieren autenticación y no son equivalentes.
- El problema NO es de Docker Compose, puertos ni red, sino de endpoints REST faltantes.
- Próximo paso: crear endpoints mínimos `/ask` y `/api/courses` en el backend para que el agente funcione y avanzar con las pruebas.

### [11] Hallazgo de rutas reales y error de prefijo
- Tras revisión exhaustiva, se detectó que los endpoints realmente expuestos por FastAPI son `/api/v1/ask` y `/api/v1/api/courses` (por el prefijo settings.API_V1_STR en main.py).
- Las tools del agente estaban llamando a `/ask` y `/api/courses` (o `/agent/ask`), lo que causaba el error 404.
- El backend y los endpoints están bien definidos y el contenedor arranca sin errores críticos.
- Próximo paso: corregir las URLs en las tools del agente para que apunten a `/api/v1/ask` y `/api/v1/api/courses`.

### [RESUMEN] Solución al problema de cursos vacíos y lecciones aprendidas (junio 2025)

**Problema:**
- El endpoint `/api/courses` devolvía una lista vacía aunque la carpeta `/content` sí tenía cursos reales.
- El agente y el frontend solo mostraban datos simulados o vacíos.

**Causas:**
- El volumen `./content:/app/content` no estaba explícitamente montado en Docker Compose, así que el contenedor backend no veía los datos reales.
- El endpoint calculaba la ruta a `/content` de forma dinámica usando `os.path.dirname(__file__)`, lo que puede fallar en Docker.

**Solución aplicada:**
1. Se añadió el volumen explícito `./content:/app/content` en el servicio backend de Docker Compose.
2. Se cambió el endpoint `/api/courses` para usar la ruta absoluta `/app/content`.
3. Se verificó desde dentro del contenedor que `/app/content` existe y contiene los cursos.
4. El endpoint `/api/v1/api/courses` ahora devuelve correctamente los cursos reales.

**Errores a evitar:**
- No asumir que `.:/app` monta todo lo necesario; montar explícitamente carpetas críticas.
- No usar rutas relativas complejas en producción; preferir rutas absolutas y claras.
- Siempre verificar acceso a datos desde dentro del contenedor, no solo en el host.
- Documentar cada hallazgo y cambio para evitar repeticiones y pérdida de contexto.

---

**Nota:** Este archivo se actualizará después de cada prueba, cambio de configuración o hallazgo relevante para mantener un control absoluto y evitar repeticiones o pérdida de contexto.

### [LECCIÓN APRENDIDA] Principio de arquitectura MCP Server: Endpoints inteligentes y orquestación LLM (junio 2025)

- El MCP Server (FastAPI) debe exponer solo unos pocos endpoints inteligentes: `/ask`, `/api/lesson/start`, `/api/lesson/answer`, `/api/lesson/complete`, etc.
- El agente LLM (LangGraph) solo debe llamar a estos endpoints y nunca replicar lógica de negocio, búsqueda o matching.
- No se deben crear endpoints CRUD para cada acción (ej: `/api/courses`, `/api/chapters`, etc.), salvo para administración o necesidades reales del backend.
- El LLM nunca debe intentar buscar, filtrar o cargar toda la base de datos, ni hacer lógica pesada: solo orquesta y presenta la información que le devuelve el backend.
- Ejemplo de error a evitar: crear un endpoint `/api/chapters` solo para que el LLM liste capítulos, cuando el backend ya puede devolver el fragmento relevante vía `/ask`.
- Flujo correcto: el usuario pide teoría o pregunta, el LLM llama a `/ask` o `/api/lesson/start`, el backend responde con el bloque relevante, el LLM lo presenta según el contexto.
- Documentar y revisar siempre este principio antes de crear nuevas tools o endpoints.

---

### [12] Hallazgo y solución de conflicto de contenedores Docker (junio 2025)
- Problema: Al reiniciar servicios, Docker arrojó error de conflicto por el contenedor 'misuperredis' ya existente.
- Solución: Se eliminó el contenedor en conflicto con `docker rm -f misuperredis` y se levantaron todos los servicios de nuevo con `docker compose up -d`.
- Todos los servicios (PostgreSQL, Redis, backend, frontend, copilot-runtime) quedaron en estado 'Up' y 'healthy'.
- Se validó que el archivo `.env` estaba correctamente montado y las variables de entorno eran correctas.
- Se comprobó que la red Docker y la resolución de nombres funcionan correctamente.
- Se recomienda SIEMPRE eliminar contenedores en conflicto antes de levantar servicios y esperar a que todos estén 'healthy' antes de arrancar el backend LangGraph.
- Estado actual: El chat funciona parcialmente (responde a saludos y algunas preguntas), pero no al 100%. Persisten errores al listar cursos o consultar teoría en algunos flujos.
- Próximo paso: Seguir depurando el flujo de tools del agente y endpoints REST para lograr funcionalidad completa.

### [13] Hallazgo: No existe endpoint REST para capítulos (junio 2025)
- Se confirmó que el backend solo expone los endpoints: /api/v1/agent/chat, /api/v1/agent/health, /api/v1/api/courses y /api/v1/ask.
- No existe endpoint para listar capítulos de un curso, por lo que la tool list_chapters_for_course_tool siempre dará error 404.
- Se decidió comentar/eliminar la tool de capítulos y dejar solo tools que usen endpoints inteligentes.
- Recomendación: El LLM debe consultar teoría o fragmentos usando /ask y nunca intentar listar capítulos directamente.
- Documentado para evitar que se repita este error en el futuro.

---

# [PLAN DE ARRANQUE PRIORITARIO JULIO 2025]

## Orden recomendado para arrancar el sistema y evitar caídas

1. **Encapsulamiento estricto del LLM en el backend**
   - El LLM solo puede interactuar con la base de datos y lógica de negocio a través de endpoints definidos, nunca funciones internas ni acceso directo a datos.
2. **Exponer y consumir un schema OpenAPI real y actualizado**
   - El frontend, runtime y LLM deben estar limitados a los endpoints definidos en el schema. Esto elimina ambigüedad y previene errores de integración.
3. **Estandarizar las respuestas del backend**
   - Todas las respuestas de los endpoints deben seguir el formato definido en el schema OpenAPI. No devuelvas respuestas libres ni HTML sin estructura.
4. **Centralizar la autenticación y los headers**
   - Define en el schema cómo se autentica cada endpoint. El runtime y el frontend deben enviar siempre los headers correctos.
5. **Mejorar logs y trazabilidad**
   - Añade logs detallados en cada request, error y decisión importante en backend y runtime.
6. **Implementar discovery automático de tools/endpoints**
   - Expón un endpoint `/mcp/schema` o similar para que el frontend/LLM descubra automáticamente las tools disponibles.
7. **Versionar y documentar instrucciones**
   - Versiona y documenta las instrucciones para el LLM y el frontend, y mantenlas sincronizadas con el schema.

## Motivo del orden
- Los primeros 4 pasos son críticos para evitar caídas, errores graves y ambigüedad en el flujo.
- Los últimos 3 son mejoras importantes para la extensibilidad, mantenimiento y robustez futura, pero no bloquean el arranque inmediato.

---

# [PLAN DE ACCIÓN JULIO 2025: Integración correcta de tools LangGraph y MCP Server]

## Contexto
- El LLM (LangGraph Agent) **NO accede ni procesa la base de datos directamente**.
- El LLM solo orquesta la conversación y llama a tools que hacen peticiones HTTP a los endpoints inteligentes del MCP Server (FastAPI).
- **Toda la lógica pesada** (búsqueda semántica, matching, scoring, recuperación de teoría, etc.) la hace el MCP Server a través de endpoints como `/ask`, `/api/lesson/start`, `/api/lesson/answer`, `/api/lesson/complete`.
- El LLM nunca debe replicar lógica de negocio, ni buscar, filtrar o cargar toda la base de datos.
- El frontend solo muestra lo que el LLM responde, y la autenticación se propaga por headers personalizados.

## Flujo correcto (resumido)
1. Usuario → Frontend (React/CopilotKit)
2. Frontend → Copilot Runtime (pasa headers de autenticación)
3. Copilot Runtime → Backend LangGraph (LLM agent)
4. LLM agent (LangGraph) → llama a tools (solo orquesta, NO busca ni filtra)
5. Tools → llaman a endpoints inteligentes del MCP Server (FastAPI)
6. MCP Server → hace toda la lógica pesada y responde con el fragmento relevante
7. LLM agent → da formato y responde al usuario

## Plan de acción (Julio 2025)

### 1. Auditoría de tools del agente LangGraph
- Revisar que **todas** las tools solo hagan peticiones HTTP a los endpoints inteligentes del MCP Server.
- Eliminar/comentar cualquier tool que:
  - Intente buscar, filtrar o procesar datos localmente.
  - Llame a endpoints CRUD o no inteligentes.
  - Intente replicar lógica de negocio.

### 2. Validación de rutas y configuración
- Verificar que las URLs de los endpoints en las tools:
  - Usan variables de entorno/configuración.
  - Apuntan a los endpoints correctos (`/ask`, `/api/lesson/start`, etc.).
  - No hay hardcodeo de `localhost` o rutas erróneas.

### 3. Pruebas end-to-end
- Simular flujos reales desde el frontend y verificar:
  - Que el LLM solo orquesta y nunca responde directamente con datos de la base.
  - Que las respuestas provienen del MCP Server.
  - Que no hay errores de integración ni duplicación de lógica.

### 4. Documentación y checklist
- Dejar documentado (en `Changes.md` y/o `copilot.md`) el estado de cada tool y el flujo validado.
- Checklist para futuros cambios:
  - ¿La tool solo llama a un endpoint inteligente?
  - ¿No hay lógica de negocio replicada?
  - ¿El LLM nunca accede a la base de datos ni filtra datos?

### 5. Investigación de patrones modernos (Julio 2025)
- Buscar si existen plugins, middlewares o patrones recientes para:
  - Service discovery automático de endpoints en LangGraph.
  - API Gateway/proxy para centralizar rutas y autenticación.
  - Observabilidad y tracing para detectar errores de integración.

## Próximo paso inmediato
- Auditar las tools del agente LangGraph para asegurar que cumplen con este flujo y reportar exactamente cuáles cumplen y cuáles no, SIN modificar nada aún.
- Registrar aquí el resultado de la auditoría y los siguientes pasos.

---

## [AUDITORÍA DE TOOLS DEL AGENTE LANGGRAPH - JULIO 2025]

### Tools activas y su análisis:

1. **list_available_courses_tool**
   - ✅ Solo llama a endpoint inteligente `/api/v1/api/courses` (POST).
   - No filtra ni busca localmente, solo orquesta y presenta.
   - Cumple el flujo correcto.

2. **list_chapters_for_course_tool**
   - ⚠️ Llama a `/api/v1/api/courses/{course_name}/chapters` (GET).
   - Según la documentación y el propio código, **NO existe este endpoint REST** en el MCP Server.
   - Está comentada en la lista de tools activas (`tools = [...]`).
   - **NO debe usarse**. Correctamente deshabilitada.

3. **get_theory_for_topic_tool**
   - ✅ Llama a `/api/v1/ask` (POST), endpoint inteligente.
   - No busca ni filtra localmente, solo presenta el fragmento recibido.
   - Cumple el flujo correcto.

4. **start_practice_lesson_tool**
   - ✅ Llama a `/api/v1/api/lesson/start` (POST), endpoint inteligente.
   - Usa el estado para user_id y chapter_id, no filtra ni busca localmente.
   - Cumple el flujo correcto.

5. **submit_answer_tool**
   - ✅ Llama a `/api/v1/api/lesson/answer` (POST), endpoint inteligente.
   - Usa el estado para user_id, session_id, item_id, no filtra ni busca localmente.
   - Cumple el flujo correcto.

6. **complete_lesson_tool**
   - ✅ Llama a `/api/v1/api/lesson/complete` (POST), endpoint inteligente.
   - Usa el estado para user_id, session_id, no filtra ni busca localmente.
   - Cumple el flujo correcto.

### Tools deshabilitadas o de ejemplo:
- `your_tool_here`: Solo ejemplo, no está activa.
- `list_chapters_for_course_tool`: Correctamente deshabilitada.

### Validación de rutas y configuración:
- Las tools usan variables de entorno (`MCP_SERVER_URL`) o rutas absolutas (`http://localhost:8000/...`).
- **Recomendación:** Unificar todas las URLs para que usen la variable de entorno `MCP_SERVER_URL` y evitar hardcodeo de `localhost`.
- Todas las tools activas llaman a endpoints inteligentes existentes.

### Conclusión de la auditoría:
- ✅ Todas las tools activas cumplen el flujo correcto: solo orquestan, no replican lógica, no acceden a la base de datos ni filtran localmente.
- ⚠️ Mejorar la consistencia de las URLs usando siempre la variable de entorno.
- 🟢 Se puede proceder a pruebas end-to-end y a la investigación de patrones modernos para service discovery/API Gateway si se desea mayor robustez.

---

# [INVESTIGACIÓN Y RECOMENDACIONES JULIO 2025: Integración moderna de agentes LangGraph/MCP]

## 1. Patrones y tecnologías actuales (Junio-Julio 2025)
- **MCP (Model Context Protocol)** es el nuevo estándar abierto para conectar agentes LLM con herramientas externas, resolviendo el problema MxN de integraciones personalizadas. Permite que el agente descubra y use tools de forma plug-and-play, con seguridad (OAuth 2.1) y descripciones enriquecidas de cada tool.
- **Service Discovery/API Gateway:** Se recomienda usar un API Gateway (ej: Traefik, Kong, Azure API Management) para exponer todos los endpoints inteligentes del MCP Server bajo un único dominio, facilitando el descubrimiento y la gestión de rutas, autenticación y rate limiting.
- **Orquestación de tools:** LangGraph soporta flujos cíclicos y persistentes, permitiendo que el agente coordine múltiples tools (vía MCP) en workflows complejos, sin replicar lógica de negocio.
- **Ecosistema MCP:** Grandes proveedores (OpenAI, Google, Microsoft, Vercel, Cloudflare, Stripe) ya soportan MCP, y existen SDKs oficiales para Python, TypeScript, Java, Go, Rust, C#.

## 2. Recomendaciones para MiSuperProfe
- **Implementar un MCP Server** (si no existe) en el MCP Server (FastAPI), exponiendo los endpoints inteligentes como tools MCP, usando el SDK oficial de Anthropic para Python.
- **Actualizar el agente LangGraph** para que actúe como MCP Client, descubriendo y usando tools vía handshake MCP, en vez de hardcodear endpoints.
- **Centralizar rutas y autenticación** usando un API Gateway delante del MCP Server, facilitando service discovery y control de acceso.
- **Documentar y versionar cada tool** expuesta vía MCP, usando descripciones enriquecidas y scopes de permisos.
- **Evitar cualquier lógica de negocio en el LLM:** El agente solo debe orquestar tools, nunca filtrar, buscar ni acceder a la base de datos directamente.
- **Aprovechar el ecosistema MCP:** Reutilizar MCP servers existentes (ej: GitHub, Stripe, Google Drive) si se requieren integraciones externas.

## 3. Plan de pruebas end-to-end (sin repetir lo ya hecho)
- [ ] Validar que todas las tools activas del agente usan solo endpoints inteligentes vía MCP (no REST directo ni lógica local).
- [ ] Simular workflows complejos (ej: consulta, inicio de lección, respuesta, cierre) y verificar que el LLM solo orquesta, sin lógica de negocio.
- [ ] Probar la resiliencia ante errores de tools (timeouts, respuestas inválidas) y que el agente maneja los fallos correctamente.
- [ ] Medir la latencia y robustez del flujo completo (LLM → MCP Client → MCP Server → Backend).
- [ ] Revisar logs y trazabilidad de cada tool call para auditoría y debugging.

## 4. Referencias y fuentes (Junio-Julio 2025)
- [Model Context Protocol (MCP) - Anthropic, OpenAI, Google, Microsoft, Stripe, Cloudflare, Vercel]
- [Restack: Reliable agentic workflows]
- [Microsoft: Baseline Agentic AI Systems Architecture]
- [Medium/Dev.to: FastAPI MCP Server, OAuth2, Service Discovery]
- [modelcontextprotocol.org]

---

# [ACTUALIZACIÓN CRÍTICA JULIO 2025: Logros y avances en integración MCP Server]

## Logros recientes
- Se expuso correctamente el endpoint `/mcp/schema` en el MCP Server (FastAPI), permitiendo discovery automático de tools y resources por agentes externos (LangGraph, CopilotKit, etc.).
- Se implementó un método `get_schema` que recorre dinámicamente los endpoints registrados y construye un schema MCP moderno, incluyendo nombre, path, método, descripción y parámetros de cada resource/tool.
- Se diagnosticó y solucionó el problema de que el router MCP no estaba montado en la app principal (`main.py`), lo que impedía el acceso real al endpoint en producción.
- Se documentó la importancia de exponer solo endpoints inteligentes y discovery automático, evitando la duplicación de lógica y los errores históricos de endpoints CRUD o hardcodeados.
- El sistema ahora es extensible: cualquier nueva tool/resource registrada aparecerá automáticamente en el schema MCP.

## Errores evitados y lecciones aprendidas
- No asumir que los endpoints están expuestos solo por definirlos: siempre verificar el montaje del router en la app principal.
- No confiar en métodos stub de paquetes externos: es mejor sobrescribir y construir el schema MCP manualmente si es necesario.
- Documentar cada cambio y validación en este archivo para evitar repeticiones y pérdida de contexto.

## Próximos pasos
- Enriquecer el schema MCP para incluir también las tools (POST) y sus metadatos.
- Validar la integración end-to-end con el agente LangGraph como MCP Client real.
- Mantener este archivo actualizado tras cada avance relevante.

---

# [ACTUALIZACIÓN CRÍTICA JULIO 2025: Diagnóstico y acciones sobre schema MCP]

## Estado actual
- El endpoint `/mcp/schema` responde correctamente y expone los resources (endpoints inteligentes tipo GET).
- Las tools decoradas con `@mcp.tool()` aún NO aparecen en el schema, a pesar de importar explícitamente los módulos y resolver dependencias (`matplotlib`, `seaborn`).
- Se resolvieron errores de ciclo de importación moviendo los imports de tools a `main.py` tras montar los routers.
- El sistema es robusto ante dependencias externas, pero el discovery MCP de tools requiere revisión adicional.

## Buenas prácticas y errores evitados
- Importar los módulos de tools explícitamente tras montar los routers para evitar ciclos de importación.
- Instalar todas las dependencias requeridas por las tools para evitar fallos en el arranque del backend.
- Documentar cada error y solución para evitar repeticiones.

## Próximos pasos
- Auditar el decorador `@mcp.tool()` y el registro de tools en la instancia MCP.
- Corregir el registro para que las tools aparezcan en el schema MCP y el discovery sea completo.
- Documentar el resultado y actualizar el checklist de integración MCP.

---

# [ACTUALIZACIÓN CRÍTICA JULIO 2025: Discovery MCP de tools resuelto]

## Logros
- El endpoint `/mcp/schema` ahora expone correctamente las tools decoradas con `@mcp.tool()` junto a los resources.
- Se implementó un fallback robusto para obtener el nombre de la tool decorada, resolviendo el AttributeError y permitiendo el discovery automático.
- El backend arranca limpio y sin errores críticos.
- El sistema está listo para integración avanzada del agente LangGraph como MCP Client y para pruebas end-to-end del flujo MCP.

## Buenas prácticas y lecciones aprendidas
- Siempre validar el tipo de objeto decorado y usar fallbacks para extraer metadata.
- Documentar cada fix y mantener el control de cambios para evitar repeticiones.

## Próximos pasos
- Integrar el agente LangGraph como MCP Client real.
- Realizar pruebas end-to-end del flujo MCP.
- Documentar resultados y checklist de integración.

---

# [ACTUALIZACIÓN JULIO 2025: INTEGRACIÓN MCP SERVER Y FLUJO END-TO-END]

## Estado actual y logros recientes
- Integración completa del endpoint `/tool/{tool_name}` en el MCP Server (FastAPI), permitiendo la ejecución dinámica de tools decoradas con `@mcp.tool()`.
- Resolución automática de dependencias (como la sesión de base de datos) y serialización robusta de cualquier objeto retornado por las tools.
- Pruebas end-to-end exitosas: el agente LangGraph puede invocar tools MCP vía HTTP y obtener respuestas reales desde la base de datos PostgreSQL.
- El sistema es extensible: nuevas tools aparecen automáticamente en el schema MCP y pueden ser invocadas dinámicamente.

## Lecciones aprendidas y errores evitados
- Nunca modificar el `.env` desde código; toda la lógica debe adaptarse a los valores universales definidos ahí.
- Validar y serializar cualquier objeto retornado por las tools antes de exponerlo vía HTTP.
- No duplicar lógica de negocio ni crear endpoints CRUD innecesarios.
- Documentar cada cambio, error y solución para evitar repeticiones y pérdida de contexto.

## Próximos pasos
- Probar el flujo completo desde frontend y validar la experiencia de usuario.
- Poblar más datos de ejemplo si es necesario para pruebas funcionales.
- Reforzar la seguridad de headers y autenticación.
- Limpiar código redundante y actualizar la documentación tras cada cambio relevante.

---

# [JULIO 2025] Auditoría de headers personalizados: el backend registra los headers de usuario (`X-Wordpress-User-ID`, `X-Wordpress-Display-Name`) en cada petición, asegurando trazabilidad y seguridad en el flujo end-to-end.

### [INCIDENTE CRÍTICO JULIO 2025: Caída de copilot-runtime por OOM, swap y política de puertos]
- El 25 de junio de 2025, copilot-runtime fue matado por el sistema (exit code 137) por falta de memoria (OOM), no por conflicto de puertos.
- El cambio de endpoint a `localhost:8000` contribuyó si el backend no estaba disponible, pero el detonante fue el consumo excesivo de memoria y la ausencia de swap.
- Se resolvió creando y activando un archivo de swap de 2GB, estabilizando todos los servicios.
- **Nueva política:** Nunca usar siempre el mismo puerto para todo. Verificar disponibilidad antes de lanzar servicios. Implementar manejo de errores y timeouts. Monitorear memoria y swap. Usar gestor de procesos para reinicio automático.
- **Advertencia:** No asumir la causa de un incidente sin evidencia. Revisar logs, uso de recursos y documentar el diagnóstico real.

### [JULIO 2025] Creación de script automático de checklist de arranque y prevención de caídas
- Se crea un script bash (`checklist_arranque.sh`) para automatizar la verificación de swap, puertos libres y arranque seguro de servicios críticos (ej. copilot-runtime).
- Motivo: Evitar caídas por falta de memoria (OOM), conflictos de puertos y procesos caídos, que han ocurrido repetidamente en el pasado.
- El script verifica:
  1. Que el swap esté activo y suficiente.
  2. Que el puerto requerido esté libre antes de arrancar el servicio.
  3. Que el servicio se arranque con PM2 para reinicio automático.
- El script se guardará en la raíz del proyecto como `checklist_arranque.sh` y se documenta aquí como vestigio y prueba de buenas prácticas DevOps.
- Fecha de creación: julio 2025.
- Objetivo: Minimizar el riesgo de caídas inesperadas y facilitar la recuperación rápida.

### [JULIO 2025] Automatización total del checklist de arranque
- El script `checklist_arranque.sh` ahora automatiza completamente:
  1. La creación y activación de swap (mínimo 1GB) si no existe.
  2. La instalación automática de PM2 si no está presente.
  3. El arranque seguro de copilot-runtime con PM2.
- Motivo: Evitar olvidos humanos y garantizar que nunca falte swap ni gestor de procesos, minimizando el riesgo de caídas por OOM o procesos caídos.
- Fecha: julio 2025.
- Documentado en todos los historiales relevantes.

### [JULIO 2025] Workaround técnico: endpoint /copilotkit/info en runtime
- Se agregó un handler para /copilotkit/info en copilot-runtime, que responde con un JSON vacío (actions: []).
- Motivo: CopilotKit frontend requiere este endpoint para inicializarse, aunque la lógica de negocio real está en el backend LangGraph/MCP Server.
- No expone datos ni lógica de negocio, solo compatibilidad técnica.
- Documentado para dejar constancia y evitar confusiones futuras.

# [ACTUALIZACIÓN CRÍTICA - 28 JUNIO 2025]

## Estado actual del sistema
- El runtime (copilot-runtime) muestra el mensaje 'Listening at http://0.0.0.0:4000/copilotkit' pero el proceso muere inmediatamente después, por lo que el puerto 4000 nunca queda disponible.
- El frontend intenta conectarse a http://18.214.59.62:4000/copilotkit pero recibe ERR_CONNECTION_REFUSED.
- El backend MCP Server y el frontend están correctamente configurados y exponen los endpoints necesarios.

## Diagnóstico
- El runtime no está corriendo realmente, o se cae justo después de arrancar.
- No hay proceso escuchando en el puerto 4000 (verificado con lsof y curl).
- El error de arranque solo se puede ver ejecutando el runtime en primer plano.

## Plan de depuración para mañana
1. Ejecutar el runtime en primer plano y observar los logs en tiempo real.
2. Corregir cualquier error de crash inmediato (por ejemplo, dependencias, errores de código, conflictos de puerto).
3. Verificar que el proceso se mantenga vivo y el puerto 4000 esté abierto.
4. Probar el flujo end-to-end desde el frontend y documentar cualquier hallazgo.

---

# [ACTUALIZACIÓN JULIO 2025: Corrección de endpoints, diagnóstico OOM y plan de ampliación de memoria]

## Cambios recientes (no documentados previamente)

### 1. Corrección de configuración en frontend y runtime
- Se detectó que el frontend `chat-frontend-react` usaba un endpoint legacy (`/agent/chat`) en vez de `/copilotkit`.
- Se modificó el archivo `src/App.tsx` para que `<CopilotKit runtimeUrl="http://localhost:4000/copilotkit" ... />` apunte correctamente al runtime.
- Se corrigió el archivo `copilot-runtime/server.ts` para que la URL de `remoteEndpoints` apunte a `http://localhost:8000/copilotkit` (backend real), en vez de `8001`.
- Ambas correcciones alinean el flujo con el estándar MCP/OpenAI y permiten discovery automático de tools/actions.

### 2. Intentos de arranque y diagnóstico
- Se intentó reiniciar ambos servicios con PM2, pero no estaban gestionados por PM2.
- Se revisaron los scripts de arranque en `package.json` de ambos proyectos:
  - Runtime: `pnpm run dev` (usa `tsx server.ts`)
  - Frontend: `npm run dev` (usa Vite)
- Se intentó arrancar ambos servicios manualmente en segundo plano, redirigiendo logs a archivos para trazabilidad.
- El runtime (`copilot-runtime`) falló con exit code 137 (`ELIFECYCLE`), típico de procesos terminados por falta de memoria (OOM).
- El frontend no generó log, lo que indica que probablemente tampoco arrancó correctamente o el comando no se ejecutó en la ruta adecuada.
- Se verificó el uso de memoria: solo 590 MiB libres y 1.5 GiB de swap disponible.
- No se detectaron procesos Node.js activos del runtime ni del frontend tras los intentos de arranque.

### 3. Diagnóstico y decisión
- El runtime fue terminado por el sistema por falta de memoria (OOM), no por conflicto de puertos ni errores de código.
- El frontend tampoco está corriendo, probablemente por falta de recursos o error de ruta.
- Se documenta que no se debe reintentar el arranque hasta ampliar la memoria, siguiendo la política de checklist y swap documentada en este archivo.

### 4. Próximo paso: ampliación de memoria
- El usuario va a ampliar la memoria del servidor antes de reintentar el arranque de servicios.
- Se recomienda, tras la ampliación:
  1. Verificar swap y memoria (`free -h`).
  2. Ejecutar el script `checklist_arranque.sh` (si existe) o manualmente:
     - Verificar swap activo y suficiente.
     - Verificar puertos libres.
     - Arrancar runtime y frontend con PM2 para reinicio automático.
     - Revisar logs y documentar cualquier incidente.

### 5. Estado actual
- Todos los cambios y diagnósticos han sido documentados.
- El sistema está listo para reintentar el arranque seguro tras la ampliación de memoria.
- Se mantiene la trazabilidad y alineación con el estándar MCP/OpenAI.

---

# [JULIO 2025] Cambio temporal en /copilotkit y /copilotkit/info para compatibilidad CopilotKit

- Se modificó app/main.py para que los endpoints /copilotkit y /copilotkit/info filtren los parámetros no serializables (por ejemplo, 'fn' y tipo 'Callable[..., Any]') de la lista de actions.
- Motivo: CopilotKit rechaza actions con parámetros complejos/no serializables, lo que causaba el error "Failed to find any agents" en el frontend.
- Ahora solo se exponen parámetros simples (string, int, float, bool) o la lista queda vacía si no hay parámetros válidos.
- Impacto: El frontend detecta correctamente al menos una action/agent y desaparece el error 500.
- Este cambio es temporal y debe revisarse si se modifica la estructura de tools o se agregan nuevas tools en el backend.

---

# [JULIO 2025] Cambio estructural en /copilotkit y /copilotkit/info para compatibilidad total CopilotKit/AG-UI

- Se modificaron los endpoints /copilotkit y /copilotkit/info para devolver la estructura esperada por CopilotKit/AG-UI:
  - Ahora la respuesta incluye un objeto 'agents' con un agente 'default' (id, name, description, actions).
  - Se añade el campo 'defaultAgent' con el valor 'default'.
  - El array 'actions' de cada agente contiene solo acciones válidas, con todos los campos requeridos (name, description, parameters, path, method).
- Motivo: CopilotKit requiere explícitamente la presencia de 'agents' y 'defaultAgent' para registrar agentes y evitar el error 'Failed to find any agents'.
- Impacto: El frontend ya no muestra el error 500 de agentes no encontrados, pero puede mostrar errores si la estructura de 'actions' no es válida o si hay campos undefined/null.
- Relación: Este cambio es una continuación del fix anterior (filtrado de parámetros no serializables) y es obligatorio para la compatibilidad con versiones recientes de CopilotKit/AG-UI.

---

### [JULIO 2025] Fix crítico en runtime CopilotKit: remoteEndpoints apunta a backend correcto

- Se corrigió `copilot-runtime/server.ts` para que la URL de `remoteEndpoints` apunte a `http://localhost:8000/copilotkit` (antes: IP pública).
- Motivo: El backend LangGraph/FastAPI expone `/copilotkit/info` en el puerto 8000, y el runtime debe descubrir los agentes y actions ahí.
- Se respeta la regla de oro: nunca hardcodear IPs públicas ni obsesionarse con el puerto 8000; la URL debe ser configurable y documentada.
- Este cambio soluciona el error `TypeError: Cannot read properties of undefined (reading 'map')` causado por respuestas vacías al consultar el puerto incorrecto.

---

# [JULIO 2025] Diagnóstico y trazabilidad automática de integración CopilotKit/MCP

## Pruebas y hallazgos recientes (automatizados)

- Se detectó que el runtime CopilotKit recibía requests del frontend pero el backend MCP no registraba ningún request nuevo.
- Se verificó que el backend MCP Server está escuchando correctamente en el puerto 8000 y responde a `/copilotkit/info` con código 200 y la estructura esperada.
- Se comprobó que la configuración de `remoteEndpoints` en el runtime apunta a la IP pública correcta del backend (`http://18.214.59.62:8000/copilotkit`).
- Se probó la conectividad real con `curl` y el backend responde correctamente desde la máquina local.
- Se intentó registrar una action manualmente en el runtime, pero la versión 1.8.13 de CopilotKit **no soporta `registerAction`** (solo discovery automático MCP).
- Se forzaron logs detallados en el runtime y backend para trazar cada request y payload.
- Se detectó que el runtime recibía y logueaba los POST/OPTIONS del frontend, pero **no reenviaba ni procesaba ninguna action** porque no había ninguna registrada ni discovery efectivo.
- Se identificó que el puerto 4000 quedó ocupado por un proceso Node.js zombie; se liberó de forma segura tras identificar el PID.
- Se confirmó que el runtime depende 100% del discovery automático de actions vía `/copilotkit/info`.
- El backend expone correctamente las actions, pero el runtime (versión 1.8.13) no las expone al frontend/chat, probablemente por un bug o incompatibilidad fina.
- Se documentó cada fix y hallazgo para evitar repeticiones y pérdida de tiempo en futuras sesiones.

## Estado actual
- El flujo frontend → runtime → backend está alineado a nivel de red y endpoints.
- El runtime recibe requests pero no expone ni reenvía actions al frontend/chat.
- El backend responde correctamente a requests directos y expone el discovery MCP.
- El sistema es robusto a nivel de logs y trazabilidad, pero persiste el bug de integración runtime/actions.

## Próximo paso recomendado
- Revisar si hay una versión más reciente de CopilotKit runtime que solucione el bug de discovery MCP.
- Si no, reportar el bug a CopilotKit con toda la evidencia y logs.
- No repetir pruebas ya documentadas; consultar este bloque antes de cualquier troubleshooting futuro.

---

# [JULIO 2025] Hallazgos críticos y reglas de oro sobre puertos y procesos

## Hallazgos recientes
- El error "address already in use" en el puerto 8000 fue causado por procesos `docker-proxy` (Docker) ocupando el puerto, no por un proceso Python/Uvicorn directo.
- El runtime CopilotKit y el backend MCP Server no pueden compartir el mismo puerto si uno está en Docker y otro en el host.
- El backend no estaba realmente escuchando en localhost:8000 porque el puerto ya estaba ocupado por Docker.
- El runtime CopilotKit no podía hacer discovery MCP porque el backend no respondía en `/copilotkit/info`.
- Redis no estaba disponible, pero esto solo afecta el checkpointing, no el arranque básico del backend.
- El error de "Failed to fetch CopilotKit agents/action information" en el runtime es síntoma de que el backend no está accesible en el puerto configurado.

## Reglas de oro (actualizadas)
- **Nunca matar procesos a ciegas ni "aplastar" puertos sin identificar el proceso y su dueño.**
- Siempre usar `sudo lsof -i :<puerto>` para identificar el proceso antes de liberar el puerto.
- Si el puerto está ocupado por Docker, reiniciar el contenedor correspondiente, no matar procesos del host.
- Documentar cada hallazgo y cambio en este archivo antes de repetir troubleshooting.
- Consultar este archivo antes de hacer troubleshooting de puertos, procesos o servicios.

## Procedimiento seguro para liberar puertos y reiniciar servicios
1. Identificar el proceso con `sudo lsof -i :<puerto>`.
2. Si es Docker, usar `docker ps` y `docker restart <container>`.
3. Si es un proceso del host, confirmar que no es crítico antes de matar.
4. Solo después de liberar el puerto, arrancar el servicio necesario.

## Estado actual
- El backend MCP Server no puede arrancar en el puerto 8000 porque Docker ya lo está usando.
- El runtime CopilotKit no puede hacer discovery MCP ni exponer actions.
- El frontend sigue sin responder porque el flujo MCP está roto en la capa de red/proceso.

## Próximo paso recomendado
- Identificar el contenedor Docker que usa el puerto 8000 y reiniciarlo correctamente.
- No intentar arrancar Uvicorn en el host mientras Docker tenga el puerto.
- Documentar cualquier cambio o hallazgo nuevo aquí antes de repetir troubleshooting.

---

## [JULIO 2025] Estado actual de puertos y servicios (auditoría de seguridad y trazabilidad)

| Puerto | Servicio/Sistema         | Origen (host/docker) | Observaciones                      |
|--------|--------------------------|----------------------|------------------------------------|
| 80     | nginx (HTTP)             | host                 | Expuesto a internet                |
| 443    | nginx (HTTPS)            | host                 | Expuesto a internet                |
| 22     | SSH                      | host                 | Expuesto a internet                |
| 5432   | PostgreSQL               | docker (misuperpostgre) | Expuesto a internet (0.0.0.0)  |
| 6379   | Redis                    | docker (misuperredis)  | Expuesto a internet (0.0.0.0)  |
| 8000   | FastAPI MCP Server       | docker (misuperapi)     | Expuesto a internet (0.0.0.0)  |
| 8081   | WordPress                | docker (wordpress_misuperprofe) | Expuesto a internet (0.0.0.0) |
| 5174   | Vite React App           | host                 | Expuesto a internet                |
| 4000   | (libre, reservado CopilotKit Runtime) | host | Permitido en AWS SG, sin proceso activo |
| 8001   | (reservado LangGraph)    | host/docker          | Permitido en AWS SG, sin proceso activo |
| 3306   | MariaDB                  | docker (mariadb_misuperprofe) | Solo interno docker         |

### Contenedores Docker activos y puertos expuestos

| Contenedor              | Puertos expuestos                      |
|------------------------|----------------------------------------|
| misuperapi             | 0.0.0.0:8000->8000/tcp                 |
| wordpress_misuperprofe | 0.0.0.0:8081->80/tcp                   |
| mariadb_misuperprofe   | 3306/tcp (solo interno)                |
| misuperredis           | 0.0.0.0:6379->6379/tcp                 |
| misuperpostgre         | 0.0.0.0:5432->5432/tcp                 |

- El puerto 4000 está libre y permitido en el Security Group de AWS, reservado para CopilotKit Runtime.
- El puerto 8001 está permitido pero actualmente libre.
- Esta tabla debe consultarse antes de exponer o reasignar cualquier puerto en el futuro.

---

# [JULIO 2025] Prueba y despliegue del starter oficial CopilotKit (coagents-starter)

- Se clonó el repositorio oficial de CopilotKit en `/home/ubuntu/copilotkit-starter`.
- Se eligió el ejemplo `coagents-starter` (carpeta `examples/coagents-starter/ui`) como base para la prueba comparativa.
- Se instalaron todas las dependencias con `pnpm install` en la carpeta `ui`.
- Motivo: Comparar el comportamiento del starter oficial con la integración propia, descartar problemas de entorno y verificar compatibilidad real con la última versión de CopilotKit.
- Próximos pasos: Arrancar el frontend del starter, probar el flujo de chat y documentar diferencias o errores respecto a la integración personalizada.
- Esta entrada garantiza trazabilidad total de experimentos y evita repeticiones o pérdida de contexto en el futuro.

---

# [PLAN DE PRUEBA Y DIAGNÓSTICO MCP/CopilotKit - MAÑANA]

## Objetivo
- Comparar el comportamiento del starter oficial de CopilotKit (`coagents-starter`) con la integración personalizada actual.
- Determinar si el error de discovery de agentes/actions es reproducible en el starter oficial o solo ocurre en la integración propia.
- Descubrir si el problema es de entorno, configuración, versión o integración MCP.

## Pasos a seguir
1. Arrancar el frontend del starter oficial (`coagents-starter/ui`) con `pnpm dev` o el comando recomendado en el README.
2. Probar el flujo de chat básico y verificar si el agente responde correctamente a mensajes simples (ej: "hola").
3. Revisar los logs del starter y comparar con los de la integración propia.
4. Documentar cualquier diferencia, error o éxito en la integración MCP/discovery de agents/actions.
5. Si el starter funciona bien, comparar configuraciones, dependencias y estructura de endpoints con la integración propia para aislar la causa raíz.
6. Si el starter falla igual, reportar el bug a CopilotKit con toda la evidencia y logs.

## Criterios de éxito
- El starter debe mostrar el chat funcional y discovery automático de agentes/actions sin errores 500 ni mensajes de "Failed to find any agents".
- Si el starter falla igual, se confirma bug de CopilotKit o incompatibilidad de entorno.
- Si el starter funciona, se debe aislar y corregir la diferencia en la integración propia.

## Notas
- No modificar nada en la integración propia hasta terminar la prueba comparativa.
- Documentar cada hallazgo y resultado en este archivo antes de avanzar.
- Este plan garantiza que mañana se retome el trabajo con el contexto completo y sin pérdida de información.

### 23. Estabilización Final y Puesta en Marcha del Sistema de Chat Completo (Julio 2025)

**Contexto:** Tras reestructurar la aplicación basándose en el ejemplo funcional `minimal-copilotkit-langgraph`, el sistema arrancaba los tres servicios (frontend, runtime, backend) pero el chat seguía sin funcionar. Se inició una fase final de depuración intensiva para estabilizar la comunicación entre los componentes.

**Resumen Cronológico de la Depuración Final:**

1.  **Diagnóstico del Error `AGENT_NOT_FOUND`:**
    *   **Síntoma:** El frontend cargaba, pero al enviar un mensaje, la consola de red del navegador mostraba un error `AGENT_NOT_FOUND`.
    *   **Causa:** Se descubrió que el frontend en `frontend-chat/src/App.tsx` todavía estaba configurado para solicitar el agente por defecto del ejemplo (`sample_agent`), mientras que nuestro backend (`app/langgraph_server_example.py`) había sido modificado para exponer un agente llamado `misuperprofe_agent`.
    *   **Solución:** Se modificó `frontend-chat/src/App.tsx` para que el componente `<CopilotSidebar>` solicitara explícitamente `misuperprofe_agent`.

2.  **Diagnóstico del Error `Invalid adapter configuration` en el Runtime:**
    *   **Síntoma:** Tras corregir el nombre del agente, el runtime (`copilot-runtime`) comenzó a fallar, mostrando un error de `Invalid adapter configuration`.
    *   **Causa:** El `CopilotRuntime` en `copilot-runtime/server.ts` se había inicializado vacío, sin un `serviceAdapter` que le indicara cómo comunicarse con un servicio de LLM (como OpenAI).
    *   **Solución (en varios pasos):**
        1.  **Validación de la API Key de OpenAI:** Para descartar problemas de conectividad o de clave, se creó un script temporal (`test-openai.ts`) que confirmó que la `OPENAI_API_KEY` era válida y que el servidor podía conectarse a la API de OpenAI.
        2.  **Implementación del Adaptador:** Se modificó `copilot-runtime/server.ts` para importar y utilizar el `OpenAIAdapter`, pasándolo en la configuración del `CopilotRuntime`.
        3.  **Resolución de Carga de API Key:** El runtime seguía sin encontrar la `OPENAI_API_KEY`. Se diagnosticó que `dotenv` no estaba buscando el archivo `.env` en el directorio raíz del proyecto. Se corrigió la configuración de `dotenv` en `copilot-runtime/server.ts` para que cargara `../../.env`.

3.  **Diagnóstico del Error `net::ERR_CONNECTION_REFUSED` en el Frontend:**
    *   **Síntoma:** Con el runtime ya configurado correctamente, el navegador empezó a mostrar un error `net::ERR_CONNECTION_REFUSED` en la consola, indicando que el frontend (en el puerto `5174`) no podía conectarse al runtime (en el puerto `4000`).
    *   **Causa:** Este es un error clásico de **CORS (Cross-Origin Resource Sharing)**. El servidor del runtime (un origen distinto al del frontend) no estaba configurado para aceptar peticiones desde el origen del frontend.
    *   **Solución:**
        1.  Se instaló el middleware `cors` en el directorio `copilot-runtime` (`pnpm add cors` y `pnpm add -D @types/cors`).
        2.  Se importó y configuró `cors` en `copilot-runtime/server.ts` para permitir explícitamente las peticiones desde cualquier origen (`app.use(cors())`), resolviendo así el bloqueo del navegador.

4.  **Limpieza y Éxito Final:**
    *   Se eliminó el archivo de API obsoleto `app/api/agent_chat.py` que correspondía a la implementación anterior y causaba confusión.
    *   Se eliminó el script de prueba `copilot-runtime/test-openai.ts`.
    *   Se ejecutó el comando `pnpm run start:all` desde el directorio raíz (`/home/ubuntu`).
    *   **Resultado:** ¡Éxito total! Los tres servicios se iniciaron correctamente. El frontend pudo conectarse al runtime (gracias a CORS), el runtime pudo conectarse al backend (puerto `8001`), el agente correcto (`misuperprofe_agent`) fue invocado, y el runtime pudo usar el `OpenAIAdapter` (gracias a la API key cargada) para procesar la solicitud. El chat se volvió plenamente funcional.

**Estado Final:**
El sistema de chat completo es estable y operativo. La arquitectura de tres componentes está correctamente interconectada y configurada, sentando una base sólida para futuras ampliaciones.

---

### 24. Re-arquitectura del Agente a un Modelo de Tool Única y Diagnóstico de Errores Posteriores (Julio 2025)

**Contexto:** A pesar de la estabilización inicial, el agente no se comportaba como se esperaba, lo que llevó a una re-arquitectura fundamental y a una nueva serie de depuraciones.

**Resumen Cronológico:**

1.  **Error de Arquitectura y Re-diseño:**
    *   **Problema:** Se detectó que el agente intentaba llamar a endpoints específicos para cada acción (ej. `/api/v1/cursos/`), lo cual era ineficiente, no escalable y contrario a la filosofía de tener un backend inteligente.
    *   **Solución:** Se reescribió por completo `app/agents_langgraph_example/agent.py` para usar una **única herramienta inteligente**: `ask_mcp_server_tool`. Esta herramienta toma la consulta en lenguaje natural del usuario y la envía al endpoint `/ask` del MCP Server, que se encarga de toda la lógica de negocio. Se añadió un `SystemMessage` para guiar al LLM sobre cómo y cuándo usar esta herramienta.

2.  **Diagnóstico del Error `AttributeError: add_conditional_edge`:**
    *   **Síntoma:** Tras el rediseño, el servidor del agente se caía al iniciar.
    *   **Causa:** Un simple error tipográfico en `agent.py`: se usó `add_conditional_edge` (singular) en lugar del método correcto `add_conditional_edges` (plural).
    *   **Solución:** Se corrigió el nombre del método.

3.  **Diagnóstico del Error `ValueError: No checkpointer set`:**
    *   **Síntoma:** El agente arrancaba pero se caía en la primera interacción que requería mantener el estado de la conversación.
    *   **Causa:** Al reescribir el agente, se omitió configurar un `checkpointer` en la compilación del grafo de LangGraph. El checkpointer es esencial para que el grafo pueda guardar y recuperar el estado de la conversación.
    *   **Solución:** Se importó `InMemorySaver` y se añadió a la compilación del grafo: `graph = graph_builder.compile(checkpointer=InMemorySaver())`.

**Estado Final (Actual):**
El agente ahora opera bajo una arquitectura robusta y escalable con una única `tool` inteligente. Se han resuelto los errores críticos de implementación que impedían su funcionamiento. El sistema está listo para una nueva ronda de pruebas funcionales.

---
*Este documento se actualizará a medida que avance el proyecto.*
