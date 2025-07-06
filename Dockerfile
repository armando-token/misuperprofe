FROM python:3.11-slim

WORKDIR /app

# Copiar el código fuente
COPY . /app

# Instalar dependencias del sistema
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN pip install --upgrade pip && \
    pip install poetry

RUN poetry cache clear . --all -n # Limpiar TODAS las cachés de Poetry

# Instalar PyTorch para CPU primero para guiar a sentence-transformers
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Ejecutar migraciones y arrancar Uvicorn
CMD ["sh", "-c", "poetry run alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
