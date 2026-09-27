# Misuperprofe API (Integrado con ChatGPT Team)

Misuperprofe API es el backend para una plataforma de aprendizaje adaptativo, ahora diseñado para una integración profunda con el entorno de ChatGPT Team. Proporciona endpoints para la gestión de contenido educativo, seguimiento del progreso del estudiante, lógica de lecciones interactivas, sistema de repetición espaciada (SRS), tablas de clasificación, y funcionalidades para profesores y administradores de academias.

La API está construida con FastAPI, Uvicorn, SQLAlchemy, Alembic para migraciones, PostgreSQL como base de datos principal y Redis para caching y leaderboards.

## Visión General y Arquitectura

-   **Tecnologías Principales:** FastAPI, PostgreSQL, Redis, SQLAlchemy.
-   **Integración con ChatGPT Team:** La autenticación de usuarios finales (alumnos, profesores) se realiza a través de un flujo OAuth 2.0 gestionado por este servidor, iniciado desde un GPT personalizado dentro de ChatGPT Team. Esto permite aprovechar la gestión de identidades y seguridad de ChatGPT Team.
-   **Gestión de Roles y Permisos:** Los roles específicos de Misuperprofe (ej. `alumno`, `profesor`, `admin_academia`) y los permisos granulares de acceso a contenido y clases se gestionan a través de un sistema externo (previsto para ser Supabase). La API de Misuperprofe consulta este sistema para tomar decisiones de autorización.
-   **Enfoque B2B:** Diseñado para academias y organizaciones que utilizan ChatGPT Team, donde Misuperprofe añade valor sobre la infraestructura de Team.

## Características Principales

-   📚 **Gestión de Contenido:** Carga de cursos y capítulos desde archivos Markdown.
-   🔐 **Autenticación Segura:** Flujo OAuth 2.0 para autenticar usuarios de ChatGPT Team y emitir JWTs específicos de Misuperprofe.
-   🧑‍💼 **Gestión de Roles y Permisos Externos:** Integración con un sistema como Supabase para una gestión flexible de roles (alumno, profesor, admin_academia) y permisos de acceso a clases y materiales.
-   👨‍🎓 **Flujo de Lecciones Interactivas:** Endpoints para iniciar lecciones, enviar respuestas, obtener el siguiente ítem (basado en errores, SRS o secuencia) y completar lecciones.
-   🧠 **Aprendizaje Adaptativo (Básico):** Sistema de Repetición Espaciada (SRS) para programar repasos de ítems.
-   🏆 **Gamificación:** Sistema de XP, rachas (streaks) y tablas de clasificación (leaderboards) semanales.
-   📊 **Analíticas:** Endpoints para obtener el dashboard de progreso del usuario y su avance a lo largo del tiempo.
-   👩‍🏫 **Funcionalidades para Profesores y Administradores:**
    *   Los profesores pueden ver el progreso detallado de los alumnos en sus clases asignadas (la asignación de clases y el rol de profesor se gestionan vía Supabase).
    *   (Futuro) Administradores de academia podrán gestionar roles y acceso a clases/cursos desde Supabase.
-   🐳 **Conteinerización:** Configuración completa con Docker y Docker Compose para un despliegue y desarrollo simplificados.
-   ⚙️ **Migraciones de Base de Datos:** Gestión de esquema de base de datos con Alembic.

## Requisitos

- Python 3.11+
- Poetry (para gestión de dependencias y ejecución de scripts)
- PostgreSQL (v13+ recomendado)
- Redis
- Docker y Docker Compose (recomendado para desarrollo y despliegue)
- Una instancia de Supabase (o sistema similar) configurada para la gestión de roles y permisos.

## Configuración

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO_MISUPERPROFE>
    cd misuperprofe # O el nombre del directorio clonado
    ```

2.  **Configurar variables de entorno:**
    Copie `.env.example` a `.env` y modifíquelo con su configuración. Asegúrese de que las siguientes variables estén correctamente configuradas:
    ```dotenv
    # Base de Datos (usadas por la aplicación y Alembic)
    DATABASE_URL=postgresql+asyncpg://misuper_usuario:tu_password_seguro_aqui@db:5432/misuper_bd
    ALEMBIC_DATABASE_URL=postgresql+psycopg2://misuper_usuario:tu_password_seguro_aqui@db:5432/misuper_bd # Para Alembic

    # Redis
    REDIS_URL=redis://redis:6379/0

    # Aplicación FastAPI y JWT OAuth para ChatGPT Team
    JWT_OAUTH_SECRET_KEY=TU_CLAVE_SECRETA_PARA_JWT_OAUTH_MUY_SEGURA_Y_LARGA # Cambiar esto
    JWT_OAUTH_ALGORITHM=HS256 # O el algoritmo que prefieras (ej. RS256 si usas claves pública/privada)
    # Nota: Si se utiliza un algoritmo asimétrico como RS256, se necesitará gestionar un par de claves pública/privada en lugar de solo la SECRET_KEY.
    # La clave pública se usaría para la verificación y la privada para la firma.
    JWT_OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30

    # Supabase (para gestión de roles y permisos)
    SUPABASE_URL="TU_SUPABASE_URL"
    SUPABASE_KEY="TU_SUPABASE_SERVICE_ROLE_KEY" # O la anon key si es apropiado para las consultas

    LOG_LEVEL=INFO # DEBUG, INFO, WARNING, ERROR

    # Estas son usadas por el servicio 'db' en docker-compose.yml para inicializar la BD
    POSTGRES_USER=misuper_usuario
    POSTGRES_PASSWORD=tu_password_seguro_aqui # Debe coincidir con la de DATABASE_URL
    POSTGRES_DB=misuper_bd         # Debe coincidir con la de DATABASE_URL
    ```
    **Nota:** `JWT_OAUTH_SECRET_KEY` es crucial para la seguridad de los tokens emitidos a los usuarios de ChatGPT Team.

3.  **Configuración de Supabase (Externa):**
    Antes de que la API pueda funcionar completamente, necesitará configurar su instancia de Supabase con las tablas y funciones necesarias para:
    *   Mapear usuarios de ChatGPT Team (`external_user_identifier`, ej. email) a roles de Misuperprofe (`alumno`, `profesor`, `admin_academia`). (Ej. una tabla `user_roles` o similar).
    *   Gestionar la pertenencia de alumnos y profesores a clases/grupos. (Ej. tablas para `clases`/`grupos`, y tablas de asociación para `profesor_clase` y `alumno_clase`).
    *   Definir permisos de acceso a cursos y capítulos por clase, rol, o usuario. (Ej. una tabla `material_permissions` que vincule usuarios/roles/clases con `material_id` y fechas de acceso).
    *   El archivo `app/crud/crud_supabase.py` contiene las funciones que interactuarán con estas tablas (ej. `get_user_misuperprofe_role_from_supabase`, `check_profesor_clase_access_supabase`, `check_user_material_access_supabase`, etc.). Deberá actualizar los nombres de tablas y columnas placeholders en ese archivo para que coincidan con su esquema de Supabase.

## Instalación y Ejecución (Usando Docker Compose - Recomendado)

1.  **Asegúrese de tener Docker y Docker Compose instalados.**
2.  **Construir y levantar los contenedores (después de configurar `.env`):**
    ```bash
    docker compose up -d --build
    ```
    Esto iniciará los servicios `web` (API), `db` (PostgreSQL) y `redis`.

3.  **Ejecutar migraciones de la base de datos de Misuperprofe:**
    ```bash
    docker compose exec web poetry run alembic upgrade head
    ```

4.  **Cargar contenido inicial de cursos (teoría):**
    ```bash
    docker compose exec web poetry run python scripts/load_markdown.py
    ```

5.  **Verificar que la API esté funcionando:**
    Abra `http://localhost:8000/healthz` en su navegador o use `curl http://localhost:8000/healthz`. Debería ver `{\"status\":\"ok\"}`.
    La documentación interactiva de la API estará disponible en `http://localhost:8000/docs`.

## Flujo de Autenticación (OAuth 2.0 con ChatGPT Team)

La autenticación de los usuarios finales se realiza mediante un flujo OAuth 2.0:
1.  Un GPT personalizado dentro de ChatGPT Team, al realizar una acción que requiere acceso a Misuperprofe, redirigirá al usuario (o realizará una llamada de backend) al endpoint `/oauth/authorize` de esta API (no documentado aquí ya que es parte del flujo estándar de OAuth).
2.  El usuario se autentica si es necesario (puede ser transparente si ya está logueado en Team).
3.  Después de la autorización, el GPT recibe un código de autorización.
4.  El GPT intercambia este código por un Access Token llamando al endpoint:
    *   `POST /oauth/token`: Recibe el código de autorización, `client_id`, `client_secret` (del GPT), y otros parámetros del flujo OAuth.
        *   Este endpoint verifica el `external_user_identifier` (ej. email del usuario de Team).
        *   Consulta Supabase para obtener el rol Misuperprofe del usuario.
        *   Crea o actualiza una entrada en `external_user_map` en la BD de Misuperprofe, vinculando el usuario de Team con un `internal_user_id_hash` de Misuperprofe y su rol.
        *   Si el rol es `PROFESOR`, crea una entidad `Profesor` en la BD de Misuperprofe si no existe.
        *   Emite un JWT (Access Token) que contiene el `internal_user_id_hash`, `external_user_identifier`, y el rol Misuperprofe.
5.  El GPT utiliza este JWT en el encabezado `Authorization: Bearer <token>` para todas las llamadas subsecuentes a los endpoints protegidos de la API Misuperprofe.
6.  La API Misuperprofe valida estos JWTs para autenticar y autorizar al usuario.

## Endpoints Principales de la API

Todos los endpoints que manejan datos específicos del usuario o realizan acciones están protegidos y requieren un JWT válido obtenido a través del flujo OAuth 2.0. La base de la API es `http://localhost:8000` (en desarrollo local con Docker).

### Lecciones y Alumnos (`/api/lesson`)
*   `POST /start`: Iniciar una nueva lección. Utiliza el `internal_user_id_hash` del JWT.
*   `POST /answer`: Enviar la respuesta a un ítem. Valida que el `internal_user_id_hash` del JWT coincida con el de la sesión.
*   `POST /complete`: Marcar una lección como completada. Valida que el `internal_user_id_hash` del JWT coincida con el de la sesión.
*   `POST /next_item`: Obtener el siguiente ítem. Valida que el `internal_user_id_hash` del JWT coincida con el de la sesión.
*   `GET /leaderboard`: Obtener la tabla de clasificación.
*   `GET /user/status`: Obtener el estado y progreso general del usuario (identificado por el JWT).
*   `GET /item/{item_id}`: Obtener detalles de un ítem de lección específico. Requiere acceso al material (verificado vía Supabase).
*   `POST /result`: Registrar el resultado de una interacción LLM. Valida `student_id` contra el `internal_user_id_hash` del JWT.

### Cursos (`/api/courses`)
*   `GET /`: Listar todos los cursos disponibles.
*   `GET /{course_id}/chapters`: Listar todos los capítulos de un curso.

### Preguntas al Contenido (`/ask` en `app/main.py`)
*   `POST /ask`: Permite realizar una pregunta sobre el contenido. El acceso al capítulo resultante es verificado vía Supabase.

### Funciones del Profesor (`/api/profesor/clases` y `/api/clase_alumno`)
El rol de `PROFESOR` se determina a partir del JWT (que a su vez lo obtiene de Supabase). Los permisos para acceder a clases específicas también se verifican consultando Supabase en tiempo real a través de las dependencias (`dependencies_supabase.py`).
*   `GET /api/profesor/clases`: Listar las clases a las que el profesor (identificado por JWT) tiene acceso según Supabase.
*   `GET /api/profesor/clases/{clase_id}`: Obtener detalles de una clase específica, si el profesor tiene acceso.
*   `GET /api/profesor/clases/{clase_id}/alumnos/{user_id_hash}/progreso`: Ver el progreso de un alumno específico en una clase, si el profesor tiene acceso a la clase.
*   `POST /api/clases/join`: Endpoint para que un alumno (identificado por JWT) se una a una clase usando un `codigo_clase`. La lógica de unión y verificación de existencia/permisos de la clase se realiza vía Supabase.

### Analíticas (`/api/lesson/analytics`)
*   `GET /user_dashboard`: Obtener el dashboard de progreso de un usuario (identificado por el JWT).
*   `GET /progress_over_time`: Obtener el historial de progreso de un usuario (identificado por el JWT).

### Salud del Sistema
*   `GET /healthz`: Verificar el estado de la aplicación (no requiere autenticación).

*(Consulte la documentación Swagger generada por FastAPI en `/docs` para ver todos los endpoints, modelos de datos y detalles completos.)*

## Estructura de Contenido

El contenido de los cursos se encuentra en el directorio `content/`. Cada subdirectorio dentro de `content/` representa un curso.

```
content/
└── nombre_del_curso/
    └── nombre_del_curso_teoria.md  # Archivo Markdown con la teoría del curso
                                    # Los encabezados H2 (##) definen capítulos.
```
Ejemplo: `content/psicologia/psicologia_teoria.md`

La carga se realiza mediante el script `scripts/load_markdown.py`.

## Desarrollo Local (Sin Docker)

Si prefiere no usar Docker para la API (aunque sí para PostgreSQL/Redis, o si los tiene corriendo localmente):

1.  **Instalar Poetry:** Siga la [guía oficial de Poetry](https://python-poetry.org/docs/#installation).
2.  **Clonar el repositorio y navegar al directorio.**
3.  **Configurar `.env`:** Asegúrese de que `DATABASE_URL`, `ALEMBIC_DATABASE_URL`, `REDIS_URL`, `JWT_OAUTH_SECRET_KEY`, `SUPABASE_URL`, y `SUPABASE_KEY` apunten a sus servicios locales/accesibles y estén configuradas correctamente.
4.  **Instalar dependencias:**
    ```bash
    poetry install
    ```
5.  **Activar el entorno virtual de Poetry (opcional, `poetry run` lo hace implícitamente):**
    ```bash
    poetry shell
    ```
6.  **Ejecutar migraciones:**
    ```bash
    poetry run alembic upgrade head
    ```
7.  **Cargar contenido:**
    ```bash
    poetry run python scripts/load_markdown.py
    ```
8.  **Ejecutar el servidor FastAPI/Uvicorn:**
    ```bash
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

## Ejecución de Pruebas

Para ejecutar las pruebas unitarias y de integración, asegúrese de que su entorno esté configurado correctamente. Las pruebas están diseñadas para ejecutarse en un entorno asíncrono.

-   **Dependencias de Prueba:** Las pruebas utilizan `pytest`, `pytest-asyncio` para el manejo de funciones de prueba asíncronas, y `httpx.AsyncClient` para realizar solicitudes HTTP asíncronas a la aplicación.
-   **Base de Datos de Prueba:** Las pruebas requieren una base de datos PostgreSQL separada o la capacidad de crear y destruir tablas en su base de datos de desarrollo. La configuración de la base de datos de prueba se gestiona típicamente a través de fixtures en los archivos de prueba (ver `tests/conftest.py` si existe, o las fixtures directamente en los archivos de prueba).
-   **Entorno de Ejecución:**
    *   **Con Docker (Recomendado para consistencia):** Si su `docker-compose.yml` está configurado para ejecutar pruebas o si puede ejecutar `pytest` dentro del contenedor `web` que ya tiene acceso a una base de datos de prueba o de desarrollo configurada, este es el método preferido.
      ```bash
      docker compose exec web poetry run pytest
      ```
    *   **Localmente:** Si ejecuta las pruebas localmente (fuera de Docker), asegúrese de que las variables de entorno en su archivo `.env` (o las variables de entorno del sistema) para `DATABASE_URL` y `ALEMBIC_DATABASE_URL` apunten a su base de datos de prueba, y que esta sea accesible.
      ```bash
      poetry run pytest
      ```

Las pruebas actuales (ej. `tests/test_api_lesson.py`) están configuradas para usar una base de datos de prueba asíncrona y realizan el parcheo necesario para las dependencias de la aplicación durante el ciclo de vida de las pruebas.

## Estructura del Proyecto

Una visión general de los directorios clave del proyecto:

-   `app/`: Contiene toda la lógica principal de la aplicación FastAPI.
    -   `api/`: Routers y definiciones de endpoints (organizados por funcionalidad, ej. `lesson.py`, `course.py`, `oauth_team.py`).
    -   `crud/`: Operaciones de Create, Read, Update, Delete para interactuar con la base de datos (PostgreSQL y Supabase).
    -   `db/`: Configuración de la sesión de base de datos (SQLAlchemy) y cliente para Supabase.
    -   `models/`: Modelos de datos SQLAlchemy que definen las tablas de la base de datos.
    -   `schemas/`: Esquemas Pydantic para la validación de datos de entrada/salida y la serialización.
    -   `core/`: Componentes centrales como configuración (`config.py`) y utilidades de seguridad (`security.py`).
    -   `services/`: Lógica de negocio más compleja que puede ser reutilizada por diferentes endpoints (ej. `spaced_repetition_logic.py`).
    -   `tools/`: Utilidades diversas (ej. `redis_utils.py`, `semantic_search_optimized.py`).
    -   `main.py`: Punto de entrada de la aplicación FastAPI, donde se ensamblan los routers y se configura el middleware.
-   `alembic/`: Configuración y scripts de migración de Alembic para gestionar la evolución del esquema de la base de datos PostgreSQL.
-   `content/`: Archivos Markdown que contienen el material de los cursos.
-   `memory_bank/`: Documentación interna sobre el progreso del desarrollo y decisiones de diseño.
-   `scripts/`: Scripts de utilidad para tareas como la carga inicial de datos (`load_markdown.py`), asignación de roles, etc.
-   `tests/`: Pruebas automatizadas (unitarias y de integración) utilizando `pytest`.
-   `Dockerfile`: Define la imagen Docker para la aplicación FastAPI.
-   `docker-compose.yml`: Define los servicios para el desarrollo y despliegue (API, base de datos, Redis).
-   `pyproject.toml` y `poetry.lock`: Archivos de gestión de dependencias de Poetry.
-   `.env` (y `env.example`): Archivos para la configuración de variables de entorno.
-   `README.md`: Este archivo, con la documentación principal del proyecto.

## Contribuir

Las contribuciones son bienvenidas. Por favor, siga el flujo estándar de Git:

1.  Fork el repositorio.
2.  Cree una nueva rama para su feature (`git checkout -b feature/NuevaFuncionalidad`).
3.  Realice sus cambios y haga commit (`git commit -am \'Añadir NuevaFuncionalidad\'`).
4.  Empuje a su rama (`git push origin feature/NuevaFuncionalidad`).
5.  Abra un Pull Request.

## Licencia

Distribuido bajo la Licencia MIT. Ver `LICENSE` (si existe) para más información. 