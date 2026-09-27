# 🎓 MiSuperProfe

<div align="center">

### Enterprise Adaptive AI Tutoring & DECO Cognitive Assessment Engine

[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![FAISS](https://img.shields.io/badge/FAISS-CPU%20v1.7.4-brightgreen.svg?logo=meta&logoColor=white)](https://github.com/facebookresearch/faiss)
[![Docker Compose v2](https://img.shields.io/badge/Docker%20Compose-v2.24+-2496ED.svg?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Caddy](https://img.shields.io/badge/Caddy-2.7+-1F88C0.svg?logo=caddy&logoColor=white)](https://caddyserver.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7%20Alpine-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<br/>

**Transforming High-Stakes University Entrance Exam Preparation through Contextualized Cognitive Assessment and Dense Semantic Theory Retrieval.**

[Live Production Gateway](https://app.misuperprofe.com) • [API Documentation](https://app.misuperprofe.com/docs) • [Architecture](#-system-architecture) • [Quickstart](#-quickstart-guide-in-3-steps) • [API Reference](#-api-reference--curl-examples)

</div>

---

## 📌 Executive Overview

**MiSuperProfe** is a high-throughput, adaptive AI tutoring backend and cognitive assessment platform engineered specifically for competitive, high-stakes academic examinations—most notably the **DECO®** (*Destrezas Cognitivas* / Cognitive Skills) examination format pioneered by Latin America's most demanding university admission systems, such as the **Universidad Nacional Mayor de San Marcos (UNMSM)**.

Traditional e-learning platforms rely on rote memorization and disjointed flashcards. In contrast, MiSuperProfe synthesizes **contextualized situation-based problem solving** with a real-time semantic retrieval pipeline across a curated academic corpus of **2,473 theoretical chapters** spanned over **10 foundational disciplines**. 

The system operates as an intelligent multi-agent backend for OpenAI Custom GPTs, CopilotKit interfaces, and modern web applications, serving structured pedagogical recipes, conducting spaced-repetition evaluations, tracking granular user mastery, and dynamically adjusting question complexity based on real-time academic profiling.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   THE MISUPERPROFE MISSION                                       │
├────────────────────────────────┬────────────────────────────────┬───────────────────────────────┤
│    🔍 Semantic Theory Search   │   🧠 Contextual DECO Matrix    │     ⚡ Adaptive Spacing       │
│ Sub-15ms semantic matching     │ Area-specific contextualization│ SuperMemo SM-2 Spaced         │
│ across 2,473 categorized       │ (Clinical, Engineering, Ethics)│ Repetition (SRS) tracking     │
│ chapters via FAISS CPU.        │ paired with cognitive depth.   │ student mastery & XP curves.  │
└────────────────────────────────┴────────────────────────────────┴───────────────────────────────┘
```

---

## 🏗️ System Architecture

The MiSuperProfe infrastructure is containerized via **Docker Compose v2** and protected by an enterprise **Caddy 2.7+** ingress gateway that guarantees zero-touch automatic TLS/SSL certificate provisioning and HTTP/3 QUIC acceleration. Internally, services communicate over an isolated bridge network with hardened security boundaries.

```mermaid
flowchart TD
    %% Ingress & Clients
    Client["🌐 Client Applications<br/>(Custom GPT / CopilotKit / Web App)"]
    
    subgraph Host_Environment["🖥️ Production Host (Ubuntu 22.04 LTS / Cloud VM)"]
        subgraph Docker_Network["Docker Compose v2 Network ('v13_default')"]
            
            %% Edge Proxy
            Caddy["🔒 Caddy Reverse Proxy<br/>• Auto Let's Encrypt TLS/SSL<br/>• HTTP/3 & QUIC Support<br/>• Rate Limiting & SSL Termination"]
            
            %% Core Application Service
            FastAPI["⚡ FastAPI Application Gateway (:8000)<br/>• Async ASGI Engine (Uvicorn)<br/>• OpenAPI 3.1 & Model Validation<br/>• Lifespan Context Manager"]
            
            %% Service Modules
            subgraph Core_Engines["🧠 Core Intelligent Engines"]
                DynamicRouter["⚡ Centralized Dynamic Router<br/>(Action Dispatcher: practice, progress, stats)"]
                DecoEngine["🧠 DECO Cognitive Matrix Engine<br/>(Areas A-E Context & Difficulty Modulator)"]
                FaissEngine["🔍 FAISS Semantic Search Engine<br/>(Sentence-Transformers all-MiniLM-L6-v2)"]
                SrsEngine["📈 Adaptive SRS & XP Engine<br/>(Attempt Tracking & Spaced Repetition)"]
            end
            
            %% Persistence Layer
            subgraph Persistence_Layer["💾 High-Reliability Data Storage"]
                PostgreSQL[("🐘 PostgreSQL 15 Relational DB<br/>• 2,473 Markdown Chapters<br/>• 10 Core Academic Courses<br/>• Student Attempt Telemetry<br/>• External User Identity Maps")]
                Redis[("⚡ Redis 7 In-Memory Cache<br/>• Leaderboards & Weekly XP<br/>• Fast Session Store<br/>• Append-Only File (AOF) Persistence")]
            end
            
            %% Vector Cache Storage
            VectorStorage[("📁 Serialized Vector Cache<br/>• embeddings.npy<br/>• faiss_index.bin<br/>• chapters.pkl & metadata.json")]
        end
    end

    %% Flow Connections
    Client -->|"HTTPS (Port 443) / HTTP (Port 80)"| Caddy
    Caddy -->|"Proxy pass (misuperapi:8000)"| FastAPI
    
    FastAPI --> DynamicRouter
    FastAPI --> DecoEngine
    FastAPI --> FaissEngine
    FastAPI --> SrsEngine
    
    FaissEngine <-->|"Zero-Latency Memory Map"| VectorStorage
    FaissEngine -.->|"Syncs Theory Extracts"| PostgreSQL
    
    DecoEngine -->|"Fetches Chapter Context"| PostgreSQL
    SrsEngine -->|"Logs Attempts & Mastery"| PostgreSQL
    SrsEngine -->|"Updates Real-Time Rank & XP"| Redis
    DynamicRouter -->|"Aggregates Analytics"| PostgreSQL
    DynamicRouter -->|"Checks Session Cache"| Redis
```

---

## ✨ Core Features Grid

<table align="center" width="100%">
  <tr>
    <td width="50%" valign="top">
      <h3>🧠 DECO Cognitive Matrix Engine</h3>
      <ul>
        <li><b>Context-Aware Question Generation:</b> Tailors theoretical problems into real-world scenarios based on academic discipline:
          <ul>
            <li><b>Area A (Health Sciences):</b> Clinical case histories, medical symptoms, laboratory assays.</li>
            <li><b>Area B (Basic Sciences):</b> Controlled scientific experiments, phenomenological deduction.</li>
            <li><b>Area C (Engineering):</b> Applied mechanical problems, coordinate geometries, structural diagrams.</li>
            <li><b>Area D (Economics):</b> Financial markets, macroeconomic shifts, business decision models.</li>
            <li><b>Area E (Humanities):</b> Ethical dilemmas, historical sources, philological textual critique.</li>
          </ul>
        </li>
        <li><b>Taxonomic Cognitive Depth:</b> Enforces 8 hierarchical cognitive competencies: <i>Analysis, Inference, Extrapolation, Application, Synthesis, Evaluation, Interpretation, and Comparison</i>.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🔍 FAISS Semantic Theory Engine</h3>
      <ul>
        <li><b>Massive Knowledge Retrieval:</b> In-memory indexing of <b>2,473 complete chapters</b> spanning all 10 core entrance exam disciplines.</li>
        <li><b>Sentence-Transformers Vectorization:</b> Powered by <code>all-MiniLM-L6-v2</code> producing 384-dimensional dense semantic vectors.</li>
        <li><b>Ultra-Fast Cold Start:</b> Serialized disk caching (<code>faiss_index.bin</code> and <code>embeddings.npy</code>) with automated MD5 cryptographic corpus hash verification.</li>
        <li><b>Sub-15ms Ingestion:</b> Instantaneous nearest-neighbor retrieval bypassing costly external vector database network round-trips.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>⚡ Centralized Dynamic API (<code>/dynamic</code>)</h3>
      <ul>
        <li><b>Polymorphic Gateway:</b> A single, resilient endpoint executing multi-modal student actions (<code>get_courses</code>, <code>get_question</code>, <code>practice</code>, <code>get_progress</code>, <code>get_stats</code>, <code>explain</code>, <code>set_user_area</code>).</li>
        <li><b>Zero-Friction Custom GPT Compatibility:</b> Designed specifically to bypass strict OpenAPI parameter limits and schema validation drift in OpenAI Actions.</li>
        <li><b>Spaced Repetition (SRS):</b> Algorithmic scheduling based on SuperMemo principles, reinforcing forgotten concepts at optimal memory retention intervals.</li>
        <li><b>Granular XP & Progress Breakdown:</b> Real-time accuracy and mastery reporting aggregated per course, discipline, and historical session.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h3>🐳 Production-Ready Docker & Caddy Stack</h3>
      <ul>
        <li><b>Automated Edge TLS:</b> Integrated Caddy container managing Let's Encrypt certificates without external certbot crons.</li>
        <li><b>Fault-Tolerant Orchestration:</b> Built-in health probes (<code>pg_isready</code>, <code>redis-cli ping</code>) and <code>restart: unless-stopped</code> guarantees.</li>
        <li><b>Enterprise Ops Suite:</b> Automated backup scripts for PostgreSQL and Redis, transactional database dumps, safe restart utilities, and persistent host logging volumes.</li>
        <li><b>Stateless Container Design:</b> Separates state into persistent named Docker volumes (<code>postgres_data</code>, <code>redis_data</code>, <code>caddy_data</code>).</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🏛️ Comprehensive Knowledge Base (10 Disciplines)

MiSuperProfe embeds the complete academic syllabus required for premier competitive admissions. Every discipline contains rich, structured Markdown chapters indexed for instant semantic access:

| Icon | Course / Discipline | Focus Areas & Syllabus Modules | Target Areas |
| :---: | :--- | :--- | :---: |
| 🧬 | **Biología (Biology)** | Cellular biology, genetics, ecology, physiology, organ systems | Area A, B |
| ⚖️ | **Cívica (Civics)** | Constitutional law, human rights, civic citizenship, national defense | Area D, E |
| 🌍 | **Cultura General (General Culture)** | Contemporary affairs, science history, global treaties, art | All Areas |
| 📈 | **Economía (Economics)** | Microeconomics, macroeconomics, fiscal policy, currency systems | Area D |
| 🤔 | **Filosofía (Philosophy)** | Epistemology, ethical systems, logic, ontology, Latin American thought | Area E |
| 🗺️ | **Geografía (Geography)** | Physical geography, geomorphology, climate, Peruvian hydrology | Area D, E |
| 📜 | **Historia (History)** | Peruvian pre-Inca history, colonial era, universal modern history | Area D, E |
| ✍️ | **Lenguaje (Language & Linguistics)** | Grammatical syntax, phonetics, morphology, orthographic rules | All Areas |
| 📖 | **Literatura (Literature)** | Classical literature, Spanish Golden Age, Peruvian indigenism | Area E |
| 🧠 | **Psicología (Psychology)** | Cognitive development, learning theories, personality, social dynamics | Area A, E |

**Total Ingested Chapters:** **`2,473 Chapters`** • **Vector Database Footprint:** **`~384 MB (In-Memory Index)`**

---

## 📊 The DECO Cognitive Matrix Specification

The engine dynamically pairs student academic targets with specialized problem templates:

```
                                  DECO PATTERN MATRIX
┌──────────┬────────────────────────────┬─────────────────────────────┬───────────────────────────┐
│ Academic │ Core Target Discipline     │ Contextual Scenario         │ Cognitive Objective       │
│ Area     │                            │                             │                           │
├──────────┼────────────────────────────┼─────────────────────────────┼───────────────────────────┤
│ Area A   │ Health Sciences & Medicine │ Clinical Case / Lab Report  │ Diagnostic Analysis       │
│ Area B   │ Basic & Natural Sciences   │ Laboratory Phenomenon       │ Scientific Application    │
│ Area C   │ Engineering & Architecture │ Applied Technical Scenario  │ Quantitative Formulation  │
│ Area D   │ Business & Economics       │ Corporate / Market Crisis   │ Strategic Evaluation      │
│ Area E   │ Humanities & Law           │ Ethical Dilemma / Source    │ Critical Interpretation   │
└──────────┴────────────────────────────┴─────────────────────────────┴───────────────────────────┘
```

When an assessment session is initiated via `/api/v1/deco/question`, the engine synthesizes:
1. **The exact theoretical excerpt** retrieved via FAISS semantic search or chapter index.
2. **The contextual styling rules** (e.g., "5 multiple-choice options", "Formal clinical case prelude").
3. **The cognitive depth requirement** (e.g., "Analyze symptom correlations to deduce physiological cause").

---

## 📜 Project Evolution & Heritage

MiSuperProfe has evolved across three major engineering iterations to arrive at its current enterprise production grade:

```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│     v12: Foundation       │      │  v13: Decoupled Vector    │      │  Production Release       │
│      (Early 2024)         │ ───► │       (Mid 2025)          │ ───► │      (August 2025)        │
│                           │      │                           │      │                           │
│ • Monolithic FastAPI core │      │ • Local FAISS vector index│      │ • Unified /dynamic API    │
│ • ChatGPT Team OAuth      │      │ • DECO Pattern Matrix     │      │ • Redis XP Leaderboards   │
│ • Basic SRS logic         │      │ • Multi-container Docker  │      │ • Zero-downtime Caddy SSL │
│ • Synchronous DB sessions │      │ • Async SQLAlchemy 2.0   │      │ • 100% Audited Reliability│
└───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

### 1. Version 12 — Foundational Prototype & ChatGPT Team Integration
- **Concept:** Initial backend developed to test AI-driven tutoring for competitive university preparation.
- **Key Mechanics:** Integration with ChatGPT Team workspaces using custom OAuth 2.0 delegation; preliminary Spaced Repetition System (SRS) schemas; linear lesson progression.
- **Architectural Bottlenecks:** External token authentication overhead, reliance on synchronous database operations, lack of local vector search capability, and rigid prompt instructions.

### 2. Version 13 — Architectural Decoupling & Vector Search Engine
- **Concept:** Re-engineering the platform into an autonomous, high-speed microservices architecture.
- **Key Innovations:**
  - Integrated local in-memory **FAISS vector indexing** with `sentence-transformers`, indexing 2,473 theoretical chapters with sub-15ms query times.
  - Implemented the **DECO Pattern Matrix** (`deco_patterns.py`) to systematically formulate context-driven questions for UNMSM exam archetypes.
  - Fully containerized the stack with Docker Compose v2, isolated networks, and automatic SSL proxying via Caddy.
  - Migrated persistence layer to **SQLAlchemy 2.0 async** with asyncpg connection pooling.

### 3. Production Release (Final August 2025) — Enterprise Hardening & Stability
- **Concept:** Production release deployed at `app.misuperprofe.com` passing comprehensive multi-stage audit verification.
- **Key Milestones:**
  - Introduced the centralized **Polymorphic `/dynamic` API**, unifying progress metrics, real-time question generation, topic explanations, and practice sessions into a bulletproof interface.
  - Hardened automated system operations: `safe_restart.sh`, daily PostgreSQL and Redis backups, and self-healing container health checks.
  - Redis 7 sorted-set leaderboards tracking weekly student XP and streaks.
  - Verified 100% operational audit compliance across all endpoints and knowledge domains.

---

## 🚀 Quickstart Guide in 3 Steps

Deploy a complete production or staging instance on any modern Linux or macOS host in under three minutes.

### Prerequisites
- [Docker Engine](https://docs.docker.com/engine/install/) (v24.0+)
- [Docker Compose v2](https://docs.docker.com/compose/) (v2.24+)
- Git installed on host

### Step 1: Clone the Repository
```bash
git clone https://github.com/MiSuperProfe/misuperprofe.git
cd misuperprofe
```

### Step 2: Configure Environment Variables
Copy the environment template and configure your secrets:
```bash
cp env.example .env
```

Ensure critical variables in `.env` match your configuration:
```dotenv
# Database Configuration
POSTGRES_USER=mysuper_user
POSTGRES_PASSWORD=SuperSecretProductionPassword!
POSTGRES_DB=mysuper_bd
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DATABASE_URL=postgresql+psycopg2://mysuper_user:SuperSecretProductionPassword!@db:5432/mysuper_bd

# In-Memory Cache
REDIS_URL=redis://redis:6379/0

# Security & API Credentials
API_KEY=YourEnterpriseApiKeyHere
JWT_SECRET_KEY=YourCryptographicallyStrongSecretKey32BytesLong
JWT_ALGORITHM=HS256

# Core Application Settings
APP_NAME=MiSuperProfeAPI
API_V1_STR=/api/v1
ENVIRONMENT=production
```

> [!NOTE]
> If deploying behind Caddy on a public domain, ensure your domain DNS points to your server and configure `/etc/caddy/Caddyfile`:
> ```caddyfile
> app.misuperprofe.com {
>     reverse_proxy misuperapi:8000
> }
> ```

### Step 3: Build & Launch the Services
Start all containerized services in detached mode:
```bash
docker compose up --build -d
```

Initialize the database schema and ingest the 2,473 theoretical chapters:
```bash
# Ingest all markdown curriculum into PostgreSQL and build initial FAISS index
docker compose exec misuperapi python scripts/load_markdown.py
```

Verify service status:
```bash
docker compose ps
```

All 4 services (`misuperapi`, `misuperpostgre`, `misuperredis`, `misupercaddy`) should be in the `healthy` or `running` state.

---

## 🔌 API Reference & cURL Examples

All protected endpoints require an authorization token provided via the `Authorization` header:
```http
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

### 1. Healthcheck Endpoint

Verifies operational readiness of the API gateway.

#### Request:
```bash
curl -s -X GET "https://app.misuperprofe.com/api/v1/agent/health"
```

#### Response (`200 OK`):
```json
{
  "status": "ok",
  "service": "Agent Service"
}
```

---

### 2. Centralized Dynamic Endpoint (`POST /api/v1/dynamic`)

The versatile `/dynamic` route acts as a polymorphic dispatch hub.

#### A. Fetch User Progress & XP Breakdown
Calculates overall experience points (XP), answer accuracy, and detailed mastery segmented per course directly from student attempt histories.

**Request:**
```bash
curl -s -X POST "https://app.misuperprofe.com/api/v1/dynamic" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YourEnterpriseApiKeyHere" \
  -d '{
    "action": "get_progress",
    "user_id": "student_usr_99812"
  }'
```

**Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "user_id": "student_usr_99812",
    "total_xp": 480,
    "current_streak": 5,
    "total_questions_answered": 52,
    "correct_answers": 44,
    "progress_by_course": [
      {
        "course": "biologia",
        "xp": 210,
        "questions_answered": 22,
        "correct_answers": 20
      },
      {
        "course": "historia",
        "xp": 140,
        "questions_answered": 16,
        "correct_answers": 13
      },
      {
        "course": "filosofia",
        "xp": 130,
        "questions_answered": 14,
        "correct_answers": 11
      }
    ]
  },
  "message": "Progreso obtenido exitosamente"
}
```

#### B. List All Available Courses & Chapter Counts
Enumerates all active courses and their total structured chapter counts.

**Request:**
```bash
curl -s -X POST "https://app.misuperprofe.com/api/v1/dynamic" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YourEnterpriseApiKeyHere" \
  -d '{
    "action": "get_courses"
  }'
```

**Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "courses": [
      {
        "id": "biologia",
        "name": "Biología",
        "description": "Curso integral de Biología para ciencias de la salud",
        "chapters": 312
      },
      {
        "id": "historia",
        "name": "Historia",
        "description": "Historia del Perú e Historia Universal contextualizada",
        "chapters": 284
      },
      {
        "id": "filosofia",
        "name": "Filosofía",
        "description": "Lógica, epistemología, ética y pensamiento filosófico",
        "chapters": 196
      }
    ],
    "total": 10
  },
  "message": "Lista de cursos obtenida exitosamente"
}
```

#### C. Set Student Academic Area Profile
Associates a student identifier with their specific UNMSM academic admission stream (Area A, B, C, D, or E).

**Request:**
```bash
curl -s -X POST "https://app.misuperprofe.com/api/v1/dynamic" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YourEnterpriseApiKeyHere" \
  -d '{
    "action": "set_user_area",
    "user_id": "student_usr_99812",
    "area": "Area_A"
  }'
```

**Response (`200 OK`):**
```json
{
  "success": true,
  "message": "Área del usuario student_usr_99812 establecida a Area_A exitosamente."
}
```

---

### 3. DECO Question Recipe Generator (`POST /api/v1/deco/question`)

Generates a tailored pedagogical prompt blueprint for the Custom GPT, binding academic theory with the candidate's target DECO matrix rules.

#### Request:
```bash
curl -s -X POST "https://app.misuperprofe.com/api/v1/deco/question" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YourEnterpriseApiKeyHere" \
  -d '{
    "user_id": "student_usr_99812",
    "area": "Biología",
    "chapter_id": 4
  }'
```

#### Response (`200 OK`):
```json
{
  "theory_extract": "# Capítulo 4: Fisiología Celular y Transporte de Membrana\nEl transporte activo primario utiliza ATP para transportar moléculas contra su gradiente electroquímico...",
  "deco_pattern": {
    "user_area": "Area_A",
    "subject": "Biología",
    "recommended_context": "caso clínico",
    "recommended_cognitive_level": "análisis",
    "style_guidelines": {
      "tone": "formal y técnico",
      "structure": "Caso clínico/laboratorio seguido de pregunta directa.",
      "options_count": 5
    }
  },
  "metadata": {
    "course_id": 1,
    "chapter_id": 4,
    "chapter_title": "Fisiología Celular y Transporte de Membrana"
  }
}
```

---

### 4. DECO Answer Submission & Evaluation (`POST /api/v1/deco/answer`)

Submits the evaluation of a completed DECO interaction, awards real-time XP, schedules spaced repetition intervals, and records historical analytics.

#### Request:
```bash
curl -s -X POST "https://app.misuperprofe.com/api/v1/deco/answer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YourEnterpriseApiKeyHere" \
  -d '{
    "user_id": "student_usr_99812",
    "session_id": "Fisiología Celular y Transporte de Membrana",
    "answer": "B",
    "is_correct": true,
    "area": "biologia",
    "topic": "Transporte de Membrana"
  }'
```

#### Response (`200 OK`):
```json
{
  "session_id": "Fisiología Celular y Transporte de Membrana",
  "user_id": "student_usr_99812",
  "is_correct": true,
  "user_answer": "B",
  "correct_answer": "N/A",
  "feedback": "Respuesta correcta registrada.",
  "micro_lesson": "Respuesta correcta registrada.",
  "cognitive_skill": "N/A",
  "topic": "Transporte de Membrana",
  "area": "biologia",
  "difficulty": 0,
  "points_earned": 10,
  "created_at": "2026-09-27T18:30:00Z"
}
```

---

## 📁 Repository Directory Structure

```
misuperprofe/
├── .gitignore
├── alembic/                         # Database schema migration framework
│   ├── env.py                       # Alembic asynchronous runtime
│   ├── script.py.mako               # Migration template
│   └── versions/                    # Versioned schema revisions
├── alembic.ini                      # Alembic database configuration
├── content/                         # 2,473 Markdown theoretical chapters
│   ├── biologia/                    # Biology chapters & modules
│   ├── civica/                      # Civics and Constitutional Law
│   ├── cultura general/             # General Cultural Knowledge
│   ├── economia/                    # Micro and Macroeconomics
│   ├── filosofia/                   # Logic, Ethics, and Philosophy
│   ├── geografia/                   # Physical & Human Geography
│   ├── historia/                    # Peruvian and World History
│   ├── lenguaje/                    # Linguistics, Syntax, and Grammar
│   ├── literatura/                  # Universal and Peruvian Literature
│   └── psicologia/                  # Cognitive and Social Psychology
├── docker-compose.yml               # Multi-container orchestration (v2)
├── Dockerfile                       # Multi-stage production container image
├── openapi_schema_COMPATIBLE.json   # Validated OpenAI Custom GPT specification
├── pyproject.toml                   # Poetry project configuration & dependencies
├── README.md                        # Enterprise project documentation
├── scripts/                         # Operational & maintenance automation
│   ├── backup_database.sh           # Automated PostgreSQL & Redis backup
│   ├── clean_spaced_repetition.py   # Spaced repetition maintenance
│   ├── healthcheck.sh               # Health check and probe diagnostic script
│   ├── load_markdown.py             # Bulk markdown parser and database loader
│   ├── safe_restart.sh              # Zero-downtime backup-before-restart utility
│   └── test_endpoints.sh            # API endpoint integration test suite
└── src/
    └── app/                         # FastAPI core application package
        ├── api/                     # REST API routers & endpoint handlers
        │   └── routers/
        │       ├── agent_router.py   # Agent management endpoints
        │       ├── ask_router.py     # Semantic theory query router
        │       ├── deco_router.py    # DECO question & answer engine
        │       └── dynamic_router.py # Centralized polymorphic /dynamic router
        ├── config.py                # Pydantic v2 application settings
        ├── core/                    # Security, auth, and MCP bindings
        ├── crud/                    # Reusable database CRUD operations
        ├── db/                      # SQLAlchemy async engine & session pool
        ├── main.py                  # ASGI FastAPI application entrypoint
        ├── models/                  # SQLAlchemy ORM declarative models
        ├── schemas/                 # Pydantic input/output schemas
        ├── services/                # Business logic & cognitive services
        │   ├── deco_patterns.py     # DECO Pattern Matrix by Area (A-E)
        │   ├── pattern_service.py   # Singleton pattern loader
        │   └── progress_report_service.py # Student progress analyzer
        └── tools/                   # Vector and caching utilities
            ├── redis_utils.py       # Redis XP leaderboard handlers
            └── semantic_search_optimized.py # FAISS vector search engine
```

---

## 🛠️ Operations & Maintenance

The `scripts/` directory provides essential automation utilities for enterprise stability:

### 1. Safe Container Restart (Backup Prior to Restart)
Always execute `safe_restart.sh` when deploying updates. It automatically captures a transactional database snapshot before cycling containers:
```bash
./scripts/safe_restart.sh
```

### 2. Manual Transactional Backup
Generate manual timestamped backups of both PostgreSQL and Redis:
```bash
./scripts/backup_database.sh
```
Backups are archived into `./backups/` and retained according to local retention policies.

### 3. Service Health Diagnostics
Inspect running service statuses and container metrics:
```bash
./scripts/healthcheck.sh
```

---

## 🛡️ Security, Privacy & Integrity

- **Encrypted Ingress:** TLS 1.3 encryption with modern cipher suites enforced by Caddy.
- **Isolated Network Perimeter:** Application, database, and caching containers are not exposed to the public internet; only ports `80` and `443` on Caddy are open.
- **Stateless Agent Communication:** OpenAI Custom GPT interactions do not persist sensitive student identifiers on external servers. Student tracking utilizes hashed external pseudonyms.
- **Cryptographic Model Verification:** Vector embeddings and chapter databases are checksummed via MD5 to prevent cache tampering or corrupted cold-starts.

---

## 🤝 Contributing

We welcome contributions from educators, software engineers, and cognitive scientists! Please review our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on our branching strategy (`main`, `feature/*`, `fix/*`), code style standards (**Black**, **Ruff**, **Mypy**), and pull request process.

---

## 📄 License

This project is licensed under the terms of the **MIT License**. See the [LICENSE](LICENSE) file for details.

```
Copyright (c) 2024-2026 Armando Silva and MiSuperProfe Contributors.
```
