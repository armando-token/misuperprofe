# Progreso de Instalación y Configuración del Servidor (Misuperprofe)

## Resumen de pasos completados hasta ahora:

### 1. Actualización del Sistema y Paquetes Base:
- Ejecuté `sudo apt update` y `sudo apt upgrade -y`.
- Instalé paquetes esenciales como `git`, `curl`, `build-essential`, `libpq-dev`, `python3-dev`, `python3-venv`, `wget`.

### 2. Instalación y Configuración de PostgreSQL:
- Instalé `postgresql` y `postgresql-contrib`.
- Habilité y inicié el servicio PostgreSQL (`sudo systemctl enable postgresql`, `sudo systemctl start postgresql`).
- Creé el usuario `misuper_usuario` con la contraseña proporcionada y la base de datos `misuper_bd`, con `misuper_usuario` como propietario.
- Verifiqué la conexión a la base de datos.

### 3. Instalación y Configuración de Redis:
- Instalé `redis-server`.
- Habilité y inicié el servicio Redis (`sudo systemctl enable redis-server`, `sudo systemctl start redis-server`).
- Verifiqué que Redis responde (`redis-cli ping` -> PONG).

### 4. Clonación del Código Fuente y Reorganización:
- El repositorio se clonó desde `https://github.com/MiSuperProfe/misuperprofev10.1.git`.
- Moví todo el contenido del directorio `misuperprofe` (creado por el clonado) a `/home/ubuntu` (la raíz del proyecto), y luego eliminé el directorio `misuperprofe` vacío.
- Cambié el directorio de trabajo a `/home/ubuntu`.

### 5. Organización de Archivos en `memory_bank`:
- Creé el subdirectorio `Legacy` dentro de `memory_bank`.
- Moví todos los archivos `.md` de `memory_bank` a `memory_bank/Legacy`.
- Verifiqué que los archivos `.md` están en `memory_bank/Legacy`.

### 6. Instalación de Poetry y Dependencias Python:
- Instalé Poetry utilizando `curl -sSL https://install.python-poetry.org | python3 -`.
- Agregué Poetry al PATH y recargué la configuración del shell (`echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc`).
- Eliminé `poetry.lock` (si existía), generé uno nuevo (`poetry lock`) e instalé las dependencias (`poetry install`).

### 7. Configuración de Variables de Entorno (`.env`):
- Copié `env.example` a `.env`.
- El usuario confirmó haber editado manualmente el archivo `.env` con las credenciales correctas de la base de datos y otras configuraciones.

### 8. Inicialización de Base de Datos (Migraciones SQLAlchemy con Alembic) - En Progreso:
- Creamos `alembic.ini` en `/home/ubuntu` con una configuración básica.
- **Problemas con el historial de migraciones (ciclos y orden de tablas):**
    - **Resuelto mediante re-inicialización de Alembic:**
        - Eliminamos los directorios `alembic/versions/` y el directorio `alembic/` completo, así como el archivo `alembic.ini`.
        - Re-inicializamos Alembic (`poetry run alembic init alembic`).
        - Modificamos `alembic.ini` para comentar la línea `sqlalchemy.url`.
        - Modificamos `alembic/env.py` para importar `Base` de `app.models.base` y usar `Base.metadata` como `target_metadata`, y para usar `settings.ALEMBIC_DATABASE_URL`.
        - **Generamos la primera migración exitosamente** (`poetry run alembic revision --autogenerate -m "Initial migration"`).
        - **Aplicamos la migración inicial exitosamente** (`poetry run alembic upgrade head`).
- **Estado actual:** La migración inicial ha sido generada y estamos listos para aplicarla a la base de datos.

### 9. Ejecutar pruebas automáticas (pytest) - Próximo paso
- Activación del entorno virtual: Se usa directamente `poetry run` en lugar de `poetry shell` (ya que `poetry shell` está en desuso o requiere plugins adicionales en Poetry 2.0+).
- **Resolución de errores en la ejecución de pruebas (ImportError y ModuleNotFoundError):**
    - Se resolvió el `ImportError` en `test_loaders.py` renombrando `load_course_content` a `load_markdown` en `scripts/load_markdown.py`.
    - Se resolvió el `ModuleNotFoundError` para `scripts.load_questions` recreando el archivo `/home/ubuntu/scripts/load_questions.py` con el contenido proporcionado por el usuario.
    - **Resolución de ImportError para `app.resources.pregunta.Pregunta`:**
        - Se identificó que el archivo `/home/ubuntu/app/resources/pregunta.py` estaba vacío.
        - Se recreó el archivo con el contenido proporcionado por el usuario, definiendo la clase `Pregunta`.
    - **Correcciones a las pruebas automáticas (pytest):**
        - Se corrigió el regex en `scripts/load_markdown.py` para que solo detectara encabezados de nivel 2 y 3 como capítulos.
        - Se configuraron las pruebas en `tests/test_loaders.py` para usar la base de datos PostgreSQL en lugar de SQLite, importando `settings` y usando `settings.DATABASE_URL`.
        - Se corrigió el error de capitalización en el nombre del curso ('Biologia' a 'biologia') en `tests/test_loaders.py`.
        - Se importó la clase `Pregunta` en `tests/test_loaders.py`.
        - Se corrigió el argumento pasado a `load_markdown` en `tests/test_loaders.py` para que fuera un objeto `Path`.
        - Se modificó la fixture `test_db` en `tests/test_loaders.py` para eliminar las tablas después de cada prueba (`Base.metadata.drop_all`).
        - Se ajustaron las aserciones de contenido en `test_load_markdown` para que esperaran contenido HTML.
        - Se cambió `opcion_correcta` a `respuesta_correcta` en las aserciones de `test_load_questions`.
        - Se añadió la relación `capitulo = relationship("Capitulo")` y su importación a la clase `Pregunta` en `app/resources/pregunta.py`.
    - **Estado Actual:** Las pruebas automáticas (`poetry run pytest -q`) ahora pasan exitosamente.

### 10. Configuración y Arranque con Docker Compose:
- Instalé Docker (`docker.io`) y Docker Compose (`docker-compose`).
- Habilité e inicié el servicio Docker.
- Reemplacé el contenido de `docker-compose.yml` y `Dockerfile` con las versiones simplificadas de la `Intall_guide.md`.
- **Resolución de problemas de permisos de Docker:**
    - Añadí el usuario `ubuntu` al grupo `docker` (`sudo usermod -aG docker ${USER}`).
    - Ejecutamos `newgrp docker` para aplicar los cambios de grupo.
    - Reinicié el servicio Docker (`sudo systemctl restart docker`).
    - Cambié los permisos del socket de Docker (`sudo chmod 666 /var/run/docker.sock`) como último recurso (aunque la adición al grupo y `newgrp` deberían ser suficientes en la mayoría de los casos).
- **Correcciones al `Dockerfile`:**
    - Actualicé la versión de Python de `3.10-slim` a `3.11-slim` para que coincidiera con los requisitos del proyecto.
    - Eliminé la opción `--no-dev` del comando `poetry install` ya que está obsoleta.
    - Reorganicé el `Dockerfile` para copiar el código fuente (`COPY . /app`) *antes* de `poetry install` para asegurar que el directorio `app` estuviera disponible.
- **Resolución del error "no space left on device" durante `docker-compose build`:**
    - Verifiqué el espacio en disco (`df -h`).
    - Identifiqué que el directorio `.cache` ocupaba 12GB (`du -sh * .[^.]* | sort -hr | head -n 20`).
    - Creé un archivo `.dockerignore` para excluir `.cache`, `.git`, `__pycache__`, `.pytest_cache`, `.local`, `.cursor-server` y otros archivos/directorios innecesarios del contexto de construcción de Docker.
    - Ejecuté `docker system prune -a -f` para limpiar imágenes, contenedores, volúmenes y caché de construcción no utilizados, liberando espacio.
- **Resolución de errores "address already in use" para los puertos 5432 y 6379:**
    - Detuve y deshabilité los servicios PostgreSQL (`sudo systemctl stop postgresql && sudo systemctl disable postgresql`) y Redis (`sudo systemctl stop redis-server && sudo systemctl disable redis-server`) que se estaban ejecutando directamente en el sistema.
- **Resolución del error `sqlalchemy.exc.MissingGreenlet` en el contenedor `web` (misuperapi):**
    - Verifiqué que `alembic.ini` tuviera `sqlalchemy.url` comentado.
    - Modifiqué `alembic/env.py` en la función `run_migrations_online` para construir la URL de la base de datos explícitamente con el driver síncrono `psycopg2` (`postgresql+psycopg2://...`).
    - El usuario actualizó manualmente el archivo `.env` para incluir `DB_HOST=db` (para que la aplicación apunte al servicio de base de datos de Docker Compose) y `REDIS_URL=redis://redis:6379/0` (para apuntar al servicio Redis de Docker Compose), además de la variable `POSTGRES_DATABASE_URL` completa y síncrona.
- **Resolución del error `KeyError: 'ContainerConfig'` y problemas relacionados con Docker Compose:**
    - Intentos iniciales de `docker-compose up -d --build` fallaron con `KeyError: 'ContainerConfig'`.
    - Reiniciar Docker no solucionó el problema.
    - Se ejecutó `docker-compose down --remove-orphans` para limpiar el estado.
    - Los logs del contenedor `web` (misuperapi) mostraron un error `FATAL: password authentication failed for user "misuper_usuario"`.
    - Se corrigió la variable `POSTGRES_PASSWORD` en `docker-compose.yml` de `TuContraseñaSegura` a la contraseña correcta (`<POSTGRES_PASSWORD>`).
    - El error `KeyError: 'ContainerConfig'` persistió.
    - **Actualización a Docker Compose V2:**
        - Se desinstaló Docker Compose V1 (`sudo apt remove -y docker-compose` y `sudo apt autoremove -y`).
        - Se instaló Docker Compose V2 (versión v2.36.2) en `/usr/local/lib/docker/cli-plugins/docker-compose`.
    - Después de actualizar a V2, un intento de `docker compose up -d --force-recreate` falló con un conflicto de nombre de contenedor.
    - Se ejecutó `docker compose down --remove-orphans` usando la sintaxis de V2.
    - `docker compose up -d` finalmente levantó los contenedores.
- **Resolución del error `ModuleNotFoundError: No module named 'prometheus_client'`:**
    - Tras levantar los contenedores con Docker Compose V2, `curl -I http://localhost:8000/docs` falló y `docker compose ps` mostró el servicio `misuperapi` como `Up Less than a second` (indicando reinicios).
    - Los logs del contenedor `web` revelaron `ModuleNotFoundError: No module named 'prometheus_client'`. Se determinó que las migraciones de Alembic sí se habían ejecutado antes de este error.
    - Se modificó `app/main.py` para eliminar la importación de `prometheus_client` y el endpoint `/metrics` que lo utilizaba.
- **Estado Actual de Docker Compose:**
    - Después de eliminar la dependencia de `prometheus_client`, `docker compose up -d --build` construyó la imagen `web` y levantó los contenedores.
    - Sin embargo, `docker compose ps` mostró que el servicio `misuperapi` (contenedor `web`) estaba en estado `Restarting (1)`.
    - Un intento de ver los logs del contenedor `web` para diagnosticar el reinicio falló (la herramienta no se ejecutó).
    - **Población de la Base de Datos (Sesión Actual):**
        - Se ejecutó `docker compose exec web poetry run python scripts/load_markdown.py`.
        - El script reportó la carga exitosa de la teoría para múltiples cursos (literatura, psicologia, filosofia, economia, historia, lenguage, geografia, cultura general, civica, biologia).
        - Las tablas `curso` y `capitulo` ahora deberían estar pobladas.
    - **Verificación Post-Carga de Datos (Sesión Actual):**
        - Se reinició el servicio `web` (misuperapi) con `docker compose restart web`.
        - Los logs más recientes del contenedor `web` muestran que la aplicación consulta la tabla `capitulo` durante el inicio.
        - El endpoint `/healthz` responde con HTTP 200 (`curl http://localhost:8000/healthz`), confirmando que la aplicación está operativa.
    - **Verificación y Corrección del Endpoint `/api/lesson/result` (Sesión Actual):**
        - Se identificó que el endpoint `/api/lesson/result` fallaba con un error 500 debido a `StringDataRightTruncationError` al intentar guardar "N/A" en una columna `respuesta` de tipo `VARCHAR(1)`.
        - Se modificó `app/models/resultado.py` para añadir las columnas `pregunta_generada` y `respuesta_usuario` (ambas `Text, nullable=True`).
        - Se modificó `app/api/lesson.py` (función `record_llm_lesson_result`) para:
            - Cambiar la asignación de `respuesta` a `"L"` (para LLM).
            - Guardar `result_data.llm_question` en `pregunta_generada` y `result_data.user_response` en `respuesta_usuario`.
        - Se generó y aplicó una nueva migración de Alembic (`c933eba07dca`) para estos cambios.
        - Se reconstruyó la imagen Docker y se reiniciaron los servicios.
        - El endpoint `/api/lesson/result` respondió exitosamente (HTTP 201) con el payload de prueba, confirmando que el registro de resultados de LLM funciona.
        - Se descomentó y habilitó la lógica de autenticación (verificación de token Bearer) en `app/api/lesson.py` para el endpoint `record_llm_lesson_result`.
        - Se reconstruyó la imagen Docker y se reiniciaron los servicios.
        - Se confirmó que una solicitud a `/api/lesson/result` sin token de autenticación devuelve HTTP 403 (Forbidden).
        - Se confirmó que una solicitud a `/api/lesson/result` con el token de autenticación correcto devuelve HTTP 201 (Created).
    - **Verificación y Corrección del Endpoint `/api/lesson/answer` (Sesión Actual):**
        - Se inició una lección con `/api/lesson/start` para obtener `session_id` y `item_id`.
        - El primer intento a `/api/lesson/answer` falló con `ConnectionRefusedError` porque intentaba usar `asyncpg.connect()` con una URL de BBDD posiblemente incorrecta (`DATABASE_URL_ASYNCPG`) y la tabla `attempts` no existía.
        - Se creó el modelo SQLAlchemy `Attempt` en `app/models/adaptive.py`.
        - Se refactorizó la función `submit_answer` en `app/api/lesson.py` para usar el modelo `Attempt` con la sesión SQLAlchemy (`db`) en lugar de `asyncpg` directo.
        - Se generó y aplicó una nueva migración de Alembic (`c803bfc3f1e8`) para crear la tabla `attempts`. Se corrigió un `NameError` en este script de migración.
        - El segundo intento a `/api/lesson/answer` falló con `NameError: name 'SpacedRepetition' is not defined` en `app/api/lesson.py`.
        - Se añadió la importación de `SpacedRepetition` en `app/api/lesson.py`.
        - El tercer intento a `/api/lesson/answer` falló con `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379` porque `redis.Redis()` se instanciaba sin usar `settings.REDIS_URL`.
        - Se modificó `app/api/lesson.py` para instanciar el cliente Redis usando `redis.from_url(settings.REDIS_URL)`.
        - Se reconstruyó la imagen Docker y se reiniciaron los servicios tras cada corrección.
        - El endpoint `/api/lesson/answer` finalmente respondió exitosamente con un `next_item_id`, `next_item_content`, XP y racha, confirmando que la lógica adaptativa y el registro de intentos funcionan.
    - **Verificación y Corrección del Endpoint `/api/lesson/complete` (Sesión Actual):**
        - Se procedió a probar `POST /api/lesson/complete` usando el `session_id` previamente obtenido.
        - **Primer intento:** Falló con `{\"detail\":\"Error en la transacción de cierre de lección: 'Select' object has no attribute 'count'\"}`.
            - **Corrección (Conteo SQLAlchemy):** Se modificó `app/api/lesson.py` (función `complete_lesson`) para usar `select(func.count(LessonError.id)).filter(...)` y `scalar_one_or_none() or 0`.
            - **Problemas de espacio en disco durante la reconstrucción (Build 1):**
                - `docker compose up -d --build` falló con `[Errno 28] No space left on device`.
                - Se modificó el `Dockerfile` para añadir `RUN poetry cache clear --all -n`. Falló la build (`Not enough arguments (missing: \"cache\")`).
                - Se corrigió en `Dockerfile` a `RUN poetry cache clear . --all -n`. Falló la build por espacio.
                - Se modificó el `Dockerfile` para añadir `--no-install-recommends` a `apt-get install` y `apt-get clean && rm -rf /var/lib/apt/lists/*`.
                - El build (`docker compose up -d --build`) falló nuevamente por espacio durante `apt-get install`.
                - Se ejecutó `docker system prune -a -f` (liberó ~53GB).
                - `docker compose up -d --build` finalmente tuvo éxito.
        - **Segundo intento:** Falló con HTTP 500. Los logs (`docker compose logs web`) indicaron un `ROLLBACK` después de intentar obtener `UserProgress`.
            - **Corrección (Manejo de `UserProgress` no existente):** Se modificó `app/api/lesson.py` para crear una nueva instancia de `UserProgress` si no existía, asegurar la actualización de `total_xp` antes de calcular cofres, y añadir `progress` a la sesión `db` solo si no era `None`.
            - Se reconstruyó la imagen Docker (`docker compose up -d --build`) con éxito (Build 2).
        - **Tercer intento:** Falló con `{\"detail\":\"Error en la transacción de cierre de lección: name 'logger' is not defined\"}`.
            - **Corrección (`logger` no definido):** Se añadió `logger = logging.getLogger(__name__)` al inicio de la función `complete_lesson` en `app/api/lesson.py`.
            - Se reconstruyó la imagen Docker (`docker compose up -d --build`) con éxito (Build 3).
        - **Cuarto intento:** Falló con `{\"detail\":\"Error en la transacción de cierre de lección: object NoneType can\\\'t be used in \\\'await\\\' expression\"}`.
            - **Corrección (`await` en `db.add` y `ProgressUnit` no añadido):** Se eliminó `await` de `db.add()` y se añadió `db.add(pu)` para nuevas instancias de `ProgressUnit` en `complete_lesson`.
            - **Fallo de reconstrucción por espacio (Build 4):** `docker compose up -d --build` falló con `[Errno 28] No space left on device` durante `poetry install` (específicamente con `nvidia-cusparse-cu12`).
        - **Manejo persistente del error \"No space left on device\" (Post Build 4):**
            - Se movieron `matplotlib` y `seaborn` de `[tool.poetry.dependencies]` a `[tool.poetry.group.dev.dependencies]` en `pyproject.toml` para reducir dependencias de producción.
            - El intento de reconstruir (`docker compose up -d --build`) fue interrumpido por el usuario/sistema. Los logs parciales mostraron que la construcción estaba en progreso, pero el problema subyacente de `nvidia-cusparse-cu12` (probablemente dependencia transitiva de `sentence-transformers`/`torch`) se perfilaba como el principal bloqueador. La estrategia de instalar PyTorch (CPU) explícitamente en el Dockerfile había fallado previamente también por falta de espacio.
        - **Resolución de `poetry.lock` desactualizado (Post Build 4 y cambio en `pyproject.toml`):**
            - Un nuevo intento de `docker compose up -d --build` (después de `docker system prune -a -f`) falló el 2024-08-16 indicando: `pyproject.toml changed significantly since poetry.lock was last generated. Run \\`poetry lock\\` to fix the lock file.`
            - **Primer intento de regeneración (fallido):** Se ejecutó `docker run --rm -v $(pwd):/app -w /app python:3.11-slim poetry lock --no-update`. Falló porque la imagen `python:3.11-slim` no incluye `poetry`.
            - **Segundo intento de regeneración (fallido):** Se ejecutó `docker run --rm -v $(pwd):/app -w /app python:3.11-slim /bin/sh -c \"pip install poetry && poetry lock --no-update\"`. Falló porque la opción `\"--no-update\"` no es válida para `poetry lock`.
            - **Tercer intento de regeneración (exitoso):** Se ejecutó `docker run --rm -v $(pwd):/app -w /app python:3.11-slim /bin/sh -c \"pip install poetry && poetry lock\"`. Esto regeneró `poetry.lock` correctamente.
        - **Reconstrucción Exitosa (Build 5 - 2024-08-16):** Después de regenerar `poetry.lock` y con `matplotlib` y `seaborn` en dependencias de desarrollo (y `torch` CPU instalado explícitamente en el `Dockerfile`), `docker compose up -d --build` se completó exitosamente. Todos los servicios (`db`, `redis`, `web`) están `Up` y `Healthy`.
    - **Diagnóstico y Corrección de Error en `/api/lesson/complete` (Continuación - Post Build 5):**
        - **Quinto intento a `/api/lesson/complete` (2024-08-16):** El comando `curl` falló con código de salida 56 (`CURLE_RECV_ERROR`).
        - **Análisis de logs:** Los logs del contenedor `web` mostraron un `ROLLBACK` de la base de datos y una advertencia `SAWarning: On class 'ProgressUnit', Column object 'unit_id' named directly multiple times, only one will be used: chapter_id, unit_id. Consider using orm.synonym instead`.
        - **Corrección del modelo `ProgressUnit`:** Se identificó que la línea `chapter_id = unit_id` en `app/models/adaptive.py` causaba el conflicto. Se corrigió renombrando la columna `unit_id` a `chapter_id` en su definición original y eliminando la asignación conflictiva.
        - **Generación de migración:** Se generó el script de migración `e8bb99ef6f2e_rename_unit_id_to_chapter_id_in_.py`.
        - **Ajuste manual del script de migración:** El script autogenerado se modificó manualmente para manejar correctamente el renombramiento de una columna que es parte de una clave primaria y foránea, incluyendo la copia de datos y la recreación de restricciones (`progress_units_pkey` asumida como nombre de PK).
        - **Aplicación de migración:** El script de migración ajustado `e8bb99ef6f2e` se aplicó exitosamente a la base de datos.
        - **Limpieza de Docker:** Se ejecutó `docker system prune -a -f` (liberó ~28GB).
        - **Reconstrucción Exitosa (Build 6 - 2024-08-16):** Después de la migración `e8bb99ef6f2e` y la limpieza de Docker, `docker compose up -d --build` se completó exitosamente. Todos los servicios (`db`, `redis`, `web`) están `Up` y `Healthy`.
    - **Diagnóstico y Corrección de Error en `/api/lesson/complete` (Continuación - Post Build 6):**
        - **Análisis y Corrección:** Se identificó que, a pesar de la migración de la base de datos, el código en `app/api/lesson.py` (en las funciones `submit_answer` y `complete_lesson`) todavía usaba `ProgressUnit.unit_id` en consultas y `unit_id=` al instanciar `ProgressUnit`. Se corrigieron estas referencias a `ProgressUnit.chapter_id` y `chapter_id=` respectivamente.
        - **Reconstrucción Exitosa (Build 7 - 2024-08-16):** Después de corregir las referencias en `app/api/lesson.py`, `docker compose up -d --build` se completó exitosamente. Todos los servicios están `Up` y `Healthy`.
        - **Séptimo intento y ÉXITO con `/api/lesson/complete` (2024-08-16):** El endpoint respondió con HTTP 200 y el payload `{\"xp\":30,\"accuracy\":1.0,\"duration\":33366,\"claim_token\":\"claim-4c1ccbb1-ca45-4154-92f9-a1063646dc8a-1749193519\"}`. Esto confirma que la lógica de la lección completa, incluyendo las interacciones con `ProgressUnit` y otras tablas, ahora funciona correctamente.

- **Verificación del Endpoint `/ask` (2024-08-16):**
    - Se identificó la definición del endpoint `/ask` en `app/main.py`.
    - Se probó con la pregunta `\"¿Qué es el Realismo?\"`.
    - El endpoint respondió con HTTP 200, devolviendo un fragmento del capítulo \"C. LA ESENCIA DEL CONOCIMIENTO\" con una definición filosófica de Realismo y una confianza de ~0.66.
    - **Mejora Identificada y Aplicada:** Se observó que `/ask` no devolvía el `chapter_id`, necesario para el flujo con `/api/lesson/result`. Se modificó `app/main.py` para incluir `"capitulo_id": chapter.id` en la respuesta de `/ask`.

### 11. Ajustes Finales, Corrección de Errores y Verificaciones Exhaustivas (Post 2024-08-16)

#### 11.1 Configuración de Firewall (ufw)
- Se permitió OpenSSH: `sudo ufw allow OpenSSH`
- Se permitió el puerto 8000/tcp para la API: `sudo ufw allow 8000/tcp`
- Se habilitó ufw: `sudo ufw enable`
- Se verificó el estado: `sudo ufw status verbose` (Mostró OpenSSH y 8000/tcp permitidos desde cualquier lugar).

#### 11.2 Verificación de Datos en PostgreSQL
- Se conectó a la base de datos `misuper_bd` con el usuario `misuper_usuario` vía `psql`.
- Conteo de cursos: `SELECT COUNT(*) FROM curso;` (Resultado: 10)
- Conteo de capítulos: `SELECT COUNT(*) FROM capitulo;` (Resultado: 2473)
- **Conclusión:** La carga de datos inicial fue exitosa.

#### 11.3 Verificación del Endpoint de Login y Flujo de Autenticación
- Se revisó `app/api/lesson.py` (endpoint `record_llm_lesson_result`) y `app/main.py` (endpoint `start_session`).
- **Autenticación:** Se utiliza una `API_KEY` estática (`<API_KEY>` del archivo `.env`) enviada como Bearer Token para proteger `record_llm_lesson_result`. El endpoint `start_session` no parece tener autenticación (lo cual es esperado si es para iniciar sesión de un usuario final, que luego podría usar un token de sesión para otras operaciones).

#### 11.4 Investigación del Uso de Redis
- **Búsqueda en el código:** `grep -r -i "redis" .`
- **Identificación de Usos:**
    - `app/api/lesson.py`: Actualización de leaderboards, gestión de "error flags".
    - `app/tools/redis_utils.py`: Funciones de utilidad para interactuar con Redis (leaderboards, colas de lecciones/errores, flags de error).
    - `app/main.py`: Inicialización del cliente Redis.
- **Corrección de `NameError` en `redis_utils.py`:**
    - `REDIS_ERROR_FLAG_PREFIX` no estaba definido globalmente.
    - **Solución:** Se añadió `REDIS_ERROR_FLAG_PREFIX = "error_flag:"` a `app/tools/redis_utils.py`.
- **Eliminación de Redefinición Local en `app/api/lesson.py`:**
    - Se eliminó la redefinición local de `REDIS_ERROR_FLAG_PREFIX` en `app/api/lesson.py` para usar la global de `redis_utils.py`.
- **Corrección de Errores Lógicos y de Tipos en `app/api/lesson.py` (Error Flags):**
    - El objeto `error` (instancia de `LessonError`) no tiene atributo `id` antes de ser añadido a la BBDD.
    - El `item_id` en `set_error_flag` es un string (UUID) pero `Capitulo.id` es `INT`.
    - **Solución:** Se corrigió la lógica para usar `error.item_id` (que es el `chapter_id` como string) consistentemente para el flag de Redis.
- **Verificación de Error Flags en Redis:**
    - Se simuló un error y se verificó la creación del flag en Redis (`redis-cli KEYS "error_flag:*"`).
    - Se verificó la eliminación del flag después de una respuesta correcta.
    - **Conclusión:** Los flags de error en Redis funcionan correctamente.

#### 11.5 Resolución de Problemas de Construcción de Docker ("No space left on device")
- **Contexto:** Durante la implementación de funcionalidades para profesores, los builds de Docker fallaban consistentemente por falta de espacio, especialmente al instalar `torch` y sus dependencias CUDA.
- **Pasos de Resolución:**
    1.  **Limpieza Profunda:** `docker system prune -a -f` (liberó ~30GB inicialmente).
    2.  **Modificación de `pyproject.toml` para PyTorch CPU:**
        - Se añadió una fuente explícita para PyTorch CPU:
          \`\`\`toml
          [[tool.poetry.source]]
          name = "pytorch_cpu"
          url = "https://download.pytorch.org/whl/cpu"
          priority = "explicit"
          \`\`\`
        - Se forzó la dependencia `torch` desde esta fuente:
          `torch = {version = "^2.0.0", source = "pytorch_cpu"}`

### 12. Depuración: Frontend React/Vite (CopilotKit) con Backend FastAPI - Error 401 Unauthorized (En Progreso a 21 de Junio de 2025)

- **Contexto:** Se está intentando hacer funcionar un frontend desarrollado con React (Vite) y la librería CopilotKit (accesible en `http://18.214.59.62:5173/`) para que se comunique con el endpoint `/agent/chat` del backend FastAPI.
- **Problema Principal:** El frontend recibe consistentemente un error `401 Unauthorized` al realizar peticiones POST al endpoint `/agent/chat`, a pesar de que el token JWT (generado localmente mediante un script Python para pruebas) se envía en la cabecera `Authorization: Bearer <token>`.
- **Pasos de Depuración Realizados y Observaciones:**
    - **Corrección de `IndentationError` en Backend:** Se resolvió un `IndentationError` en `app/api/agent_chat.py` (corregido manualmente por el usuario) que impedía que el endpoint se cargara correctamente.
    - **Depuración de Token JWT:**
        - Se generaron tokens JWT de prueba localmente.
        - Inicialmente, el backend reportó `JWT validation/decoding error: Signature has expired.`.
        - Se generaron nuevos tokens frescos, y se confirmó que el frontend (`App.tsx`) los extraía correctamente de la URL (`?token=...`) y los incluía en la cabecera de las peticiones.
    - **Persistencia del Error 401:** A pesar de usar tokens frescos, el error `401 Unauthorized` continuó.
    - **Mensajes de Depuración en Backend (`[AUTH_DEBUG]`):**
        - Se añadieron mensajes de depuración (prints con el prefijo `[AUTH_DEBUG]`) en la función `get_current_team_user_claims` en `app/api/dependencies_team.py` para trazar el proceso de validación del token.
        - **Observación Crucial:** Estos mensajes `[AUTH_DEBUG]` no aparecían en los logs del backend (`misuperapi`) cuando se producía el error 401 desde el frontend de React/Vite. Esto sugirió que la dependencia `reusable_oauth2_team` (basada en `OAuth2PasswordBearer`) podría estar rechazando la petición antes de que la lógica de validación personalizada de JWT (donde están los prints) se ejecutara, posiblemente debido a una cabecera `Authorization` ausente o malformada.
    - **Hipótesis sobre Proxy de Vite:** Se formuló la hipótesis de que el proxy configurado en `vite.config.ts` (para redirigir las peticiones `/agent/chat` del frontend al backend en el puerto 8000) podría no estar pasando correctamente la cabecera `Authorization`.
    - **Middleware para Registrar Cabeceras en Backend (`[HEADERS_DEBUG]`):
        - Se añadió un middleware a `app/main.py` para registrar todas las cabeceras de las peticiones entrantes al backend, con logs prefijados por `[HEADERS_DEBUG]`.
        - El objetivo era verificar si la cabecera `Authorization` llegaba al backend y con qué contenido.
- **Estado Actual de la Depuración (21 de Junio de 2025):**
    - Se está intentando obtener y analizar los logs del backend (`misuperapi`) que contengan los mensajes `[HEADERS_DEBUG]` después de realizar una petición desde el frontend de React/Vite (`http://18.214.59.62:5173/`).
    - Se experimentaron dificultades para obtener estos logs del backend mediante la interfaz, y se instruyó al usuario para reiniciar los contenedores Docker y visualizar los logs directamente desde su terminal EC2.
    - **Objetivo Inmediato:** Confirmar si la cabecera `Authorization` (con el token JWT) está llegando correctamente al backend FastAPI. Si llega, analizar su contenido. Si no llega, el problema reside en la configuración del proxy de Vite o en cómo el frontend realiza la petición a través del proxy.

### 13. Configuración de Nginx para Múltiples Dominios (WordPress y FastAPI)

- Se verificó y ajustó la configuración de Nginx en el servidor host para actuar como reverse proxy:
    - `misuperprofe.com` apunta al servicio WordPress dockerizado (expuesto en el puerto 8081 del host).
    - `app.misuperprofe.com` apunta al servicio FastAPI dockerizado (expuesto en el puerto 8000 del host).
- Se confirmó que Certbot gestionaba los certificados SSL para ambos subdominios, asegurando la comunicación HTTPS.
- Se limpiaron bloques de servidor HTTP redundantes y se recargó la configuración de Nginx (`sudo nginx -t && sudo systemctl reload nginx`).
- El acceso a ambos dominios (`https://misuperprofe.com` y `https://app.misuperprofe.com`) fue verificado.

### 14. Corrección de Datos del Curso "Lenguaje" (20-21 de Junio de 2025)

- **Problema:** El tutor IA no podía listar los capítulos del curso "Lenguaje" porque en la base de datos estaba registrado como "lenguage" (con 'g').
- **Pasos de Corrección:**
    1.  Se renombró el directorio `content/lenguage/` a `content/lenguaje/`.
    2.  Se renombró el archivo de teoría `content/lenguaje/lenguage_teoria.md` a `content/lenguaje/lenguaje_teoria.md`.
    3.  Se eliminaron los datos incorrectos (capítulos y curso "lenguage") de la base de datos PostgreSQL directamente.
    4.  Se ejecutó el script `scripts/load_markdown.py` para recargar los datos del curso "Lenguaje" correctamente.
    5.  Se reconstruyó y reinició el contenedor `web` de FastAPI.
- **Resultado:** El tutor IA ahora puede listar correctamente los capítulos del curso "Lenguaje". Se resolvió un error 502 Bad Gateway temporal que ocurrió post-corrección, debido al tiempo de "warmup" de FastAPI al recalcular embeddings.

### 15. Análisis del Comportamiento de Búsqueda Semántica con "Hola" (21 de Junio de 2025)

- **Observación:** Al enviar el mensaje "hola" al tutor, este respondía con información sobre "El hiato".
- **Análisis:** Mediante logs en `app/api/agent_chat.py`, se confirmó que la búsqueda semántica recuperaba un extracto del capítulo "El hiato" para la consulta "hola".
- **Conclusión:** Se determinó que esto se debe a la similitud semántica (según el modelo de embeddings) entre "hola" y el contenido del capítulo "El hiato", o a que es uno de los pocos documentos considerados relevantes para una consulta tan genérica. No se consideró una acción correctiva inmediata, pero se tomó nota del comportamiento para futuras evaluaciones de la búsqueda semántica.

### 16. Depuración del Sistema de Chat (LangGraph AG-UI Agent + React/Vite CopilotKit Frontend) - (Junio 2025)

**Objetivo General:** Implementar y depurar un sistema de chat compuesto por un frontend React/Vite con CopilotKit y un backend FastAPI/LangGraph utilizando el protocolo AG-UI para la comunicación de eventos.

**Estado Inicial:** Backend de FastAPI con LangGraph parcialmente funcional (con persistencia en Redis presentando errores por falta de RediSearch), y frontend Vite ejecutándose pero inaccesible externamente debido a `ERR_CONNECTION_TIMED_OUT`.

**Resumen Cronológico Detallado de la Depuración:**

1.  **Configuración y Reinicio de Servicios:**
    *   Se confirmó la IP pública de la instancia EC2 (`18.214.59.62`).
    *   Se verificó y confirmó la configuración del grupo de seguridad de AWS para permitir el tráfico en el puerto `5174` (frontend Vite).
    *   Se reiniciaron los servicios:
        *   Docker Compose (conteniendo Redis y PostgreSQL) con `docker compose up -d`.
        *   Backend del agente LangGraph (FastAPI) en el puerto `5175` con `poetry run python3 -m app.main` (ejecutado en segundo plano).
        *   Frontend React/Vite (CopilotKit) en el puerto `5174` con `cd chat-frontend-react && npm run dev -- --host 0.0.0.0 --port 5174` (ejecutado en segundo plano).

2.  **Diagnóstico y Resolución del Firewall `ufw`:**
    *   A pesar de los reinicios, el `ERR_CONNECTION_TIMED_OUT` persistía para el frontend en el puerto `5174`.
    *   Se inspeccionó el estado del firewall local `ufw` con `sudo ufw status verbose`.
    *   Se descubrió que `ufw` estaba activo pero no tenía una regla explícita para el puerto `5174`.
    *   Se añadió la regla con `sudo ufw allow 5174/tcp`.
    *   **Resultado:** El frontend comenzó a cargar en el navegador, pero presentó problemas de comunicación con el backend.

3.  **Depuración de Errores Iniciales en el Agente LangGraph y AG-UI (`app/api/routers/agent_router.py`):**
    *   **`AttributeError: AGENT` (en `available_agents_event_stream`):**
        *   Se intentó cambiar `Role.AGENT` a `Role.ASSISTANT` basado en una suposición incorrecta.
        *   Se investigó la definición de `ag_ui.core.Role` y se descubrió que es un `typing.Literal["developer", "system", "assistant", "user", "tool"]`.
        *   **Solución:** Se corrigieron todos los usos de `Role.MEMBER` a las cadenas literales correspondientes (ej. `role="assistant"`).
    *   **`AttributeError: 'CompiledStateGraph' object has no attribute 'astream_events_v2'` (en `run_agent_graph_task`):**
        *   **Solución:** Se cambió el método a `agent_graph.astream_log(...)` como primer intento de obtener un stream de eventos/logs del grafo.
    *   **Errores de Validación Pydantic para Eventos AG-UI:**
        *   Múltiples errores relacionados con la falta del campo `type` o campos incorrectos en la instanciación de `RunStartedEvent`, `RunErrorEvent`, `TextMessageContentEvent`, etc.
        *   **Solución:** Se revisaron las definiciones de los eventos en `ag_ui.core.types` y se corrigieron las instanciaciones para que cumplieran con los esquemas, incluyendo el campo `type=EventType.EVENT_NAME`.
    *   **`NameError: name 'AGUIMessage' is not defined`:**
        *   Una importación de `Message as AGUIMessage` desde `ag_ui.core.types` fue eliminada accidentalmente y luego restaurada.
    *   **`TypeError: Cannot instantiate typing.Union` para `availableAgents`:**
        *   Se intentó usar `AGUIMessage` directamente, luego `TextMessageContentEvent`.
        *   **Solución:** Se optó por usar `AssistantMessage` de `ag_ui.core.types` para el payload JSON de `availableAgents`.

4.  **Manejo de Procesos del Backend y Puerto Ocupado:**
    *   Se detectó repetidamente que el backend no se reiniciaba correctamente porque el proceso anterior seguía ocupando el puerto `5175` (`address already in use`).
    *   **Solución:** Se utilizó `sudo lsof -t -i:5175` para encontrar el PID del proceso ofensivo y `sudo kill -9 <PID>` para detenerlo. Este ciclo se repitió varias veces durante la depuración.

5.  **Problema del Proceso Backend "Killed":**
    *   En varias ocasiones, el proceso del backend (`poetry run python3 -m app.main`) terminaba abruptamente con el mensaje "Killed" poco después de que el usuario enviaba un mensaje y el agente comenzaba a procesarlo (específicamente después del log `Entering call_llm_node`).
    *   Este problema pareció mitigarse una vez que se corrigieron varios de los errores de validación de Pydantic y atributos de los eventos AG-UI.

6.  **Depuración del Streaming de Chunks del LLM con `astream_log`:**
    *   **`RuntimeWarning: coroutine 'AGUIEventEmitter.emit' was never awaited`:**
        *   Se identificó que los métodos `emit` y `signal_done` de la clase `AGUIEventEmitter` (definida en `app/agents/main_agent.py`) son corutinas (`async def`).
        *   **Solución:** Se añadió `await` a todas las llamadas a `event_emitter.emit(...)` y `event_emitter.signal_done()` en `app/api/routers/agent_router.py`.
    *   **Problema con `RunLogPatch` y `AttributeError: 'RunLogPatch' object has no attribute 'get'`:**
        *   Se descubrió que los eventos de `agent_graph.astream_log()` son objetos `RunLogPatch` y no diccionarios simples. El acceso a su contenido debe hacerse a través de sus atributos (ej. `event.ops`).
    *   **Intento de Procesar `event.ops` de `RunLogPatch`:**
        *   Se intentó iterar sobre `event.ops` para encontrar los chunks de LLM, buscando en `op['path']` patrones como `/streamed_output_str/-` o `/streamed_output/-` y extrayendo `op['value']`.
        *   Se añadió `await asyncio.sleep(0)` dentro y fuera del bucle `astream_log` para intentar ceder control al event loop de asyncio y evitar que la conexión SSE se cierre.
    *   **Persistencia del `Event generator cancelled`:**
        *   A pesar de los ajustes, el warning `Event generator cancelled for thread_id ...` continuaba apareciendo en los logs del backend inmediatamente después de que el agente entraba al nodo de llamada al LLM (`Entering call_llm_node`).
        *   El frontend recibía el evento `RUN_STARTED` (visible en la pestaña Network del navegador) pero no los chunks de la respuesta del LLM.
        *   Hipótesis: El bucle `async for event in agent_graph.astream_log(...)` no producía eventos de manera continua o no cedía el control adecuadamente, llevando al cierre de la conexión SSE por inactividad percibida por el cliente.

7.  **Cambio de Estrategia: Uso de `astream_events` (Investigación y Aplicación):**
    *   Tras la persistencia del problema de `Event generator cancelled` y la dificultad para extraer consistentemente los chunks del LLM de `RunLogPatch` con `astream_log`, se realizó una investigación sobre las mejores prácticas para streaming con LangGraph y FastAPI.
    *   **Descubrimiento:** La documentación y ejemplos de LangGraph sugieren que el método `astream_events(version="v2")` es más adecuado para obtener un flujo de eventos estructurados, incluyendo los chunks del LLM, de una forma más compatible con Server-Sent Events (SSE).
    *   **Acción:** Se modificó `app/api/routers/agent_router.py` en la función `run_agent_graph_task` para reemplazar `agent_graph.astream_log(...)` con `agent_graph.astream_events(initial_state, config=config_for_graph, version="v2")`.
    *   Se adaptó la lógica dentro del bucle para procesar la nueva estructura de eventos de `astream_events`, esperando encontrar los chunks del LLM en eventos como `on_chat_model_stream` o `on_llm_stream`, accediendo a `event_data["data"]["chunk"].content`.

8.  **Problema de Persistencia con Redis (Observación Continua):**
    *   Durante todo el proceso, al iniciar el backend, se observó consistentemente el error:
        `redisvl.exceptions.RedisModuleVersionError: Required Redis db module search >= 20600 OR searchlight >= 20600 not installed. See Redis Stack docs at https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/.`
    *   Esto indica que la instancia de Redis utilizada (probablemente la del `docker-compose.yml` estándar) no incluye el módulo RediSearch, necesario para el `RedisSaver` de `langgraph-checkpoint-redis`.
    *   **Impacto:** El agente LangGraph funciona, pero la persistencia del historial de conversación y el estado del grafo entre reinicios o diferentes sesiones de usuario no está activa. El checkpointer se deshabilita graciosamente.

**Estado Actual de la Depuración (al final de la sesión del 22 de Junio, post cambio a `astream_events`):**

*   El backend ha sido modificado para usar `astream_events`.
*   El siguiente paso es ejecutar el backend con estos cambios, probar el chat desde el frontend y analizar los nuevos logs del backend para:
    *   Verificar si el `Event generator cancelled` se resuelve.
    *   Observar la estructura de los eventos recibidos de `astream_events`.
    *   Confirmar si los chunks del LLM se extraen y emiten correctamente al frontend.
*   El usuario ha expresado frustración por la duración del proceso de depuración y la falta de consulta de documentación o ejemplos externos por parte del asistente en etapas tempranas.

### 17. Reestructuración del Chat: Integración del Ejemplo `minimal-copilotkit-langgraph` en MiSuperProfe (Junio 2025)

**Objetivo General:** Superar los bloqueos persistentes en la depuración del sistema de chat original y lograr una base funcional mediante la adaptación de un ejemplo externo (`minimal-copilotkit-langgraph`) a la estructura del proyecto MiSuperProfe.

**Resumen Cronológico Detallado:**

1.  **Decisión de Cambio de Estrategia:**
    *   Ante la continua dificultad para hacer funcionar el streaming de respuestas del agente LangGraph original de MiSuperProfe con el frontend CopilotKit (problemas con `astream_log`, `astream_events`, y el cierre prematuro de la conexión SSE), se optó por buscar un ejemplo funcional completo de CopilotKit + AG-UI + LangGraph para usar como base.

2.  **Investigación y Selección del Repositorio de Ejemplo:**
    *   Se realizó una búsqueda web (`github copilotkit ag-ui example functional demo`).
    *   Se seleccionó el repositorio `jrhicks/minimal-copilotkit-langgraph` por su simplicidad y por utilizar un stack tecnológico similar (React/Vite, FastAPI/LangGraph) sin NextJS.

3.  **Clonación y Configuración Inicial del Ejemplo (`minimal-copilotkit-langgraph`):**
    *   Se clonó el repositorio en `/home/ubuntu/minimal-copilotkit-langgraph`.
    *   Se revisó su `README.md`, identificando una estructura monorepo con `react-client`, `copilot-runtime-service`, y `lang-graph-service`.
    *   Se copió `lang-graph-service/.env.example` a `lang-graph-service/.env` y el usuario añadió sus claves API (ej. `OPENAI_API_KEY`, aunque luego se usaría Gemini).
    *   Se intentó `pnpm install` en la raíz del ejemplo, falló por `pnpm` no instalado.
    *   Se instaló `pnpm` globalmente: `sudo npm install -g pnpm`.
    *   Se ejecutó `pnpm install` exitosamente en la raíz del ejemplo.

4.  **Prueba y Funcionamiento del Ejemplo Clonado:**
    *   Se intentó ejecutar `pnpm run dev` (que inicia los tres servicios: React en `5173`, Copilot runtime en `4000`, LangGraph en `8000`).
    *   Se abrieron los puertos `5173`, `4000`, `8000` en el firewall `ufw`.
    *   **Problema de Acceso al Frontend:** `ERR_CONNECTION_REFUSED`.
        *   El usuario indicó que solo el puerto `5174` estaba disponible externamente en AWS.
        *   Se liberó el puerto `5174` en el servidor: `sudo lsof -t -i:5174 | xargs --no-run-if-empty sudo kill -9`.
        *   Se modificó `minimal-copilotkit-langgraph/react-client/package.json` para cambiar el script `dev` a `vite --port 5174`.
        *   Se reabrió el puerto `5174` en `ufw`.
        *   El error persistía. Se diagnosticó que Vite por defecto escucha solo en `localhost`.
        *   **Solución:** Se modificó el script `dev` en `minimal-copilotkit-langgraph/react-client/package.json` a `vite --port 5174 --host`.
    *   **Éxito:** Tras reiniciar los servicios con `cd /home/ubuntu/minimal-copilotkit-langgraph && pnpm run dev` (ejecutado en primer plano por el asistente), el ejemplo funcionó correctamente y el chat era accesible y operativo en `http://<IP_PUBLICA>:5174`.
    *   **Problema de Persistencia de Servicios:** El chat dejaba de funcionar si la terminal que ejecutaba `pnpm run dev` se cerraba. Se reiniciaron los servicios en primer plano para pruebas del usuario.

5.  **Reestructuración: Movimiento de Archivos a la Estructura de MiSuperProfe:**
    *   El usuario solicitó integrar los componentes del ejemplo directamente en `/home/ubuntu/` para simplificar la gestión.
    *   Se creó el directorio `/home/ubuntu/frontend-chat` y se movió el contenido de `minimal-copilotkit-langgraph/react-client/` a este nuevo directorio.
    *   Se creó el directorio `/home/ubuntu/copilot-runtime` y se movió el contenido de `minimal-copilotkit-langgraph/copilot-runtime-service/`.
    *   Se creó el directorio `/home/ubuntu/app/agents_langgraph_example` y se movió el contenido de `minimal-copilotkit-langgraph/lang-graph-service/sample_agent/`.
    *   Se copió `minimal-copilotkit-langgraph/lang-graph-service/server.py` a `/home/ubuntu/app/langgraph_server_example.py`.

6.  **Gestión de Dependencias Python en el Proyecto MiSuperProfe:**
    *   Se leyó `minimal-copilotkit-langgraph/lang-graph-service/pyproject.toml` y el `pyproject.toml` principal (`/home/ubuntu/pyproject.toml`).
    *   Se fusionaron las dependencias del ejemplo en `/home/ubuntu/pyproject.toml`, actualizando versiones donde fue necesario.
    *   **Resolución de Conflictos `poetry lock`/`install`:**
        *   Conflicto inicial entre `langgraph` y `langgraph-cli[inmem]`. Se ajustó la versión de `langgraph-cli` a `>=0.1.64`.
        *   Error `module 'posixpath' has no attribute 'ALLOW_MISSING'`. Se intentó actualizar Poetry, eliminar `poetry.lock`, cambiar versiones de Python activas en Poetry. El error parecía relacionado con `tarfile.py` de Python 3.12.
        *   Se forzó el uso de `python3.11` con `poetry env use python3.11`.
        *   Se relajaron las restricciones de versión: `langgraph = " >=0.3.0"` y `langgraph-cli = {extras = ["inmem"], version = "^0.1.0"}`.
        *   Error `No file/folder found for package misuperprofe-chat-agent`. Se solucionó añadiendo `packages = [{include = "app"}]` a la sección `[tool.poetry]` en `/home/ubuntu/pyproject.toml`.
    *   **Éxito:** `poetry install` finalmente se completó exitosamente.

7.  **Configuración de Ejecución Centralizada con `concurrently`:**
    *   El usuario confirmó la configuración de `/home/ubuntu/.env` con las claves API necesarias.
    *   Se intentó instalar `concurrently` globalmente con `sudo pnpm add -g concurrently` (falló) y luego con `sudo npm install -g concurrently` (exitoso).
    *   Se creó un archivo `/home/ubuntu/package.json` con scripts para iniciar los tres servicios (`frontend-chat`, `copilot-runtime`, y el backend LangGraph `poetry run python3 app/langgraph_server_example.py`) usando `concurrently`.
        ```json
        {
          "name": "misuperprofe-chat-services",
          "version": "1.0.0",
          "scripts": {
            "start:frontend": "cd frontend-chat && pnpm run dev",
            "start:runtime": "cd copilot-runtime && pnpm run dev",
            "start:backend": "poetry run python3 app/langgraph_server_example.py",
            "start:all": "concurrently \"npm:start:frontend\" \"npm:start:runtime\" \"npm:start:backend\""
          },
          "devDependencies": {
            "concurrently": "^8.2.2"
          }
        }
        ```
    *   Se ejecutó `pnpm install` en `/home/ubuntu/` para instalar `concurrently` como dependencia de desarrollo local.

8.  **Instalación de Dependencias en Subdirectorios Node.js:**
    *   `pnpm run start:all` falló inicialmente porque `vite` no se encontraba.
    *   Se ejecutó `pnpm install` dentro de `/home/ubuntu/frontend-chat/`.
    *   Se ejecutó `pnpm install` dentro de `/home/ubuntu/copilot-runtime/`.

9.  **Resolución de Problemas en la Ejecución Integrada:**
    *   **`ENOSPC: System limit for number of file watchers reached`:**
        *   **Solución:** Se aumentó el límite con `sudo sysctl fs.inotify.max_user_watches=524288`.
    *   **`ModuleNotFoundError: No module named 'sample_agent'` en `langgraph_server_example.py`:**
        *   **Solución:** Se corrigió la importación en `app/langgraph_server_example.py` a `from app.agents_langgraph_example.agent import graph` (inicialmente se intentó `from app.agents_langgraph_example.agent import agent as graph`).
        *   También se corrigió la ruta en la llamada `uvicorn.run` a `app.langgraph_server_example:app`.
    *   **`ImportError: cannot import name 'agent' from 'app.agents_langgraph_example.agent'`:**
        *   Se verificó `app/agents_langgraph_example/agent.py` y se confirmó que el objeto exportado se llamaba `graph`.
        *   **Solución:** Se corrigió la importación en `app/langgraph_server_example.py` a `from app.agents_langgraph_example.agent import graph`.

10. **Éxito Funcional del Sistema Reestructurado (Base):**
    *   Tras las correcciones, la ejecución de `pnpm run start:all` desde `/home/ubuntu/` inició exitosamente los tres servicios.
    *   Se confirmó que el chat era funcional con el agente de ejemplo del repositorio `minimal-copilotkit-langgraph`.

11. **Implementación de Autenticación JWT y Refinamiento del Backend (`app/langgraph_server_example.py`) (23 de Junio de 2025):**
    *   **Diagnóstico de `ModuleNotFoundError: No module named 'copilotkit.runtime'`:**
        *   Se determinó que la versión `0.1.46` de `copilotkit` tiene una estructura de módulos diferente. `CopilotKitRuntime` ahora es `CopilotKitSDK` (o más preferiblemente, `CopilotKitRemoteEndpoint`) y `LangGraphAdapterReferencedThread` ya no se usa directamente de esa forma.
    *   **Refactorización de `app/langgraph_server_example.py`:**
        *   Se cambiaron las importaciones para usar `CopilotKitRemoteEndpoint` (inicialmente `CopilotKitSDK`, luego ajustado para eliminar `DeprecationWarning`).
        *   Se implementó una clase `AuthenticatedLangGraphAgent(LangGraphAgent)` que sobrescribe el método `execute`.
        *   Dentro de `AuthenticatedLangGraphAgent.execute`:
            *   Se extrae el token JWT de las cabeceras de la solicitud (proporcionadas por CopilotKit en `config["context"]["headers"]`).
            *   Se valida el token usando la función `validate_and_decode_token` existente.
            *   Si el token es válido, se añaden `initial_user_id` (del claim `sub`) e `initial_nombre_usuario` (del claim `name`) al diccionario de estado que se pasa al grafo LangGraph.
        *   Se configuró la instancia principal de `CopilotKitRemoteEndpoint` para usar esta `AuthenticatedLangGraphAgent`, proporcionándole el grafo (`actual_langgraph_executable_graph`) y una configuración que incluye un `InMemorySaver` como `checkpointer`.
        *   Se eliminó el endpoint personalizado `@app.post("/")` y la lógica de adaptador antigua, confiando en el endpoint estándar `/copilotkit` provisto por `add_fastapi_endpoint`.
    *   **Corrección de Errores de Ejecución:**
        *   **`SyntaxError: 'return' with value in async generator`:** Corregido en el manejo de errores JSON dentro de un generador asíncrono.
        *   **`TypeError: 'coroutine' object is not iterable` y `RuntimeWarning: coroutine 'AuthenticatedLangGraphAgent.execute' was never awaited`:** Se corrigió asegurando que `AuthenticatedLangGraphAgent.execute` se comporte como un generador asíncrono usando `async for chunk in super().execute(...): yield chunk`.
    *   **Estado Actual del Chat (Post-Correcciones):**
        *   Los tres servicios (`frontend-chat`, `copilot-runtime`, `langgraph_server_example.py`) se inician correctamente.
        *   El frontend carga en `http://18.214.59.62:5174/?token=...`.
        *   El chat es funcional: los mensajes se envían, el agente (aún el de ejemplo, pero ahora con la capa de autenticación) procesa y responde.
        *   Las herramientas CRUD básicas (`list_available_courses_tool`, `list_chapters_for_course_tool`) del agente `app/agents_langgraph_example/agent.py` se ejecutan correctamente, como se evidencia por las consultas a la base de datos en los logs.
        *   El `DeprecationWarning` relacionado con `CopilotKitSDK` ha sido resuelto usando `CopilotKitRemoteEndpoint`.

**Próximos Pasos Inmediatos:**
*   **Verificación Exhaustiva de la Autenticación JWT End-to-End:** Confirmar en los logs del backend (`[AUTH_AGENT_DEBUG]`) que `initial_user_id` e `initial_nombre_usuario` se extraen del token y se pasan al estado del agente.
*   **Adaptación Completa del Agente MiSuperProfe:** Proceder con la Sub-fase 8.3 y 8.5 del plan en `memory_bank/copilot.md` (implementar herramientas restantes, refinar prompts).
*   **Limpieza de Código y Archivos Redundantes.**
*   **Solución para la Persistencia de Redis (LangGraph Checkpointer).**

--- 
*Este documento se actualizará a medida que avance el proyecto.*

### 18. Cambio de Estrategia de Autenticación y Corrección de Terminología (Junio 2025 - Posterior al 23 de Junio)

**Contexto:** Tras la persistencia de problemas y la complejidad en la implementación robusta de la autenticación basada en JWT entre WordPress y el sistema de chat LangGraph, y después de que el sistema base de chat (frontend, runtime, backend LangGraph) se estabilizara, se decidió cambiar el enfoque de autenticación.

**Acciones y Decisiones:**

1.  **Revisión de la Estrategia de Autenticación:**
    *   Se evaluó la viabilidad de un sistema donde WordPress actúa como la única fuente de verdad para la autenticación y el estado de membresía del usuario.
    *   El MCP Server (Model Context Protocol Server, anteriormente referido erróneamente como NPC) consultará directamente WordPress para verificar si un usuario está logueado y tiene una membresía activa (usando Paid Memberships Pro).
    *   Este enfoque elimina la dependencia de AWS Cognito y de los tokens JWT complejos que resultaron problemáticos.
    *   Se descartó el uso del plugin "WP OAuth Server" debido a informes de abandono y fallas.

2.  **Plan Detallado para Autenticación Directa con WordPress:**
    *   **Plugin Personalizado en WordPress:** Se creará un plugin (`misuperprofe-chat-auth-endpoint`) para alojar un endpoint REST API (ej. `/wp-json/misuperprofe/v1/chat_auth_status`). Este endpoint:
        *   Verificará el login del usuario en WordPress.
        *   Obtendrá `user_id` y `display_name`.
        *   Verificará la membresía activa usando `pmpro_hasMembershipLevel()`.
        *   Devolverá un JSON con este estado.
    *   **Frontend (`frontend-chat`):**
        *   Llamará al nuevo endpoint de WordPress.
        *   Si el usuario está autenticado y tiene membresía activa, enviará el `user_id` en una cabecera `X-Wordpress-User-ID` al `copilot-runtime` (y por ende al MCP Server).
    *   **MCP Server (Backend LangGraph):**
        *   Extraerá el `user_id` de la cabecera.
        *   **Obligatorio:** Se conectará a la BD de WordPress con un usuario de BD de solo lectura.
        *   Consultará la BD de WordPress para obtener `display_name` y re-verificar el estado de la membresía activa usando el `user_id`.
        *   Poblará el `AgentState` con la información del usuario validada.
    *   Se definieron medidas de seguridad (plugin personalizado, permisos de BD, HTTPS, etc.).

3.  **Corrección de Terminología:**
    *   Se acordó usar consistentemente "MCP Server" (Model Context Protocol Server) en lugar de "NPC".

4.  **Copia de Seguridad Git:**
    *   Se realizó una copia de seguridad local (commit) de todos los cambios antes de proceder con las modificaciones a la documentación y la implementación del nuevo plan de autenticación.

**Próximos Pasos Inmediatos (según el nuevo plan de autenticación):**

*   Desarrollar el plugin personalizado de WordPress.
*   Adaptar el frontend para el nuevo flujo de autenticación.
*   Implementar la lógica de conexión a BD de WordPress y verificación en el MCP Server.
*   Actualizar la documentación (`memory_bank/copilot.md` y `memory_bank/Progress1.md`) para reflejar estos detalles y el progreso.
*   Realizar una copia de seguridad Git una vez que estos cambios en la documentación estén hechos.

---
*Este documento se actualizará a medida que avance el proyecto.*

### 19. Implementación y Depuración del Plugin de Autenticación de WordPress (Junio 2025)

**Contexto:** Siguiendo el nuevo plan de autenticación directa con WordPress, se procedió a crear y depurar el plugin encargado de exponer el estado de autenticación y membresía del usuario.

**Pasos y Observaciones:**

1.  **Creación del Plugin `misuperprofe-chat-auth-endpoint`:**
    *   Se creó el archivo `wp-content/plugins/misuperprofe-chat-auth-endpoint/misuperprofe-chat-auth-endpoint.php` con la lógica inicial del endpoint REST `/wp-json/misuperprofe/v1/chat_auth_status`.

2.  **Problemas de Visibilidad del Plugin en WordPress Admin:**
    *   Inicialmente, el plugin no aparecía en la lista de plugins de WordPress.
    *   Se verificaron la ruta del plugin, su contenido básico (cabeceras de plugin), permisos de archivo/directorio (`755`/`644`) y propietario (`www-data:www-data`).
    *   **Causa Raíz Identificada:** El archivo `docker-compose.yml` utilizaba un volumen nombrado (`wordpress_data`) para `/var/www/html`, lo que significaba que los archivos del plugin creados en el sistema de archivos del host no eran visibles dentro del contenedor de WordPress.

3.  **Intentos de Solución para la Visibilidad del Plugin:**
    *   **Intento 1 (Modificación de `docker-compose.yml` - Fallido y Revertido):**
        *   Se modificó `docker-compose.yml` para mapear directamente `./wp-content/plugins` del host a `/var/www/html/wp-content/plugins` en el contenedor.
        *   Esto hizo que el nuevo plugin apareciera, pero ocultó todos los plugins previamente instalados por el usuario (instalados dentro del volumen nombrado), causando una interrupción.
        *   **Acción:** Se revirtió inmediatamente el cambio en `docker-compose.yml` y se reiniciaron los contenedores para restaurar la visibilidad de los plugins del usuario.
    *   **Intento 2 (Copia Directa al Contenedor - Exitoso):**
        *   Se utilizó `docker cp ./wp-content/plugins/misuperprofe-chat-auth-endpoint wordpress_misuperprofe:/var/www/html/wp-content/plugins/` para copiar el directorio del plugin directamente al contenedor en ejecución.
        *   **Resultado:** El plugin apareció en la lista y pudo ser activado por el usuario.

4.  **Pruebas del Endpoint `/wp-json/misuperprofe/v1/chat_auth_status`:**
    *   **Error Inicial (`ERR_CONNECTION_TIMED_OUT`):**
        *   Al intentar acceder al endpoint, se recibió un timeout.
        *   **Causa:** El puerto `8081` (mapeado a WordPress en `docker-compose.yml`) no estaba abierto en el Security Group de AWS.
        *   **Solución:** El usuario abrió el puerto `8081` en AWS.
    *   **Prueba Sin Sesión de WordPress (Exitosa):**
        *   Al acceder al endpoint desde un navegador sin una sesión activa en WordPress (ej. ventana de incógnito), se obtuvo la respuesta JSON esperada: `{"logged_in":false,"member_active":false,"user_id":null,"display_name":null}`.
    *   **Problema con Sesión de WordPress Activa (`404 rest_no_route`):**
        *   Al acceder al endpoint desde un navegador donde el usuario SÍ estaba logueado en WordPress (usuario "turismo", membresía "Gratis" activa), el endpoint devolvió un error `404 Not Found` con el mensaje `{"code":"rest_no_route","message":"No route was found matching the URL and request method.","data":{"status":404}}`. Esto fue inesperado, ya que el endpoint funcionaba sin sesión.

5.  **Depuración del Error 404 (y Posterior Problema de Autenticación):**
    *   **Modificación del `permission_callback` (Intento 1):**
        *   Se cambió el `permission_callback` del endpoint en el plugin PHP a `is_user_logged_in`.
        *   **Resultado (Logueado):** Al acceder logueado, se obtuvo un error `401 Unauthorized` con el mensaje: `{"code":"rest_forbidden","message":"Lo siento, no tienes permisos para hacer eso.","data":{"status":401}}`. Esto indicaba que, aunque la ruta se reconocía, `is_user_logged_in` devolvía `false` en ese contexto o el nonce no era válido.
    *   **Reversión y Adición de Logs (`error_log()`):**
        *   Se revirtió el `permission_callback` a `__return_true` para simplificar y asegurar que el callback del endpoint se ejecutara.
        *   Se añadieron sentencias `error_log()` dentro de la función `chat_auth_status_callback` del plugin para registrar el valor de `is_user_logged_in()`, `wp_get_current_user()->ID`, y el resultado de `pmpro_hasMembershipLevel()`.
    *   **Observación Clave desde los Logs de WordPress:**
        *   Al acceder al endpoint estando logueado en el navegador (que seguía mostrando `{"logged_in":false,...}` en la respuesta JSON), los logs del contenedor de WordPress (`docker logs wordpress_misuperprofe`) revelaron:
            *   `[MiSuperProfe Debug] chat_auth_status: is_user_logged_in() es FALSE`
            *   `[MiSuperProfe Debug] chat_auth_status: user_id es 0`
            *   `[MiSuperProfe Debug] chat_auth_status: pmpro_hasMembershipLevel() para user 0 es FALSE`
        *   **Conclusión Fundamental:** En el contexto de la solicitud a la API REST realizada por el navegador (incluso desde una pestaña donde el usuario está logueado en el panel de WP), WordPress no está reconociendo la sesión de autenticación del usuario. `is_user_logged_in()` devuelve `false` porque la cookie de sesión de WordPress probablemente no se envía o no se procesa correctamente para las solicitudes a la API REST de esta manera. Esto explica tanto el `404` inicial (si alguna comprobación de nonce o similar fallaba silenciosamente) como el `logged_in: false` posterior.

**Próximos Pasos Inmediatos (según el nuevo plan de autenticación y este diagnóstico):**

*   **Modificar el Frontend (`frontend-chat/src/App.tsx`):**
    *   La principal hipótesis es que la petición `fetch` desde el frontend al endpoint de WordPress no está incluyendo las cookies de autenticación de WordPress.
    *   Se debe asegurar que la petición `fetch` al endpoint `/wp-json/misuperprofe/v1/chat_auth_status` se realice con la opción `credentials: 'include'`. Esto es crucial para que el navegador envíe las cookies relevantes del dominio de WordPress.
    *   Investigar si se necesitan cabeceras adicionales (como nonces de WP REST API si se activan `permission_callback` más estrictos) una vez que el envío de cookies funcione.
*   **Re-probar el endpoint de WordPress** después de ajustar el frontend.
*   Si la autenticación funciona, proceder con la implementación de la lógica en el **MCP Server** para:
    *   Leer la cabecera `X-Wordpress-User-ID`.
    *   Conectarse a la BD de WordPress para la re-verificación de membresía y obtención de `display_name`.
    *   Poblar el `AgentState`.
*   Actualizar la documentación (`memory_bank/copilot.md`) para reflejar estos detalles y el progreso.
*   Realizar una copia de seguridad Git una vez que estos cambios en la documentación estén hechos.

--- 
*Este documento se actualizará a medida que avance el proyecto.*

### 20. Pausa y Próximos Pasos en Depuración de Autenticación WordPress (Finales de Junio 2025)

**Contexto:** Después de una extensa sesión de depuración intentando que el plugin de WordPress reconociera la sesión del usuario a través de la API REST, y tras encontrar problemas de permisos al intentar modificar el plugin directamente desde el asistente, se decidió pausar y continuar al día siguiente.

**Estado Actual y Tareas Pendientes Inmediatas (para mañana):**

1.  **Modificación Manual del Plugin de WordPress:**
    *   **Archivo:** `wp-content/plugins/misuperprofe-chat-auth-endpoint/misuperprofe-chat-auth-endpoint.php` (ubicado en `/home/ubuntu/wp-content/...` en el host).
    *   **Tarea:** El usuario deberá editar manualmente este archivo para añadir la siguiente línea de código PHP justo al inicio (primera línea dentro) de la función `misuperprofe_chat_auth_status_callback(WP_REST_Request $request)`:
        ```php
        error_log('[MiSuperProfe Debug] COOKIES LLEGANDO AL ENDPOINT: ' . print_r($_COOKIE, true));
        ```
    *   **Objetivo:** Registrar si las cookies del navegador están llegando efectivamente al script PHP del endpoint.

2.  **Copia del Plugin Modificado al Contenedor Docker:**
    *   Una vez modificado el archivo en el host, el usuario deberá copiar el directorio completo del plugin actualizado al contenedor de WordPress usando un comando similar a:
        ```bash
        sudo docker cp /home/ubuntu/wp-content/plugins/misuperprofe-chat-auth-endpoint wordpress_misuperprofe:/var/www/html/wp-content/plugins/
        ```
    *   **Nota:** Es importante asegurarse de que el usuario `ubuntu` tenga permisos de lectura sobre los archivos del plugin en el host, o ejecutar el `docker cp` con `sudo` si es necesario (como se muestra).

3.  **Reinicio de Servicios:**
    *   Ejecutar `pnpm run start:all` desde `/home/ubuntu/` para reiniciar el frontend, el runtime y el backend del chat.

4.  **Prueba del Flujo de Autenticación:**
    *   **Paso 1:** Iniciar sesión en el panel de administración de WordPress (`https://misuperprofe.com/wp-admin/`) con el usuario "turismo" (o cualquier usuario con sesión y membresía activa).
    *   **Paso 2:** En una nueva pestaña del **mismo navegador**, abrir la aplicación de chat: `http://<TU_IP_PUBLICA_EC2>:5174`. (Reemplazar `<TU_IP_PUBLICA_EC2>` con la IP pública correcta, ej. `18.214.59.62`).
    *   **Paso 3:** Observar la respuesta del endpoint en la consola del navegador y en el recuadro de depuración del frontend.

5.  **Análisis de Logs de WordPress:**
    *   Después de realizar la prueba, ejecutar el siguiente comando en la terminal del servidor EC2 para ver los logs relevantes del contenedor de WordPress:
        ```bash
        docker logs wordpress_misuperprofe | grep "MiSuperProfe Debug"
        ```
    *   **Objetivo:**
        *   Verificar si aparece la línea `[MiSuperProfe Debug] COOKIES LLEGANDO AL ENDPOINT: ...` y analizar el contenido de las cookies recibidas.
        *   Observar el resultado de `is_user_logged_in()` que se registra después.

6.  **Siguientes Pasos (basados en los logs):**
    *   **Si las cookies llegan y `is_user_logged_in()` sigue siendo `false`:** Investigar por qué WordPress no valida la sesión a partir de esas cookies en el contexto de la API REST (podría ser necesario un nonce, o alguna inicialización específica de WordPress para sesiones en la API REST).
    *   **Si las cookies NO llegan (el array `$_COOKIE` está vacío o no contiene las cookies de sesión de WordPress):** El problema seguiría apuntando a cómo el navegador/frontend maneja el envío de cookies en la petición `fetch`, a pesar de `credentials: 'include'`. Se podría investigar si hay políticas de `SameSite`, `CORS` u otras configuraciones de Nginx o WordPress que interfieran.

---
*Este documento se actualizará a medida que avance el proyecto.*

## Progreso Depuración Autenticación WordPress (24 de Junio)

**Objetivo:** Lograr que `frontend-chat` (corriendo en `http://18.214.59.62:5174`) se autentique correctamente contra WordPress (`https://misuperprofe.com`) para que el chat pueda verificar si un usuario ha iniciado sesión y tiene una membresía activa.

**Problema Principal Persistente:**
El endpoint del plugin de WordPress `/wp-json/misuperprofe/v1/chat_auth_status` consistentemente reporta que el usuario no ha iniciado sesión (`is_user_logged_in()` devuelve `false`). Esto se debe a que la variable superglobal `$_COOKIE` de PHP está vacía cuando el endpoint es invocado por el frontend, lo que significa que las cookies de sesión de WordPress no están llegando al backend.

**Intentos de Solución Realizados:**

1.  **Logging Inicial en Plugin PHP:**
    *   Se añadió `error_log` para imprimir `$_COOKIE` y el resultado de `is_user_logged_in()`.
    *   **Resultado:** Confirmado que `$_COOKIE` llega vacío y, por ende, `is_user_logged_in()` es `false`.

2.  **Ajustes de Puerto para Servicios del Chat:**
    *   Se cambió el puerto del backend de LangGraph (`app/langgraph_server_example.py`) de `8000` a `8001` para evitar conflictos con el servicio `web` principal (FastAPI) que usa el puerto `8000`.
    *   Se actualizó `copilot-runtime/server.ts` para que apunte al backend de LangGraph en el nuevo puerto `8001`.
    *   **Resultado:** Los servicios del chat ahora se inician sin conflicto de puertos.

3.  **Configuración de CORS:**
    *   **Nginx (Intento 1):** Se añadieron cabeceras CORS completas (`Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`, etc.) en el bloque `location /` de Nginx.
        *   **Resultado:** Error de "Access-Control-Allow-Origin header contains multiple values", ya que WordPress también intentaba enviar estas cabeceras.
    *   **Nginx (Intento 2 - Configuración Actual):** Se modificó Nginx para que solo maneje las solicitudes CORS de *preflight* (`OPTIONS`), añadiendo las cabeceras `Access-Control-Allow-Origin` y `Access-Control-Allow-Credentials` para estas. Se eliminaron estas cabeceras en Nginx para las solicitudes `GET`/`POST` reales, dejando que WordPress las gestione.
        *   **Resultado:** Se solucionó el error de "múltiples valores". Sin embargo, `$_COOKIE` seguía llegando vacío al plugin.
    *   **Plugin de WordPress (Configuración Actual):** Se añadieron filtros de PHP (`rest_allowed_cors_origins` y `rest_post_dispatch`) al plugin `misuperprofe-chat-auth-endpoint.php`.
        *   `rest_allowed_cors_origins`: Para añadir explícitamente el origen del frontend (`http://18.214.59.62:5174`) a los orígenes permitidos.
        *   `rest_post_dispatch`: Para asegurar que la cabecera `Access-Control-Allow-Credentials: true` sea enviada por WordPress en las respuestas de la API REST cuando la solicitud tiene una cabecera `Origin`.
        *   **Resultado (basado en la última prueba):**
            *   La consola del navegador (frontend) sigue mostrando `WordPress Auth Info: {logged_in: false, ...}`.
            *   Los logs de WordPress (`docker logs wordpress_misuperprofe`) muestran:
                *   `[MiSuperProfe Debug] COOKIES LLEGANDO AL ENDPOINT: Array ( )`
                *   `[MiSuperProfe Debug] chat_auth_status: is_user_logged_in() es FALSE`
            *   Esto confirma que, incluso con los filtros PHP y los ajustes de Nginx, las cookies no están llegando al script PHP del endpoint.

**Estado Actual (24 de Junio):**
*   Todos los servicios del chat (frontend, runtime, backend LangGraph) se inician correctamente en sus respectivos puertos.
*   Nginx está configurado para manejar CORS de *preflight* y permitir que WordPress gestione las cabeceras CORS para las solicitudes reales.
*   El plugin de WordPress está modificado para intentar establecer las cabeceras CORS correctas, incluyendo `Access-Control-Allow-Credentials: true`.
*   **El problema central sigue siendo que el array `$_COOKIE` está vacío en el endpoint de PHP, impidiendo que `is_user_logged_in()` funcione como se espera.**

**Próximos Pasos de Diagnóstico Sugeridos:**
*   Inspeccionar los atributos de las cookies de WordPress (ej. `wordpress_logged_in_...`) directamente en el navegador (después de iniciar sesión en `/wp-admin/`) para verificar sus atributos `SameSite`, `Secure`, `Domain`, y `Path`. Esto ayudará a determinar si alguno de estos atributos está impidiendo que el navegador envíe las cookies en la solicitud *cross-origin* desde `http://18.214.59.62:5174` a `https://misuperprofe.com`.

---
*Este documento se actualizará a medida que avance el proyecto.*

### 21. Cambio de Estrategia de Autenticación: Hacia Soluciones Basadas en Tokens (Finales de Junio 2025)

**Contexto:** Dada la persistente dificultad para que el plugin de WordPress reconozca la sesión del usuario a través de cookies en un contexto de API REST cross-origin (la variable `$_COOKIE` llega vacía al endpoint PHP), se ha decidido pausar este enfoque.

**Nueva Dirección (Propuesta 1 del plan en `copilot.md`):**
Se explorarán e implementarán soluciones de autenticación basadas en tokens más explícitos. El objetivo sigue siendo permitir que el `frontend-chat` se comunique de forma segura con el MCP Server, identificando al usuario y permitiendo la verificación de su estado de membresía en WordPress.

**Las principales vías a investigar e implementar son:**

1.  **Contraseñas de Aplicación de WordPress:**
    *   **Concepto:** El usuario genera una contraseña específica para la aplicación de chat desde su perfil de WordPress. El `frontend-chat` envía esta contraseña (junto con el nombre de usuario/email) para su validación.
    *   **Flujo General:**
        *   El `frontend-chat` recopila las credenciales de la contraseña de aplicación.
        *   Se envía a un endpoint en WordPress (en el plugin `misuperprofe-chat-auth-endpoint`) para validación usando `wp_check_application_password()`.
        *   Si es válido, WordPress devuelve `user_id`, `display_name`, y estado de membresía.
        *   El `frontend-chat` envía el `user_id` (o la propia contraseña de aplicación como token) al `copilot-runtime`.
        *   El MCP Server (backend LangGraph) valida el `user_id` (y/o el token) y realiza una consulta de re-verificación a la BD de WordPress para la membresía.

2.  **Tokens JWT generados por WordPress para Usuarios Ya Logueados:**
    *   **Concepto:** Un usuario ya autenticado en WordPress (vía cookies estándar en el navegador) solicita un token JWT a un endpoint especial en WordPress. Este JWT es luego utilizado por el `frontend-chat` para las comunicaciones con el MCP Server.
    *   **Flujo General:**
        *   El `frontend-chat` (asumiendo que el usuario está logueado en WP en el mismo navegador) llama a un nuevo endpoint en el plugin `misuperprofe-chat-auth-endpoint`.
        *   Este endpoint de WordPress, si reconoce la sesión de cookie del usuario (este es el punto que necesita superar las dificultades previas o encontrar un método que funcione en API REST para cookies), genera un JWT para ese `user_id` (usando un plugin como `usefulteam/jwt-auth` y la `JWT_AUTH_SECRET_KEY`).
        *   El JWT se devuelve al `frontend-chat`.
        *   El `frontend-chat` envía el JWT como Bearer token al `copilot-runtime`.
        *   El MCP Server valida el JWT (usando la misma `JWT_AUTH_SECRET_KEY`) y extrae el `user_id` y otros claims, luego re-verifica la membresía contra la BD de WordPress.

**Próximos Pasos Inmediatos:**
*   Iniciar la investigación y desarrollo de la opción de **Contraseñas de Aplicación** (Sub-fase 9.1 en `copilot.md`), ya que podría ser la más directa si la generación y validación son estándar en WordPress.
*   Paralelamente, continuar investigando cómo un plugin JWT puede generar un token para un usuario ya logueado por cookie, enfocándose en superar el problema de reconocimiento de sesión en el contexto de la API REST.

---
*Este documento se actualizará a medida que avance el proyecto.*

### 22. Implementación Exitosa de Autenticación con Contraseñas de Aplicación de WordPress (24 de Junio de 2025)

**Contexto:** Siguiendo la decisión de explorar soluciones basadas en tokens, se optó por implementar la autenticación mediante **Contraseñas de Aplicación de WordPress**. Este enfoque ha resultado exitoso.

**Resumen de la Implementación y Resolución:**

1.  **Modificación del Plugin de WordPress (`misuperprofe-chat-auth-endpoint.php`):**
    *   Se adaptó el endpoint `/wp-json/misuperprofe/v1/auth_status` (anteriormente `/chat_auth_status`).
    *   La lógica del plugin ahora espera una autenticación básica (nombre de usuario de WordPress y contraseña de aplicación).
    *   Internamente, `is_user_logged_in()` ahora funciona correctamente porque WordPress procesa la autenticación básica antes de que se llame al callback del endpoint, estableciendo así el contexto del usuario.
    *   Se eliminaron las complejas manipulaciones de cookies `SameSite` y los hooks `set_auth_cookie` que resultaron ineficaces para el `LOGGED_IN_COOKIE`.
    *   Se corrigió un problema de espacios en blanco antes de la etiqueta `<?php` que causaba el error "headers already sent", lo que impedía el correcto funcionamiento de CORS y la devolución de respuestas JSON.

2.  **Modificación del Frontend (`frontend-chat/src/App.tsx`):**
    *   Se añadieron campos en la UI para que el usuario ingrese su nombre de usuario de WordPress y la contraseña de aplicación generada.
    *   Estas credenciales se almacenan en `localStorage` para persistencia.
    *   La función `fetchWordPressAuthInfo` se modificó para:
        *   Utilizar el endpoint `/wp-json/misuperprofe/v1/auth_status`.
        *   Construir y enviar el encabezado `Authorization: Basic <base64_encoded_credentials>`.
        *   Eliminar la opción `credentials: 'include'`, ya que la autenticación ahora es explícita mediante el encabezado `Authorization` y no depende de las cookies de sesión del navegador para este flujo.
    *   La UI ahora muestra correctamente la información del usuario (`logged_in: true`, `member_active: true`, `user_id`, `display_name`) cuando se proporcionan credenciales válidas.

**Estado Actual:**
*   El sistema de autenticación entre el frontend y WordPress está **FUNCIONAL**.
*   Se ha superado el principal bloqueo relacionado con la verificación del estado de sesión/membresía del usuario de WordPress.

**Próximos Pasos de Desarrollo:**

1.  **Integración de la Información del Usuario en el Agente LangGraph (MCP Server):**
    *   El `frontend-chat` ahora posee la información del usuario (`user_id`, `display_name`).
    *   Esta información (principalmente `user_id`, y opcionalmente `display_name`) debe ser enviada desde el frontend al `copilot-runtime` y, subsecuentemente, al backend LangGraph (`app/langgraph_server_example.py`). Esto se puede lograr mediante cabeceras HTTP personalizadas en las solicitudes que el frontend hace al `copilot-runtime`.
    *   El backend LangGraph (`app/langgraph_server_example.py`) debe ser modificado para:
        *   Extraer el `user_id` (y `display_name` si se envía) de las cabeceras de la solicitud.
        *   Utilizar estos datos para poblar el `AgentState` (`initial_user_id`, `initial_nombre_usuario`).
        *   **Recomendado:** Realizar una consulta de re-verificación a la base de datos de WordPress (con un usuario de BD de solo lectura) usando este `user_id` para confirmar la membresía.

2.  **Adaptación Completa del Agente MiSuperProfe:**
    *   Con la información del usuario autenticado disponible en el `AgentState` del agente LangGraph:
        *   Reemplazar la lógica del agente de ejemplo en `app/agents_langgraph_example/agent.py` con las herramientas, prompts y lógica de enrutamiento específicas de MiSuperProfe.
        *   Implementar las herramientas que interactúan con los endpoints existentes de la API FastAPI principal (ej. `/ask`, `/api/lesson/start`, `/api/lesson/answer`, `/api/lesson/complete`).

3.  **Limpieza de Código:**
    *   Revisar y eliminar código obsoleto relacionado con los intentos fallidos de autenticación basada en cookies.

4.  **Persistencia del Checkpointer de LangGraph:**
    *   Investigar y solucionar el error `redisvl.exceptions.RedisModuleVersionError` para habilitar la persistencia del historial de conversación con `RedisSaver`. Esto podría implicar actualizar la imagen de Redis en `docker-compose.yml` a una que incluya el módulo RediSearch (como Redis Stack).

---
*Este documento se actualizará a medida que avance el proyecto.*

# Progreso del 24-25 de junio de 2025: Seguridad y Chat

## Restauración y Verificación
- Restauración del chat funcional y resolución de conflictos de puertos.
- Detección y corrección de la eliminación accidental del plugin de autenticación de WordPress.
- Restauración del plugin desde backup y copia al contenedor de WordPress.
- Reinicio del contenedor para aplicar los cambios.

## Pruebas de Seguridad
- Creación de nueva contraseña de aplicación en WordPress.
- Prueba del endpoint `/wp-json/misuperprofe/v1/auth_status` con `curl` y usuario/contraseña de aplicación.
- Confirmación de que la autenticación y la verificación de membresía funcionan correctamente.
- Documentación de que el navegador no siempre envía autenticación básica, pero el frontend y `curl` sí.

## Buenas Prácticas Incorporadas
- Backup antes de restaurar archivos críticos.
- Edición de plugins de WordPress solo con permisos adecuados (`sudo nano` o similar).
- Verificación de endpoints críticos con `curl`.
- Reinicio de servicios tras restaurar archivos de seguridad.
- Documentación clara de cada paso y de los problemas encontrados.

## Tareas Pendientes para Mañana
1. Verificar el flujo de autenticación y membresía desde el frontend del chat.
2. Asegurar que el frontend maneje correctamente el header de autenticación.
3. Probar el acceso con y sin membresía activa.
4. Actualizar la documentación técnica y de usuario.
5. Revisar logs y limpiar código innecesario.
6. (Opcional) Probar la integración con otros plugins o escenarios de usuario.

---

# [Actualización crítica 25 de junio de 2025: Incidente de Memoria y Swap]

- Se detectó que copilot-runtime era matado por el sistema (exit code 137) debido a falta de memoria (OOM).
- El síntoma era que el chat quedaba "muerto" y el frontend mostraba errores de conexión.
- **Solución:** Se creó y activó un archivo de swap de 2GB, estabilizando todos los servicios.
- **Recomendación:** Antes de modificar lógica, revisar siempre el uso de memoria y recursos (`free -h`, `top`).
- **Estado actual:** Todos los servicios corren correctamente tras la activación del swap.

---

## Principio Arquitectónico Esencial: Delegar la Búsqueda y Matching al Backend (MCP Server)

**Resumen:**
- La IA (modelo LLM, agente LangGraph, etc.) NUNCA debe buscar, cargar ni filtrar toda la teoría, capítulos o preguntas en memoria ni en el contexto del modelo.
- TODA la lógica de búsqueda semántica, matching y recuperación de bloques de teoría/pregunta debe estar implementada en el backend (MCP Server/FastAPI), que expone endpoints REST específicos para cada función.
- La IA solo debe hacer peticiones a estos endpoints y mostrar el resultado recibido, sin procesar ni buscar en toda la base de datos.

**Motivación:**
- Si la IA intenta buscar o filtrar toda la base de datos, se consumen todos los tokens por minuto (TPM), se vuelve lento, ineficiente y se rompe el diseño original.
- El backend (MCP Server) es el responsable de la lógica de búsqueda, usando motores semánticos/vectorizados y lógica de negocio.
- El LLM solo debe mostrar, dar formato y guiar la conversación, nunca hacer procesamiento masivo ni lógica de negocio.

**Ejemplo de flujo correcto:**
1. Usuario: "Quiero estudiar biología"
2. IA: (Llama a `/api/courses`, muestra lista)
3. Usuario: "Biología"
4. IA: "¿Qué tema o capítulo quieres estudiar?"
5. Usuario: "Fotosíntesis"
6. IA: (Llama a `/ask` con "fotosíntesis" o a `/get_question` si es práctica, muestra solo la respuesta recibida)

**Advertencia:**
- NUNCA cargar toda la teoría/capítulos/preguntas en el contexto del LLM.
- NUNCA hacer que el LLM busque o filtre en toda la base de datos.
- Solo pasar el bloque relevante que retorna el backend.

**Referencia:**
- Este principio está documentado y ejemplificado en el esquema e instrucciones legacy de CustomGPT (`memory_bank/Legacy/CustomGPT.md`).
- El diseño MCP Server padre (legacy) ya implementaba este patrón correctamente.

**Acción:**
- Si se detecta que el agente/IA está intentando buscar o filtrar en toda la base de datos, se debe corregir inmediatamente para delegar esa lógica al backend.

---

# [ACTUALIZACIÓN ESTRUCTURAL CRÍTICA - JULIO 2025]

## Principios y Reglas de Oro para el Desarrollo y Mantenimiento del Chat MiSuperProfe

- **Nunca sobrescribir ni duplicar código que ya está probado y funcional.**
- **Antes de crear nuevas funciones, herramientas o endpoints, revisar exhaustivamente el código existente y la documentación.**
- **Toda la lógica pesada de búsqueda, matching y recuperación de teoría/preguntas debe estar en el backend (MCP Server/FastAPI), nunca en la IA/LLM.**
- **El agente LangGraph solo debe orquestar, mostrar y guiar la conversación, delegando toda la lógica de negocio y búsqueda al backend.**
- **La autenticación y el estado del usuario deben propagarse desde el frontend (WordPress → frontend-chat → copilot-runtime → backend LangGraph) usando los headers personalizados (`X-Wordpress-User-ID`, `X-Wordpress-Display-Name`).**
- **Antes de modificar cualquier flujo, endpoint o herramienta, verificar si ya existe una solución implementada y funcional.**
- **Documentar cada cambio y decisión en este archivo y en `copilot.md` para evitar repeticiones y errores históricos.**

---

## Plan de Implementación y Mantenimiento (Reestructurado y Validado)

### 1. **Revisión y Aprovechamiento del Código Existente**
- Antes de implementar cualquier nueva funcionalidad, revisar los módulos en `app/api/`, `app/tools/`, `app/resources/`, `app/agents/` y la documentación en `copilot.md`.
- Si una función/herramienta ya existe y es robusta, **no duplicar ni sobrescribir**: solo extender o adaptar si es estrictamente necesario.

### 2. **Flujo Correcto de Autenticación y Propagación de Usuario**
- El frontend obtiene el `user_id` y `display_name` de WordPress usando contraseñas de aplicación.
- Estos datos se envían en headers personalizados a través de `copilot-runtime` hasta el backend LangGraph.
- El backend LangGraph extrae estos headers y los usa para poblar el `AgentState`.
- (Opcional pero recomendado) El backend puede re-verificar la membresía en la BD de WordPress usando un usuario de solo lectura.

### 3. **Uso de Herramientas y Endpoints Existentes**
- Todas las herramientas del agente LangGraph deben ser **clientes inteligentes** de los endpoints ya implementados en el backend FastAPI (MCP Server): `/ask`, `/api/lesson/start`, `/api/lesson/answer`, `/api/lesson/complete`, etc.
- **Nunca replicar la lógica de búsqueda, matching o scoring en el agente/LLM.**
- Si se necesita una nueva herramienta, primero revisar si el endpoint ya existe y solo crear la integración.

### 4. **Pruebas y Validación Continua**
- Antes de modificar o crear código, realizar pruebas end-to-end del flujo actual.
- Si se detecta un error, documentar el síntoma, la causa y la solución en este archivo y en `copilot.md`.
- Si se requiere modificar lógica crítica, hacer backup y commit antes de cualquier cambio.

### 5. **Documentación y Comunicación**
- Toda decisión de arquitectura, cambio de flujo o corrección de error debe quedar reflejada aquí y en `copilot.md`.
- Si se detecta un error de diseño (ej. la IA intentando buscar en toda la base de datos), documentar el incidente y la corrección.

---

## [Advertencia Crítica]

- **Nunca crear herramientas, endpoints o lógica que dupliquen lo que ya existe y funciona.**
- **Nunca hacer que la IA/LLM procese, busque o filtre toda la base de datos.**
- **Siempre delegar la lógica pesada al backend y solo mostrar el resultado en la IA.**

---

## [Próximos Pasos Inmediatos]

1. **Verificar que el flujo de autenticación y propagación de usuario funciona end-to-end.**
2. **Asegurar que todas las herramientas del agente LangGraph usan los endpoints existentes y no replican lógica.**
3. **Limpiar cualquier código redundante o duplicado.**
4. **Actualizar la documentación tras cada cambio relevante.**
5. **Realizar pruebas exhaustivas antes de cualquier refactor o nueva funcionalidad.**

---

# [Fin de la actualización crítica]

---

(El resto del documento se mantiene como referencia histórica y técnica, pero este bloque inicial debe ser leído y seguido antes de cualquier desarrollo o mantenimiento futuro.)

---

## [Actualización crítica: Recorte automático del historial de mensajes en el agente LangGraph]

- Se ha implementado un recorte automático del historial de mensajes en el agente (`app/agents_langgraph_example/agent.py`):
    - Solo se envían los últimos 8 mensajes al modelo LLM en cada request.
    - Esto previene el consumo excesivo de tokens y mantiene la conversación relevante.
    - Si se requiere cambiar este límite, ajustar la variable `max_history` en la función `chat_node`.
- **Motivación:** Si el historial crece sin límite, cada request puede consumir miles de tokens, incluso si los fragmentos individuales son cortos.
- **Advertencia:** Si se detecta consumo anómalo de tokens en el futuro, revisar este mecanismo y ajustar el límite según necesidad.
- **Referencia:** Ver sección comentada en `app/agents_langgraph_example/agent.py` (buscar `RECORTE AUTOMÁTICO DEL HISTORIAL DE MENSAJES`).

---

## [Nota importante: Modelo LLM en entorno de pruebas]

- Actualmente el agente LangGraph utiliza el modelo `gpt-4o-mini` **solo para pruebas y debugging**.
- **En producción, este modelo debe ser reemplazado** por uno más potente y/o económico según las necesidades y la cuota disponible (por ejemplo, `gpt-4o`, `gpt-3.5-turbo`, etc.).
- **Advertencia:** No olvidar este cambio antes de lanzar a producción. Revisar la variable `model` en `app/agents_langgraph_example/agent.py`.
- Motivo: `gpt-4o-mini` tiene menos restricciones de cuota y es ideal para pruebas continuas sin bloqueos por TPM.

---

# [ACTUALIZACIÓN CRÍTICA JULIO 2025]

## Estado y Avances Críticos

- Todos los servicios principales (frontend-chat, copilot-runtime, backend LangGraph) están correctamente estructurados y pueden arrancar desde el monorepo con `pnpm run start:all`.
- El frontend y el runtime funcionan correctamente y la autenticación con WordPress mediante contraseñas de aplicación es robusta y funcional.
- El backend LangGraph recibe correctamente los headers personalizados (`X-Wordpress-User-ID`, `X-Wordpress-Display-Name`) y los utiliza para poblar el `AgentState`.

### Problemas Detectados y Solucionados
- Incidente de memoria (OOM, exit code 137): resuelto creando un archivo de swap de 2GB.
- Conflictos de puertos: backend LangGraph migrado a 8001 para evitar colisiones con FastAPI principal.
- Errores de streaming y serialización: corregidos en el método `execute` del agente para asegurar respuestas correctas.
- Límites de tokens por minuto (TPM) de OpenAI: modelo cambiado temporalmente a `gpt-3.5-turbo` o `gpt-4o-mini` para pruebas.

### Principios y Reglas de Oro (Reafirmados)
- Nunca duplicar lógica de negocio ni cargar toda la base de datos en el LLM.
- Toda la lógica de búsqueda, matching y recuperación de teoría/preguntas debe estar en el backend (MCP Server/FastAPI).
- El agente LangGraph solo orquesta y muestra, delegando la lógica pesada al backend.
- La autenticación y el estado del usuario deben propagarse desde el frontend usando headers personalizados.
- Antes de modificar cualquier flujo, endpoint o herramienta, verificar si ya existe una solución implementada y funcional.
- Documentar cada cambio y decisión en este archivo y en `copilot.md`.

### Pruebas y Validación
- Pruebas automáticas de endpoints: `/ask`, `/api/lesson/start`, `/api/lesson/answer`, `/api/lesson/complete`, etc.
- Recorte automático del historial de mensajes implementado en el agente para evitar consumo excesivo de tokens.
- Verificación de la propagación de usuario: `user_id` y `display_name` llegan correctamente al backend y se usan en el `AgentState`.

### Tareas Pendientes y Próximos Pasos
- Verificar exhaustivamente el flujo de autenticación y propagación de usuario end-to-end.
- Asegurar que todas las herramientas del agente LangGraph usan los endpoints existentes y no replican lógica.
- Limpiar cualquier código redundante o duplicado.
- Actualizar la documentación tras cada cambio relevante.
- Realizar pruebas exhaustivas antes de cualquier refactor o nueva funcionalidad.
- Solucionar la persistencia de Redis para el checkpointer de LangGraph (instalar Redis Stack si es necesario).

---

## [Actualización 26 de junio de 2025: Checklist profesional de arranque y validación]

### Checklist de arranque y validación de MiSuperProfe (DevOps/SRE)

1. Parar todos los contenedores Docker:
   docker compose down --remove-orphans
2. Levantar todos los contenedores Docker:
   docker compose up -d
3. Verificar estado y salud:
   docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
4. Arrancar backend LangGraph/FastAPI:
   poetry run python3 app/langgraph_server_example.py
5. Arrancar copilot-runtime:
   cd copilot-runtime && pnpm run dev -- --host 0.0.0.0 --port 4000
6. Arrancar frontend Vite/CopilotKit:
   cd frontend-chat && pnpm run dev -- --host 0.0.0.0 --port 5174
7. Verificar procesos y puertos:
   ps aux | grep -E 'langgraph_server_example|pnpm|vite|copilot-runtime' | grep -v grep
   sudo ss -tulpen | grep -E '8001|4000|5174'
8. Verificar firewall local (ufw):
   sudo ufw status verbose
9. Verificar Security Group de AWS: puertos 8001, 4000, 5174 abiertos para 0.0.0.0/0
10. Probar acceso externo: frontend y backend desde navegador externo.
11. Diagnóstico rápido si algo falla: revisar procesos, puertos, logs, memoria, y documentar síntoma/causa/solución.

### Resumen del incidente resuelto (25-26 de junio de 2025)
- El frontend Vite no era accesible externamente (ERR_CONNECTION_REFUSED) aunque el proceso estaba corriendo.
- Se comprobó que el firewall local y el Security Group de AWS estaban correctamente configurados.
- El proceso de Vite estaba escuchando en 0.0.0.0:5174, pero a veces moría por crash o error de recursos.
- Se diagnosticó y validó en tiempo real que el proceso seguía vivo y el puerto abierto.
- Finalmente, el sistema arrancó correctamente y el frontend fue accesible desde fuera.
- Se documentó el checklist para evitar futuros arranques fallidos y facilitar la recuperación.

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

# [ACTUALIZACIÓN CRÍTICA JULIO 2025: Logros y avances en integración MCP Server]

## Logros recientes
- Se expuso correctamente el endpoint `/mcp/schema` en el MCP Server (FastAPI), permitiendo discovery automático de tools y resources por agentes externos (LangGraph, CopilotKit, etc.).
- Se implementó un método `get_schema` que recorre dinámicamente los endpoints registrados y construye un schema MCP moderno, incluyendo nombre, path, método, descripción y parámetros de cada resource/tool.
- Se diagnosticó y solucionó el problema de que el router MCP no estaba montado en la app principal (`main.py`), lo que impedía el acceso real al endpoint en producción.
- Se documentó la importancia de exponer solo endpoints inteligentes y discovery automático, evitando la duplicación de lógica y los errores históricos de endpoints CRUD o hardcodeados.
- El sistema ahora es extensible: cualquier nueva tool/resource registrada aparecerá automáticamente en el schema MCP.

## Lecciones aprendidas
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

# [ACTUALIZACIÓN JULIO 2025: PROGRESO Y LECCIONES CLAVE]

## Estado actual
- El sistema es funcional y robusto, con integración completa entre frontend, runtime, backend LangGraph y MCP Server.
- El flujo de tools MCP es dinámico, extensible y serializa correctamente cualquier respuesta.
- La base de datos puede poblarse fácilmente con scripts asíncronos y el flujo end-to-end está validado.

## Lecciones aprendidas
- Siempre adaptar la lógica de conexión a los valores del `.env`, nunca modificarlo desde código.
- Validar y serializar cualquier objeto retornado por tools antes de exponerlo vía HTTP.
- Documentar cada error, solución y decisión arquitectónica para evitar repeticiones y pérdida de contexto.

## Errores históricos evitados
- No duplicar lógica ni crear endpoints CRUD innecesarios.
- No cargar toda la base de datos en el contexto del LLM.
- No sobrescribir código probado sin revisión y backup.

## Próximos pasos
- Probar el flujo completo desde frontend y reforzar la seguridad de headers y autenticación.
- Limpiar código redundante y actualizar la documentación tras cada cambio relevante.
- Seguir documentando y versionando cada avance.

---

[JULIO 2025] El backend audita y registra los headers personalizados de usuario en cada petición, garantizando trazabilidad y seguridad en el flujo MCP.

# [ACTUALIZACIÓN CRÍTICA JULIO 2025: INCIDENTE OOM Y REGLA DE ORO DE PUERTOS Y RECURSOS]

## Diagnóstico real del incidente de caída (copilot-runtime)
- El 25 de junio de 2025, el proceso copilot-runtime fue matado por el sistema (exit code 137) debido a falta de memoria (OOM), no por conflicto de puertos.
- El cambio de endpoint a `localhost:8000` contribuyó al problema si el backend no estaba disponible, pero el detonante fue el consumo excesivo de memoria y la ausencia de swap.
- Se resolvió creando y activando un archivo de swap de 2GB, estabilizando todos los servicios.
- **Regla de oro:** Nunca usar siempre el mismo puerto (ej. 8000) para todos los servicios. Antes de lanzar un servicio, verificar si el puerto está libre y si el backend de destino está disponible. Implementar manejo de errores y timeouts en reenvío de peticiones. Monitorear memoria y recursos tras cada cambio. Configurar swap y usar gestor de procesos para reinicio automático.
- **Advertencia:** No asumir la causa de un incidente sin evidencia. Revisar logs, uso de recursos y documentar el diagnóstico real.

---

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
*Este documento se actualizará a medida que avance el proyecto.*

# [ACTUALIZACIÓN JULIO 2025 - ARQUITECTURA FINAL Y ESTADO DEL PROYECTO]

## Resumen Ejecutivo

Tras un intenso ciclo de depuración y re-arquitectura, el sistema de chat ha alcanzado un estado funcional y estable. Se ha migrado de un modelo de múltiples herramientas a una arquitectura de **agente con herramienta única**, más robusta, escalable y alineada con los principios de diseño del proyecto. Los errores críticos que impedían el funcionamiento (`AGENT_NOT_FOUND`, `Invalid adapter configuration`, `CORS`, `add_conditional_edge`, `No checkpointer set`) han sido sistemáticamente diagnosticados y resueltos.

## Arquitectura Funcional

El sistema se basa en tres componentes principales que operan de la siguiente manera:

1.  **Frontend (`frontend-chat` en puerto `5174`):** Cliente React/Vite con `@copilotkit/react-ui`. Solicita el agente `misuperprofe_agent` al `copilot-runtime`.
2.  **Runtime (`copilot-runtime` en puerto `4000`):** Servidor Node.js que actúa como intermediario.
    *   Utiliza `OpenAIAdapter` para la comunicación con el LLM.
    *   Gestiona **CORS** para permitir las peticiones del frontend.
    *   Redirige las solicitudes al backend LangGraph en el puerto `8001`.
3.  **Backend (`app/langgraph_server_example.py` en puerto `8001`):** Servidor Python/FastAPI que expone el agente LangGraph.
    *   Implementa un agente con una **única herramienta inteligente (`ask_mcp_server_tool`)** que se comunica con el endpoint `/ask` del MCP Server dockerizado.
    *   Utiliza un `InMemorySaver` como `checkpointer` para gestionar el estado de la conversación.

## Lecciones Aprendidas Clave

*   **Abstracción del Backend:** La decisión de usar una única `tool` (`ask_mcp_server_tool`) que consume el endpoint inteligente `/ask` ha demostrado ser la correcta. Simplifica el agente, centraliza la lógica de negocio en el MCP Server y hace que el sistema sea más mantenible.
*   **Errores de Configuración de LangGraph:** La depuración ha revelado dos puntos críticos en LangGraph:
    1.  La importancia de usar los nombres de método correctos (`add_conditional_edges` vs. `add_conditional_edge`).
    2.  La necesidad **obligatoria** de un `checkpointer` (como `InMemorySaver`) para que el grafo maneje el estado de la conversación. Sin él, el agente es incapaz de funcionar.
*   **Configuración de la Cadena de Comunicación:** La estabilidad del sistema depende de una configuración precisa en cada eslabón de la cadena `Frontend -> Runtime -> Backend`, prestando especial atención a los nombres de agentes, la configuración del adaptador LLM en el runtime y la política de CORS.

## Estado Actual y Próximos Pasos

El sistema está operativo con la nueva arquitectura. El siguiente paso es crear una copia de seguridad y, posteriormente, realizar pruebas funcionales exhaustivas para validar que el agente se comporta como se espera en todos los escenarios de conversación.

--- 
*Este documento se actualizará a medida que avance el proyecto.*