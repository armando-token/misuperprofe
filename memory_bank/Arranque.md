# ✅ Checklist Maestro de Arranque de MiSuperProfe

Este documento es la **fuente de verdad única** para el arranque y la configuración de red del sistema. Debe seguirse rigurosamente para evitar errores.

---

## 🔴 **Reglas de Oro**

1.  **NO USAR `localhost`:** Toda comunicación entre servicios (ej. Agente -> API Principal) debe usar la IP pública del servidor o los nombres de host de Docker según el contexto.
2.  **UN SERVICIO POR PUERTO:** Cada componente tiene un puerto asignado. No intente lanzar un servicio en un puerto que no le corresponde.

---

## 🗺️ **Mapa de Servicios, Puertos y Comandos**

| Servicio | Ubicación | Puerto | Comando de Arranque (desde `/home/ubuntu`) |
| :--- | :--- | :--- | :--- |
| **API Principal (FastAPI)** | Docker | `8000` | `docker compose up -d` |
| **PostgreSQL DB** | Docker | `5432` | `docker compose up -d` |
| **Redis** | Docker | `6379` | `docker compose up -d` |
| **WordPress** | Docker | `8081` | `docker compose up -d` |
| **Agente LangGraph** | Host (Python) | `8001` | `nohup poetry run python3 app/langgraph_server_example.py > agent.log 2>&1 &` |
| **Copilot Runtime** | Host (Node.js) | `4000` | `cd copilot-runtime && nohup npm start > runtime.log 2>&1 &` |
| **Frontend Vite** | Host (Node.js) | `5174` | `cd frontend-chat && nohup npm run dev > frontend.log 2>&1 &` |

---

## 🚀 **Guía de Despliegue en un Servidor Nuevo**

Esta guía asume un servidor Ubuntu limpio.

### **Paso 1: Preparación del Sistema**

1.  **Actualizar el sistema:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```
2.  **Instalar dependencias base:**
    ```bash
    sudo apt install -y git curl build-essential python3-dev python3.11-venv docker.io
    ```
3.  **Instalar Node.js (v18) y `npm`:**
    ```bash
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 18
    nvm use 18
    ```
4.  **Instalar Poetry:**
    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    ```
5.  **Instalar Docker Compose V2:**
    ```bash
    sudo apt remove docker-compose # Remover versión antigua si existe
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    ```
6.  **Configurar permisos de Docker (sin `sudo`):**
    ```bash
    sudo usermod -aG docker ${USER}
    sudo chmod 666 /var/run/docker.sock
    newgrp docker # Aplicar en la sesión actual
    ```

### **Paso 2: Configuración del Proyecto**

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/MiSuperProfe/misuperprofev10.1.git .
    ```
    *(Nota: El `.` clona el contenido en el directorio actual, `/home/ubuntu`)*

2.  **Crear el archivo de entorno (`.env`):**
    Cree un archivo `/home/ubuntu/.env`. El contenido debe ser el proporcionado en la documentación interna (`copilot.md` o `debug.md`), asegurándose de que `DB_HOST` apunte a `db` para los contenedores. Para la ejecución de scripts desde el host, el propio script ya gestiona la conexión a la IP pública.

3.  **Instalar dependencias Python:**
    ```bash
    poetry install --no-root
    ```
4.  **Instalar dependencias Node.js:**
    ```bash
    # Para el Runtime
    cd /home/ubuntu/copilot-runtime && npm install
    # Para el Frontend
    cd /home/ubuntu/frontend-chat && npm install
    ```
5.  **Poblar la base de datos (¡Paso Crítico!):**
    Desde `/home/ubuntu`, ejecute el script que carga el contenido de los cursos.
    ```bash
    cd /home/ubuntu
    poetry run python3 scripts/load_markdown.py
    ```

### **Paso 3: Arranque de Servicios**

1.  **Iniciar los servicios base de Docker:**
    ```bash
    cd /home/ubuntu
    docker compose up -d
    ```
    Verifique con `docker ps` que todos los contenedores (`misuperapi`, `misuperpostgre`, etc.) estén `Up` y `healthy`.

2.  **Iniciar los servicios del Chat (en segundo plano):**
    ```bash
    # Iniciar Agente LangGraph (Puerto 8001)
    cd /home/ubuntu
    nohup poetry run python3 app/langgraph_server_example.py > agent.log 2>&1 &

    # Iniciar Copilot Runtime (Puerto 4000)
    cd /home/ubuntu/copilot-runtime
    nohup npm start > runtime.log 2>&1 &

    # Iniciar Frontend Vite (Puerto 5174)
    cd /home/ubuntu/frontend-chat
    nohup npm run dev > frontend.log 2>&1 &
    ```

### **Paso 4: Verificación Final**

1.  **Verificar los puertos:**
    ```bash
    ss -tulpen | grep -E '8000|8001|4000|5174'
    ```
    Debe ver una línea por cada puerto, indicando que un proceso está escuchando.

2.  **Acceder a la aplicación:**
    Abra su navegador y vaya a `http://<IP_PUBLICA_DEL_SERVIDOR>:5174`.

3.  **Revisar logs si algo falla:**
    - `tail -f /home/ubuntu/agent.log`
    - `tail -f /home/ubuntu/copilot-runtime/runtime.log`
    - `tail -f /home/ubuntu/frontend-chat/frontend.log`
    - `docker compose logs -f misuperapi`

---
*Este documento es la referencia principal para el arranque. Cualquier desviación debe ser justificada y documentada aquí.*
