# Contributing to MiSuperProfe

Thank you for your interest in contributing to **MiSuperProfe**! As an enterprise-grade open-source adaptive tutoring platform and DECO assessment engine, we welcome contributions from educators, software engineers, data scientists, and open-source enthusiasts worldwide.

This guide outlines our development workflow, coding standards, branch conventions, and submission guidelines to ensure high software quality and collaborative efficiency.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Architecture & Tech Stack Overview](#architecture--tech-stack-overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development Setup](#local-development-setup)
- [Branching Strategy](#branching-strategy)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Coding Standards & Tooling](#coding-standards--tooling)
  - [Formatting & Linting](#formatting--linting)
  - [Type Annotations](#type-annotations)
  - [Pre-commit Hooks](#pre-commit-hooks)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request (PR) Workflow](#pull-request-pr-workflow)
- [Issue Reporting & Security Disclosures](#issue-reporting--security-disclosures)

---

## Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for all participants. By contributing to this project, you agree to abide by our Code of Conduct:

- **Be Respectful:** Value diverse perspectives, constructive critiques, and professional discourse.
- **Maintain Professionalism:** Focus on pedagogical impact, code quality, and positive community collaboration.
- **Graceful Collaboration:** Welcome newcomers, share knowledge generously, and accept constructive feedback gracefully.

Instances of unacceptable behavior may be reported directly to the core maintainers at [dev@misuperprofe.com](mailto:dev@misuperprofe.com).

---

## Architecture & Tech Stack Overview

Before contributing, familiarize yourself with our core stack:
- **Language & Runtime:** Python 3.11 / 3.12 managed via [Poetry](https://python-poetry.org/)
- **Web Gateway & Core Engine:** [FastAPI](https://fastapi.tiangolo.com/), Starlette, Uvicorn (ASGI)
- **Vector Search & Embedding:** [FAISS (faiss-cpu)](https://github.com/facebookresearch/faiss), `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Database Layer:** PostgreSQL 15, SQLAlchemy 2.0 (Async), Alembic migrations
- **Caching & High-Speed Leaderboards:** Redis 7 (Alpine), Append-Only File (AOF) persistence
- **Ingress & Edge Security:** Caddy 2.7+ (Automatic TLS / Reverse Proxy)
- **Containerization:** Docker Compose v2

---

## Getting Started

### Prerequisites

Ensure you have the following installed on your host machine:
- **Git** (2.35+)
- **Python** (3.11 or 3.12)
- **Poetry** (1.7+)
- **Docker Engine** (24.0+) & **Docker Compose v2** (2.24+)

### Local Development Setup

1. **Fork and Clone the Repository:**
   ```bash
   git clone https://github.com/<your-username>/misuperprofe.git
   cd misuperprofe
   ```

2. **Set Up an Isolated Python Virtual Environment with Poetry:**
   ```bash
   poetry env use python3.11
   poetry install --with dev
   ```

3. **Activate the Virtual Environment:**
   ```bash
   poetry shell
   ```

4. **Initialize Environment Variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your local credentials and secrets
   ```

5. **Start Infrastructure Services (PostgreSQL & Redis):**
   ```bash
   docker compose up -d db redis
   ```

6. **Run Database Migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

7. **Index Knowledge Base Content (Optional but Recommended for Local Semantic Search):**
   ```bash
   poetry run python scripts/load_markdown.py
   ```

8. **Launch the FastAPI Development Server:**
   ```bash
   cd src
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

Verify your environment by accessing `http://localhost:8000/api/v1/agent/health` or visiting the interactive Swagger UI at `http://localhost:8000/docs`.

---

## Branching Strategy

We enforce a strict Git flow designed for continuous delivery and zero-downtime releases:

```
main (Protected, stable production branch)
  │
  ├── feature/deco-analytics-v2   (New capabilities, engines, or endpoints)
  ├── fix/faiss-cache-invalidation (Bug fixes and performance patches)
  ├── docs/api-curl-examples      (Documentation enhancements)
  └── refactor/srs-sm2-algorithm  (Code refactoring without behavioral alteration)
```

### Branch Naming Conventions

Always branch off the latest `main` branch using one of the following prefixes:
- `feature/<short-descriptive-title>`: For new features and enhancements.
- `fix/<short-descriptive-title>`: For bug fixes and security patches.
- `docs/<short-descriptive-title>`: For documentation additions or corrections.
- `refactor/<short-descriptive-title>`: For code refactoring and performance optimizations.
- `test/<short-descriptive-title>`: For test suite additions or fixture enhancements.
- `chore/<short-descriptive-title>`: For dependency bumps, build configurations, or CI/CD updates.

*Example:* `feature/matrix-cognitive-levels` or `fix/jwt-expiration-handler`.

---

## Commit Message Guidelines

We enforce the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. All commit messages must be written in English.

### Format
```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

### Supported Types
| Type | Purpose | Example |
| :--- | :--- | :--- |
| `feat` | Introduces a new feature or endpoint | `feat(deco): add cognitive difficulty weighting to matrix` |
| `fix` | Patches a bug or addresses an issue | `fix(faiss): resolve cache collision during chapter reload` |
| `docs` | Modifies documentation or inline comments | `docs(readme): update quickstart and curl reference` |
| `refactor`| Refactors codebase without altering external behavior | `refactor(db): streamline async session pool management` |
| `perf` | Improves execution time or resource footprint | `perf(search): cache query embedding tensors in redis` |
| `test` | Adds or modifies automated tests | `test(api): add dynamic endpoint parameter validation tests` |
| `chore` | Maintenance tasks, dependencies, tooling | `chore(deps): bump fastapi from 0.115.11 to 0.115.12` |

---

## Coding Standards & Tooling

### Formatting & Linting

All Python code must strictly conform to PEP 8 standards. We use **Black** for deterministic formatting and **Ruff** for fast linting.

```bash
# Check code formatting
poetry run black --check src/ tests/

# Auto-format codebase
poetry run black src/ tests/

# Execute Ruff linter
poetry run ruff check src/ tests/

# Auto-fix Ruff warnings
poetry run ruff check --fix src/ tests/
```

### Type Annotations

- Fully annotate all function signatures, return values, and Pydantic models.
- Validate static types using **Mypy**:
  ```bash
  poetry run mypy src/
  ```

### Pre-commit Hooks

Ensure pre-commit hooks are active prior to opening a PR:
```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

---

## Testing Guidelines

Reliability in academic evaluation engines is non-negotiable. Ensure that all new features and bug fixes include unit and integration tests.

### Running the Test Suite
```bash
# Execute complete test suite
poetry run pytest

# Execute tests with coverage reporting
poetry run pytest --cov=src/app --cov-report=term-missing tests/
```

### Test Organization
- Unit tests reside under `tests/unit/`.
- Integration and end-to-end API tests reside under `tests/integration/`.
- Use `pytest-asyncio` for asynchronous endpoint testing with test database fixtures.
- Mock external LLM and vector model inferences in CI pipelines to preserve test deterministic performance.

---

## Pull Request (PR) Workflow

1. **Keep Pull Requests Atomic:** A PR should address a single concern, bug, or feature.
2. **Sync with Upstream:** Rebase your branch onto the latest `main` before opening your PR:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
3. **Draft a Comprehensive Description:**
   - Clearly state the problem and the implemented solution.
   - Link related issue numbers (e.g., `Closes #42`).
   - Include sample cURL commands or verification output where applicable.
4. **Pass Automated CI/CD Gates:**
   - [ ] All unit and integration tests pass (`pytest`).
   - [ ] Linters and formatters report zero errors (`black`, `ruff`, `mypy`).
   - [ ] Documentation updated to reflect changes.
5. **Code Review:** At least one core maintainer review and approval is required before merging.

---

## Issue Reporting & Security Disclosures

### Bug Reports & Feature Requests
Open an issue on GitHub using our provided issue templates. Please provide:
- A clear, concise summary of the issue or feature proposal.
- Step-by-step reproduction instructions.
- Operating system, Python version, Docker version, and relevant logs.

### Security Vulnerabilities
If you discover a security vulnerability, **please do not disclose it publicly on GitHub issues**. Instead, send a detailed security report to [security@misuperprofe.com](mailto:security@misuperprofe.com) or [armando@misuperprofe.com](mailto:armando@misuperprofe.com). We will acknowledge receipt within 24 hours and coordinate a coordinated remediation release.

---

*Thank you for contributing to the future of AI-driven cognitive education with MiSuperProfe!*
