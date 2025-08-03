# 🎓 MiSuperProfe - Sistema de Tutoría Inteligente v13

[![Status](https://img.shields.io/badge/Status-Desplegado%20y%20Validado-green.svg)](https://app.misuperprofe.com)
[![Version](https://img.shields.io/badge/Version-v13-blue.svg)](https://github.com/MiSuperProfe/v13)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-100%25%20Passing%20(Auditado)-brightgreen.svg)](memory/audit.md)
[![Docker](https://img.shields.io/badge/Docker-Compose%20v2-blue.svg)](https://docs.docker.com/compose/)

## 🎯 **Descripción del Proyecto**

**MiSuperProfe** es un sistema de tutoría inteligente que utiliza un motor semántico local y un Custom GPT para proporcionar respuestas educativas precisas y preguntas de práctica personalizadas. El sistema está completamente contenerizado, desplegado en un servidor dedicado y ofrece una experiencia de aprendizaje interactiva y adaptativa.

### **Características Principales:**
- 🤖 **Motor Semántico Optimizado:** Búsqueda de respuestas basada en `sentence-transformers` y `faiss` para encontrar la teoría más relevante en **2473 capítulos** de conocimiento.
- 🧠 **Arquitectura de Patrones DECO:** El sistema utiliza una matriz de "patrones" para generar preguntas de práctica altamente personalizadas. Estos patrones ajustan el **contexto** (ej. "caso clínico" vs. "dilema ético"), el **nivel cognitivo** y el **estilo** de la pregunta según el área académica del estudiante, garantizando una experiencia de aprendizaje relevante.
- 📚 **10 Cursos Completos:** Incluyendo historia, biología, lenguaje, geografía, y más.
- 📊 **Sistema de Progreso Detallado:** Seguimiento de XP y rendimiento, con un **desglose por cada curso**, permitiendo un análisis granular del avance del estudiante.
- ⚡ **Endpoint Dinámico Centralizado:** Un único endpoint (`/dynamic`) que maneja acciones de `practice`, `get_progress`, `get_courses`, etc.
- 🐳 **Arquitectura 100% Contenerizada:** Todos los servicios (API, PostgreSQL, Redis, Caddy) son gestionados por Docker Compose v2 para máxima portabilidad y un despliegue simplificado.
- 🔒 **Seguridad con SSL Automático:** Caddy, como parte del stack de Docker, gestiona y renueva automáticamente los certificados SSL/TLS.
- 🛡️ **Scripts de Mantenimiento:** Herramientas para backups, reinicios seguros y monitoreo.

## 🚀 **Estado Actual del Proyecto**

**✅ SISTEMA COMPLETAMENTE DESPLEGADO, AUDITADO Y OPERATIVO**

El sistema ha sido desplegado exitosamente desde cero en un servidor virgen. Todas las funcionalidades han sido validadas a través de un plan de auditoría detallado (`memory/audit.md`), confirmando que cada componente funciona como se espera.

### **Servicios Desplegados:**
- ✅ **Servidor:** Ubuntu en `app.misuperprofe.com`
- ✅ **Base de Datos (Docker):** PostgreSQL con 2473 capítulos.
- ✅ **Caché (Docker):** Redis para optimización.
- ✅ **API (Docker):** FastAPI sirviendo la lógica de la aplicación.
- ✅ **Proxy Inverso con SSL (Docker):** Caddy gestionando HTTPS.

---

## 🏗️ **Arquitectura del Sistema**

El sistema está completamente contenerizado usando Docker Compose v2, lo que asegura la portabilidad y consistencia entre entornos. Todos los servicios, incluyendo el proxy inverso Caddy, operan dentro de la misma red de Docker, simplificando la comunicación y la seguridad.

```mermaid
graph TD
    A[Internet] -->|HTTPS (Puerto 443)| B(Servidor Ubuntu);
    subgraph Servidor Ubuntu
      subgraph Red Docker ('v13_default')
        B --> C[Contenedor Caddy];
        C -->|reverse_proxy a 'misuperapi:8000'| E[Contenedor API FastAPI];
        E --> F[Contenedor PostgreSQL];
        E --> G[Contenedor Redis];
      end
    end
```

### Motor Híbrido: Búsqueda Semántica + Patrones DECO
Una de las piezas centrales del proyecto es su capacidad para generar contenido educativo relevante y contextualizado.

1.  **Motor de Búsqueda Semántica (Extracción de Teoría):**
    -   **Base de Datos Relacional (PostgreSQL):** Los 2473 capítulos de conocimiento se almacenan de forma segura.
    -   **Vectorización en Tiempo Real (`sentence-transformers`):** Al iniciar la aplicación, el contenido de cada capítulo se convierte en un vector numérico (embedding).
    -   **Índice en Memoria (`faiss`):** Todos los vectores se cargan en un índice FAISS que permite encontrar los capítulos más relevantes a una consulta en milisegundos.

2.  **Motor de Generación de Preguntas (Patrones DECO):**
    -   Una vez que el motor semántico extrae la teoría relevante, el sistema consulta el archivo de patrones `deco_patterns.py`.
    -   Este archivo le indica al Custom GPT, basándose en el **área del usuario** y la **materia**, qué tipo de pregunta construir (ej. un problema de aplicación para ingeniería vs. un análisis de texto para humanidades).
    -   Esta arquitectura híbrida asegura que las preguntas no solo sean correctas (basadas en la teoría) sino también **pedagógicamente relevantes** para el perfil del estudiante.

---

## 🔧 **Guía de Despliegue Simplificada (Desde Cero)**

Este proyecto ha sido optimizado para un despliegue rápido y sencillo en un servidor Ubuntu virgen. (Ver `memory/start.md` para la guía detallada con explicaciones).

### **1. Preparación del Servidor**
```bash
# Actualizar repositorios e instalar herramientas base
sudo apt-get update && sudo apt-get install -y docker.io git python3-pip

# Instalar Docker Compose v2 (Plugin)
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
```

### **2. Despliegue y Configuración**
```bash
# Clonar el repositorio
git clone git@github.com:MiSuperProfe/v13.git
cd v13

# Crear el Caddyfile (único paso de configuración manual)
sudo mkdir -p /etc/caddy
echo "app.misuperprofe.com { reverse_proxy misuperapi:8000 }" | sudo tee /etc/caddy/Caddyfile
```

### **3. Construcción y Arranque**
El `docker-compose.yml` automatiza la instalación de dependencias, migraciones y arranque.
```bash
# Construir y arrancar todos los servicios
docker compose up --build -d

# Cargar el contenido teórico en la BD (esperar ~1-2 min después del paso anterior)
docker compose exec misuperapi python scripts/load_markdown.py
```
¡Listo! El sistema estará operativo en `https://app.misuperprofe.com`.

---

## 🔌 **API y Endpoints Clave**

La API ha sido auditada y los siguientes endpoints son los puntos de interacción principales. El esquema completo y compatible se encuentra en `openapi_schema_COMPATIBLE.json`.

- **`GET /api/v1/ask`**: Acceso directo al motor semántico para buscar teoría relevante a partir de un texto.
- **`GET /api/v1/courses`**: Lista los 10 cursos disponibles.
- **`POST /api/v1/deco/question`**: **(Endpoint Principal)** Utilizado por el GPT para obtener el material teórico de un capítulo específico y la "receta" del patrón DECO para generar una pregunta.
- **`POST /api/v1/deco/answer`**: Registra y evalúa la respuesta a una pregunta DECO, enviado por el GPT.
- **`POST /api/v1/dynamic`**: Un endpoint versátil que maneja múltiples acciones:
    - `action: 'get_courses'`: Lista todos los cursos.
    - `action: 'get_progress'`: **Obtiene el progreso detallado del usuario, incluyendo XP total y un desglose por cada curso.**
    - `action: 'get_stats'`: Obtiene estadísticas globales del sistema.
- **`GET /api/v1/agent/health`**: Endpoint de salud para monitoreo.

---

## 🛡️ **Mantenimiento y Operaciones**

El proyecto incluye un conjunto de scripts en la carpeta `scripts/` para facilitar la administración.

```bash
# Reinicio seguro que crea un backup antes de detener los contenedores (RECOMENDADO)
./scripts/safe_restart.sh

# Crear un backup manual de la base de datos y Redis
./scripts/backup_database.sh

# Verificar el estado de todos los contenedores
docker compose ps

# Ver logs en tiempo real de todos los servicios
docker compose logs -f
```
