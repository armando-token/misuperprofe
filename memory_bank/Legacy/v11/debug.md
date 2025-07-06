# Plan de Recuperación y Prevención de Errores para el Agente LangGraph

## Resumen de la Situación

Tras implementar los cambios sugeridos en el agente **LangGraph** para que utilizara correctamente la herramienta `search_courses`, surgieron múltiples **fallos críticos** no relacionados con el código del agente en sí, sino con el **entorno de ejecución**. Entre ellos se encontraron conflictos de puertos, corrupción del entorno Python (fallos con Poetry, entornos virtuales y Docker) y endpoints mal configurados. Estos problemas impidieron que el agente funcionara correctamente a pesar de que el código había sido corregido. A continuación se detalla un plan paso a paso para **solucionar estos problemas de forma adecuada**, evitar su recurrencia y asegurar el éxito en la implementación.

## 1. Reinicio del Entorno desde Cero (Nuevo Servidor Limpio)

Dado el nivel de corrupción identificado en el sistema anfitrión actual, la solución más segura y profesional es **provisionar una nueva instancia de servidor** con un entorno limpio. Esto garantiza que partimos de una base estable y predecible, evitando pelear contra configuraciones rotas del sistema operativo actual. **Antes de desechar la máquina actual, realiza copias de seguridad** de cualquier dato necesario (por ejemplo, archivos de contenido, base de datos o cambios de código no versionados).

Pasos para configurar el nuevo entorno correctamente:

* **Crear una nueva instancia** con una imagen base conocida (por ejemplo, Ubuntu 20.04/22.04 LTS limpia).
* **Actualizar el sistema base**: `sudo apt update && sudo apt upgrade -y`. Instalar utilidades esenciales: `git`, `curl`, `build-essential`, etc. (como ya se hizo originalmente).
* **Instalar Python y dependencias**: Asegúrate de tener instalada la versión adecuada de Python (por ejemplo, Python 3.10) junto con herramientas de desarrollo: `python3-dev`, `python3-venv`, etc.. Esto provee un entorno consistente para construir entornos virtuales o usar Poetry sin conflictos.
* **Instalar Redis y PostgreSQL** (si no se usan contenedores para ellos): En caso de que en la arquitectura se usen servicios locales para la base de datos o caché, instalarlos y configurarlos (tal como se detalla en la documentación de progreso). Si se usarán contenedores Docker para estos (como sugiere la arquitectura original), simplemente asegúrate de que el Docker host esté limpio y listo.

Con un servidor nuevo y limpio, evitamos heredar los problemas inexplicables del anterior (p. ej., entornos virtuales que no encuentran librerías instaladas). Este **borrón y cuenta nueva** sigue el estándar industrial: cuando un sistema muestra corrupción profunda, se reconstruye en lugar de parchearlo interminablemente.

## 2. Despliegue Correcto del Código Fuente en el Nuevo Entorno

Una vez listo el servidor limpio, procede a **desplegar el código de la aplicación**:

1. **Obtener el código fuente**: Clona el repositorio original (`git clone https://github.com/MiSuperProfe/misuperprofev10.1.git`) o copia los archivos de código desde la copia de seguridad proporcionada (`backup_codigo_fuente.zip`). Asegúrate de ubicar el código en la misma estructura esperada (por ejemplo, `/home/ubuntu` según las notas de instalación). Verifica que los archivos claves (`app/agents/agent.py`, `app/langgraph_server_example.py`, etc.) estén presentes y contengan las correcciones realizadas.

2. **Configurar variables de entorno (.env)**: Copia el archivo de ejemplo (`env.example`) a `.env` en la raíz del proyecto y edítalo con las credenciales y configuraciones correctas. **Presta especial atención a las URLs y puertos** en este archivo:

   * **No uses** valores hardcodeados de `localhost` o asumir siempre puerto 8000. Siguiendo la regla de oro del proyecto, estos deben ser configurables y apuntar al host correcto. Por ejemplo, si hay una variable para la URL de la API del MCP Server, configúrala con la IP pública del servidor (`18.214.59.62:8000` según la documentación) en lugar de `localhost`. Esto evitará errores de *“name resolution”* si el agente intenta resolver un nombre de host incorrecto.
   * Asegúrate de que el **prefijo de la API (`API_V1_STR`)** esté considerado. Según el código, el backend expone sus endpoints bajo un prefijo `/api/v1/` automático. Verifica si en el `.env` o configuración hay algo como `API_V1_STR="/api/v1"` y que las herramientas del agente lo tengan en cuenta (más sobre esto en el siguiente punto).

3. **Instalar dependencias con Poetry (o pip)**: Dado que originalmente el proyecto utiliza Poetry, se recomienda continuar con esa herramienta en el entorno nuevo (para mantener consistencia con scripts y comandos existentes).

   * **Instalar Poetry**: `curl -sSL https://install.python-poetry.org | python3 -` (ya realizado antes). Añade Poetry al PATH si es necesario (`export PATH="$HOME/.local/bin:$PATH"`).
   * **Crear el entorno virtual e instalar**: Posiciónate en el directorio del proyecto (donde está `pyproject.toml`) y ejecuta `poetry install`. Esto creará un nuevo entorno virtual aislado y descargará todas las dependencias según el lockfile. En un sistema limpio no deberías volver a ver el error de “python not found” de Poetry. Si apareciera algún problema:

     * Verifica la versión de Python por defecto (`python3 --version`) y que Poetry la esté usando. Puedes forzar un intérprete específico con `poetry env use /usr/bin/python3.10` (ajusta la ruta/version según corresponda) si fuese necesario.
     * Asegúrate de **no interrumpir la instalación** y de tener conexión a internet para bajar paquetes.
   * **Alternativa con pip/venv**: Solo si Poetry diera problemas insalvables (poco probable en un sistema limpio), puedes optar por un entorno virtual manual. Por ejemplo: `python3 -m venv .venv && source .venv/bin/activate` seguido de `pip install -r requirements.txt` (tendrías que generar un `requirements.txt` del `pyproject.toml` si no lo tienes). En principio, mantente en Poetry para no desalinear el flujo de trabajo con la documentación del proyecto.

4. **Verificar instalación**: Tras instalar, comprueba que el entorno contiene los paquetes necesarios:

   * Ejecuta `poetry run pip list` y verifica que aparecen paquetes clave como `copilot_kit`, `langgraph`, etc. La ausencia de alguno explicaría errores de importación.
   * Incluso puedes hacer una prueba rápida: `poetry run python -c "import copilot_kit; import langgraph; print('OK')"` para confirmar que los módulos se importan sin error. En un entorno limpio, esto debe funcionar (en la máquina anterior un error crítico fue que `ModuleNotFoundError` surgía pese a que el paquete figuraba instalado, síntoma de corrupción del entorno).

## 3. Configuración Correcta de Puertos y Comunicación Entre Servicios

Con el código desplegado y las dependencias listas, hay que **iniciar los servicios respetando los puertos y configuraciones de red definidas en la arquitectura**. Los pasos clave son:

* **Levantamiento de servicios Docker base**: Según el **checklist de arranque**, los contenedores Docker (MCP Server, PostgreSQL, Redis, WordPress, etc.) se inician con `docker compose up -d`. Haz esto primero en el nuevo servidor y asegúrate de que todos estén *Up* y *healthy* (`docker ps` debería mostrarlos activos).
* **Asignación correcta de puertos**: **No intentes ejecutar el agente LangGraph en el puerto 8000**, ya que este está reservado para el MCP Server dentro de Docker. El agente **debe usar el puerto 8001** (como indica la documentación). En la instancia anterior, ejecutar el agente en 8000 causó un conflicto de puertos con el contenedor FastAPI existente y llevó a terminar accidentalmente ese proceso crítico. Para evitar esto en adelante:

  * **Sigue la documentación de puertos al pie de la letra**. El agente va en 8001, Copilot runtime en 4000, etc., tal como en el mapa de servicios. No asumas puertos ni los fuerces por costumbre; verifica antes de lanzar un servicio que el puerto esté libre.
  * Si un puerto esperado estuviera ocupado (por ejemplo, si algo inesperado corre en 8001), **no mates procesos a ciegas**. Identifica primero qué ocupa el puerto (`sudo lsof -i:8001`) y procede según corresponda. En particular, si descubres que el ocupante es Docker (p.ej., un contenedor usando ese puerto), **no mates un proceso del host**; reinicia o reconfigura el contenedor en su lugar. Esta disciplina previene apagar servicios esenciales por error.
* **Usar la IP pública para conexiones internas**: Asegúrate de que el agente LangGraph se comunique con el MCP Server usando la **IP del servidor (18.214.59.62)** y no `localhost`. Por ejemplo, si la herramienta del agente necesita llamar a `http://<MCP_SERVER>/api/v1/loquesea`, esa URL debe contener la IP o nombre de host correcto. Esto es crítico si en el futuro el agente corre en otro host o contenedor distinto; incluso en la misma máquina, seguir esta regla evitará confusiones de resolución de nombres. En la práctica, en el nuevo entorno puedes utilizar temporalmente `http://18.214.59.62:8000` para las llamadas del agente (dado que el Security Group de AWS ya permite esos puertos). Esta configuración normalmente se define en variables de entorno o en la configuración de la herramienta; revísalas para ajustar el host adecuado.

## 4. Corrección de Endpoints y Lógica de Herramientas del Agente

Con el entorno estable, debemos asegurarnos de que la **lógica del agente LangGraph y sus herramientas apunten a endpoints válidos** en el MCP Server, evitando los errores 404 observados previamente. Durante las pruebas se descubrió que las herramientas del agente estaban llamando a rutas incorrectas (por ejemplo, `/ask` o `/api/courses` sin prefijo), las cuales resultaban en 404 porque el backend realmente expone dichas funcionalidades bajo el prefijo `/api/v1`. Para resolver este aspecto:

* **Actualizar las URLs de las tools del agente**: Revisa el código de definición de cada herramienta LangGraph que haga llamadas HTTP. Asegúrate de que usen el endpoint completo correcto, incluyendo `/api/v1/`. Por ejemplo:

  * La herramienta de listar cursos disponibles (`list_available_courses_tool`) debería hacer petición a `http://18.214.59.62:8000/api/v1/api/courses` (según los hallazgos, este endpoint existe y devuelve la lista real de cursos). En la auditoría más reciente, se confirmó que esta tool **ya se ajustó** para llamar a `/api/v1/api/courses` y cumple con el flujo correcto.
  * La herramienta de obtener teoría de un tema (`get_theory_for_topic_tool`) debe llamar a `http://18.214.59.62:8000/api/v1/ask` (endpoint inteligente de consulta) en vez de alguna ruta inexistente. También se confirmó que ahora esta tool apunta a `/api/v1/ask` y cumple su función correctamente.
  * Cualquier otra herramienta debe revisarse de manera similar. Por ejemplo, hubo una herramienta para listar capítulos por curso que intentaba llamar a un endpoint que no existía (`/api/courses/{curso}/chapters`); dicha herramienta ha sido **deshabilitada** (comentada) porque el enfoque correcto es obtener esa info por otros medios o endpoints existentes. No reactivarla a menos que se implemente su correspondiente endpoint en el backend.

* **Implementar endpoints mínimos si faltaran**: En caso de identificar que alguna funcionalidad necesaria no tiene un endpoint en el MCP Server, implementa uno nuevo **en el backend FastAPI**, en lugar de hacer que el agente acceda directamente a la base de datos. La filosofía de la arquitectura indica que el LLM **no debe replicar la lógica de negocio ni hacer consultas directas a DB**, sino delegar al backend mediante endpoints inteligentes. Por ejemplo, si se necesitara un endpoint `/api/v1/chapters` para que el agente liste capítulos de un curso, convendría crearlo en el MCP Server (a menos que la estrategia sea siempre obtener capítulos a través de respuestas de `/ask`). En nuestro caso, ya se vio que listar capítulos específicos directamente no encaja y se optó por no usar esa tool, priorizando usar `/ask` con la pregunta adecuada.

* **Verificar endpoints existentes**: Comprueba manualmente que los endpoints relevantes del MCP Server funcionan:

  * Haz un **curl de prueba** al endpoint de cursos: por ejemplo `curl http://18.214.59.62:8000/api/v1/api/courses` (o usando `POST` según esté definido). Debería devolver la lista de cursos reales (después de las correcciones de montaje de contenido aplicadas).
  * Prueba el endpoint `/api/v1/ask` con una consulta sencilla: por ejemplo, vía curl o usando una herramienta tipo Postman, envía un JSON con `{"query": "hola"}` a `http://18.214.59.62:8000/api/v1/ask` y verifica que responde (aunque sea un error de autenticación si requiere token, o una respuesta de ejemplo). Esto confirma que el backend principal está escuchando y procesando.
  * Si algún endpoint requerido devuelve 404, revalúa la ruta y prefijo. Puede ser necesario ajustar la configuración de rutas en el FastAPI principal. Recuerda que en el código FastAPI puede haber un `APIRouter` montado con prefix global (como `app.include_router(..., prefix=settings.API_V1_STR)`), causando que las rutas reales incluyan `/api/v1`. Este fue justo el caso que nos afectó antes: el agente llamaba `/ask` cuando en realidad debía ser `/api/v1/ask`.

Al corregir las herramientas del agente para alinearlas con los endpoints reales del backend, evitaremos los errores `404 Not Found` y nos aseguraremos de que el agente pueda **orquestar correctamente las respuestas** consultando al backend, en lugar de quedarse sin datos.

## 5. Inicio de Servicios y Pruebas de Integración

Con todo configurado, procede a **iniciar cada componente según el checklist de arranque**:

* Inicia el **Agente LangGraph** en el puerto 8001:

  ```bash
  OPENAI_API_KEY=<tu_clave> poetry run python3 app/langgraph_server_example.py
  ```

  Observa la salida y espera ver un mensaje del Uvicorn indicando que está corriendo en `http://0.0.0.0:8001`. Asegúrate de reemplazar la clave de API por la correcta antes de ejecutar. *Nota:* Si usas un entorno virtual manual en lugar de Poetry, activa el venv y ejecuta `python app/langgraph_server_example.py` en su lugar, pero en general Poetry facilita este paso.

* Inicia el **Copilot Runtime** (puerto 4000) y el **Frontend Vite** (puerto 5174) según las instrucciones de Arranque, preferiblemente en terminales separadas (o usando herramientas como `pm2` o `screen` para mantenerlos corriendo). Estos no tuvieron cambios, pero verifica que arrancan sin errores y escuchan en los puertos esperados.

* **Verificación básica de puertos**: Ejecuta `sudo ss -tulpen | grep -E '8000|8001|4000|5174'` y comprueba que cada servicio tiene su puerto **escuchando**. Deberías ver:

  * :8000 -> proceso docker (misuperapi)
  * :8001 -> proceso uvicorn (LangGraph)
  * :4000 -> proceso Node (copilot-runtime)
  * :5174 -> proceso Node (frontend Vite)
    Si alguno falta, retrocede y revisa logs de ese servicio para ver qué falló.

* **Prueba de conversación completa**: Abre el frontend en el navegador (`http://18.214.59.62:5174`) e inicia una conversación de prueba. Usa un prompt que fuerce al agente a usar una herramienta, por ejemplo: *"¿Qué cursos tienes disponibles?"*. Observa la interacción:

  * El frontend envía la solicitud al runtime (4000), que la reenvía al agente (8001).
  * El agente procesa con el LLM; cuando necesite datos de cursos, debería invocar la herramienta `list_available_courses_tool`.
  * Verifica mediante los **logs del agente LangGraph** que efectivamente se está llamando a la herramienta. Deberías ver eventos de `tool_call` en la consola de Uvicorn o en la salida estándar del agente indicando que intenta conectar al endpoint de cursos. Si aún tuvieras configurado el logger en nivel debug, podrías ver la URL siendo consultada. Confirma que no aparece más el error previo de *“Temporary failure in name resolution”* ni un 404, lo cual indicaría que la comunicación con el endpoint backend fue exitosa.
  * Comprueba que la respuesta del agente incorporó la información real (lista de cursos reales desde la base de datos). Si los cursos aparecen vacíos o simulados, revisa de nuevo la configuración del volumen de contenido y la respuesta del endpoint `/api/v1/api/courses`. Según la solución previa, ese endpoint debe devolver los cursos reales después de haber montado correctamente la carpeta `/content` en Docker.

* **Prueba de otra herramienta**: Por ejemplo: *"Muéstrame la teoría sobre la fotosíntesis"*. Esto debería desencadenar la herramienta `get_theory_for_topic_tool` que llama a `/api/v1/ask`. Revisa que el agente responde con un contenido que aparentemente proviene de la base de conocimientos (no un simple "No sé"). Si hay un error (por ejemplo, necesita autenticación), puede ser porque `/ask` requiere el token JWT de usuario:

  * Asegúrate de haber iniciado sesión o de proporcionar un token válido en el frontend (la configuración indica que el frontend CopilotKit propaga las credenciales de WordPress en headers). Si hace falta, genera un token JWT de prueba como se hizo previamente e incluye ese token en la URL al abrir el frontend (o en la petición).
  * Si el agente responde adecuadamente con teoría, ¡éxito! Habrás restablecido la funcionalidad deseada.

En este punto, el **flujo completo frontend → runtime → agente → backend** debería estar funcional y alineado. Los mensajes simples deben responder apropiadamente, y las consultas que requieren datos (cursos, teoría, etc.) deben ser contestadas gracias a las herramientas del agente que consumen los endpoints del backend.

## 6. Reglas y Mejores Prácticas para Evitar Futuros Problemas

Para mantener el sistema estable y evitar caer nuevamente en una espiral de fallos, es importante seguir una serie de **reglas de oro y buenas prácticas** que ya han surgido de las lecciones aprendidas en este proyecto:

* **Respeta la arquitectura de puertos y hostnames**: Nunca hardcodees valores de host o puerto en el código. Usa variables de entorno o configuración para estos parámetros, de forma que puedas cambiar entre entornos sin romper nada. En particular:

  * No asumas que *8000 es tu puerto libre universal*. En este proyecto, 8000 pertenece al MCP Server en Docker. Ajusta tu mentalidad a que **cada servicio tiene su puerto designado** y respeta eso. Siempre verifica disponibilidad antes de lanzar algo en un puerto específico.
  * No utilices `localhost` para comunicaciones cross-service, especialmente cuando interviene Docker; sigue la norma de utilizar la IP pública o el nombre de host correcto del servicio. Esto previene errores de resolución en entornos híbridos (host + containers).
* **Manejo cuidadoso de procesos y puertos**: Si un puerto está ocupado, no mates procesos sin identificar. Repite: **no "aplastes" un puerto a ciegas**. Usa herramientas (`lsof`, `ss`) para diagnosticar qué ocupa ese puerto:

  * Si es un contenedor Docker (como fue el caso del puerto 8000), interactúa con Docker (restart/stop) en lugar del SO. Matar procesos del sistema anfitrión en ese caso apaga el contenedor equivocado.
  * Si es un proceso del host y *sabes con certeza* que no es crítico, puedes detenerlo, pero siempre con comprensión de qué es. Esta prudencia hubiera evitado el incidente de bajar el MCP Server por error.
  * Documenta cada vez que debas liberar un puerto o reiniciar un servicio, para mantener un historial de acciones y razones.
* **Mantén el aislamiento del entorno Python**: Ahora que tienes un entorno funcional, **no instales paquetes globalmente ni manipules la instalación de Python del sistema**. Usa siempre el entorno virtual/Poetry configurado para cualquier comando relacionado con la aplicación:

  * Si necesitas instalar un nuevo paquete, agrégalo a `pyproject.toml` y usa `poetry add`, manteniendo la coherencia de dependencias.
  * Evita mezclar `pip install` global con el virtualenv activo; eso podría llevar a confusiones similares a las que vimos. En entorno limpio esto no debería pasar, pero la regla es: un entorno virtual aislado por proyecto.
  * Sé consciente de la versión de Python que usas. No instales múltiples versiones manualmente a menos que sepas manejarlas (pyenv, etc.), porque múltiples instalaciones mal gestionadas causan conflictos en `PATH` y `sys.path`.
* **Seguir las convenciones del proyecto**: La documentación (`Arranque.md`, `Changes.md`, etc.) existe por algo. Consúltala **antes de hacer cambios mayores**. Por ejemplo, si se hubiera revisado la checklist de arranque, no se habría lanzado Uvicorn en 8000 ya que allí claramente se indica 8001 para el agente. Asimismo, la documentación de cambios destaca errores pasados que no debemos repetir (hardcodear hosts, crear endpoints innecesarios, etc.). Revisar estos apuntes te hubiera alertado de los *pitfalls*:

  * En `Changes.md` se resalta que no hay que duplicar lógica ni crear endpoints redundantes para el LLM. Esto guía a que la solución era corregir las tools para usar los endpoints inteligentes existentes, no crear funciones ad-hoc en el agente ni endpoints REST duplicados.
  * También en `Changes.md` (actualizado a julio 2025) se añadieron **reglas de seguridad para puertos** después del incidente, como las mencionadas sobre no matar procesos sin identificar. Estas reglas ahora forman parte del conocimiento del proyecto y deben cumplirse estrictamente.
* **Logs y trazabilidad**: Mantén un nivel de logging suficiente para diagnosticar problemas rápidamente. Por ejemplo, habilitar logs debug en el agente LangGraph mientras pruebas te puede mostrar cada decisión (LLM output, herramienta elegida, request HTTP que lanza, etc.). Esto ayudó a encontrar el problema de resolución de nombres y los 404. Una vez en producción, puedes bajar el nivel, pero en desarrollo es tu mejor aliado.
* **No sobrescribir código probado**: Si algo ya estaba funcionando (por ejemplo, un módulo de autenticación o un endpoint), no lo reemplaces sin necesidad. Extiende o integra, pero evita *romper* funcionalidad existente. En nuestro caso, el agente LangGraph era nuevo, pero este principio aplica a futuros cambios.
* **Pruebas exhaustivas tras cambios**: Después de cada modificación importante, prueba el flujo completo end-to-end. Ya que ahora dispones de un entorno estable, utilízalo para testear cada caso de uso previsto:

  * ¿Puede el usuario listar cursos, entrar a un curso, obtener teoría de un tema, sin errores ni incoherencias?
  * ¿Qué sucede si pide algo fuera de lo común? El agente debería manejar errores graciosamente o decir que no sabe, pero no colgarse.
  * Prueba también con distintos estados: usuario no autenticado (debe fallar en endpoints protegidos), usuario autenticado (debe acceder a lo que corresponda), etc., para asegurar que la propagación de headers de autenticación funciona como se diseñó.

En resumen, **la clave del éxito a partir de aquí es la disciplina en la configuración y la adherencia a la arquitectura diseñada**. Has aprendido por las malas que invertir tiempo peleando con un sistema corrupto es tiempo perdido; más vale reinstalar y hacer bien las cosas desde el principio. También, que saltarse pasos de la documentación (como los puertos) o no verificar supuestos (como endpoints existentes) lleva a problemas en cascada. Aplicando estas lecciones, el agente LangGraph debería funcionar correctamente y de forma mantenible dentro de la plataforma MiSuperProfe.

Finalmente, una vez que todo funcione, considera realizar un **snapshot/backup** de esta nueva instancia en buen estado. Así, ante cualquier experimento futuro que salga mal, podrás volver rápidamente a un punto seguro sin reconstruir todo de cero nuevamente. ¡Buena suerte, y en adelante a programar con confianza en un entorno estable! 🚀
