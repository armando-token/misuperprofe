# 📖 Guía Maestra del Proyecto: Arquitectura y Principios

Este documento es la **fuente de verdad única** sobre la arquitectura, el flujo de datos y los principios de diseño del sistema de chat de MiSuperProfe.

---

## 🏗️ **Arquitectura del Sistema**

El sistema se compone de dos ecosistemas principales que se ejecutan en paralelo: los **servicios base** (dockerizados) y los **servicios de chat** (ejecutados en el host).

### **1. Servicios Base (Docker)**
Gestionados a través de `docker-compose.yml`, proporcionan la lógica de negocio y la persistencia de datos.

| Servicio | Contenedor | Puerto | Descripción |
| :--- | :--- | :--- | :--- |
| **API Principal** | `misuperapi` | `8000` | Backend FastAPI con la lógica de negocio, endpoints inteligentes (`/ask`), y gestión de lecciones. |
| **Base de Datos** | `misuperpostgre`| `5432` | Base de datos PostgreSQL donde reside todo el contenido y progreso de los usuarios. |
| **Caché** | `misuperredis` | `6379` | Instancia de Redis utilizada para caching y tareas de apoyo. |
| **Autenticación** | `wordpress_misuperprofe` | `8081` | Instancia de WordPress que gestiona usuarios y membresías (Paid Memberships Pro). |

### **2. Servicios de Chat (Host)**
Componentes no dockerizados que conforman la interfaz y la lógica conversacional.

| Servicio | Directorio | Puerto | Descripción |
| :--- | :--- | :--- | :--- |
| **Frontend** | `/frontend-chat` | `5174` | Cliente React/Vite con `@copilotkit/react-ui`. Es la interfaz de usuario. |
| **Runtime** | `/copilot-runtime`| `4000` | Servidor Node.js que actúa como intermediario entre el frontend y el agente. |
| **Agente** | `/app` | `8001` | Servidor Python/FastAPI que expone el agente conversacional construido con LangGraph. |

---

## 🌊 **Flujo de Datos y Comunicación**

1.  **Inicio de Chat:** El **Frontend** (en `http://<IP>:5174`) solicita al **Runtime** (puerto `4000`) el agente `misuperprofe_agent`.
2.  **Envío de Mensaje:** El usuario envía un mensaje. El Frontend lo envía al **Runtime**.
3.  **Procesamiento del Runtime:** El **Runtime** (configurado con `OpenAIAdapter`) reenvía la solicitud al **Agente** en el puerto `8001`.
4.  **Lógica del Agente (LangGraph):**
    *   El **Agente** recibe la pregunta.
    *   Utiliza su **única herramienta** (`ask_mcp_server_tool`) para formular una consulta clara al backend principal.
    *   La herramienta determina si debe llamar al endpoint de listar cursos (`POST /api/v1/api/courses`) o al endpoint de conocimiento (`POST /api/v1/ask`) en la **API Principal** (puerto `8000`).
5.  **Búsqueda en el Backend:** La **API Principal** realiza la búsqueda semántica en la base de datos **PostgreSQL** y devuelve solo la información relevante (un fragmento de teoría, una lista de cursos, etc.).
6.  **Respuesta al Usuario:** La respuesta viaja de vuelta por la misma cadena: `API Principal` -> `Agente` -> `Runtime` -> `Frontend`, que la muestra al usuario.

![Diagrama de Flujo](https://i.imgur.com/your_diagram_image.png) <!-- Reemplazar con un diagrama real si es posible -->

---

## 🔐 **Flujo de Autenticación**

La autenticación es crucial y se basa en las **Contraseñas de Aplicación de WordPress**.

1.  **Generación:** Un usuario genera una "Contraseña de Aplicación" en su perfil de WordPress.
2.  **Login en el Chat:** En la UI del **Frontend**, el usuario introduce su nombre de usuario de WordPress y esta contraseña de aplicación.
3.  **Validación:** El **Frontend** envía estas credenciales (vía `Authorization: Basic`) a un endpoint personalizado en **WordPress** (`/wp-json/misuperprofe/v1/auth_status`).
4.  **Respuesta de WordPress:** El plugin de WordPress valida las credenciales. Si son correctas, devuelve el `user_id`, `display_name` y el estado de su membresía.
5.  **Propagación (Próximo Paso):** El `user_id` y `display_name` deben ser enviados por el Frontend en **cabeceras personalizadas** (`X-User-ID`, `X-User-Name`) en cada solicitud al **Runtime**, que a su vez las reenviará al **Agente** para poblar el `AgentState` y personalizar la experiencia.

---

## ⚖️ **Principios de Diseño y Reglas de Oro**

Estos principios son **innegociables** para mantener la estabilidad y escalabilidad del proyecto.

*   **Delegación Total al Backend:** El Agente/LLM **NUNCA** realiza búsquedas, filtrado o procesamiento masivo de datos. Toda la lógica de negocio y el acceso a la base de datos se delega a la **API Principal** (MCP Server) a través de sus endpoints inteligentes. El agente solo orquesta.
*   **Abstracción con Herramienta Única:** El agente utiliza una sola herramienta genérica (`ask_mcp_server_tool`). Esto simplifica su diseño y centraliza la lógica de comunicación con el backend, haciendo el sistema más fácil de mantener y extender.
*   **Configuración Explícita:** No se debe usar `localhost` para la comunicación entre servicios. Los puertos y hosts deben ser explícitos. El archivo `.env` es la fuente de verdad para la configuración y no debe ser modificado por el código.
*   **Gestión de Dependencias Rigurosa:** Usar `poetry` para Python y `npm`/`pnpm` para Node.js. Evitar instalaciones globales. Todas las dependencias deben estar declaradas en `pyproject.toml` y `package.json`.
*   **Documentar Antes de Actuar:** Cualquier cambio significativo, error encontrado o decisión de arquitectura debe ser documentado en los archivos `.md` correspondientes antes de implementar.

---

## ⚠️ **Lecciones Aprendidas Críticas (Errores a no repetir)**

*   **AGENT_NOT_FOUND:** El nombre del agente solicitado por el Frontend debe coincidir exactamente con el expuesto por el Backend.
*   **Invalid adapter configuration:** El Runtime debe tener un `serviceAdapter` (como `OpenAIAdapter`) configurado para poder usar un LLM.
*   **CORS (Cross-Origin Resource Sharing):** La comunicación entre el Frontend y el Runtime (en diferentes puertos) fallará con `net::ERR_CONNECTION_REFUSED` si el Runtime no tiene un middleware `cors` habilitado.
*   **Checkpointer en LangGraph:** LangGraph **requiere** un `checkpointer` (ej. `InMemorySaver`) para funcionar. Sin él, fallará con `ValueError: No checkpointer set`.
*   **Conflictos de Puertos:** Verificar siempre que los puertos no estén ya en uso antes de lanzar un servicio.
*   **Memoria (OOM Killer):** Procesos que consumen mucha memoria (como los de Node.js) pueden ser terminados por el sistema si no hay suficiente RAM. Activar un archivo `swap` es una solución efectiva para entornos de desarrollo.
*   **Poblamiento de la Base de Datos:** La aplicación no funcionará correctamente si la base de datos no se ha poblado con el contenido de los cursos. El script `scripts/load_markdown.py` es un paso esencial en la configuración.