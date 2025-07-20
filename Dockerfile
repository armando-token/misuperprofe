FROM python:3.12-slim

# Establecer el directorio de trabajo principal
WORKDIR /app

# Copiar archivos de dependencias
COPY poetry.lock pyproject.toml ./

# Copiar el código fuente y la configuración de Alembic al directorio src
COPY ./src /app/src
COPY ./alembic /app/src/alembic
COPY ./alembic /app/alembic
COPY alembic.ini /app/src/alembic.ini
COPY alembic.ini /app/alembic.ini

# Instalar dependencias Y el proyecto actual como un paquete
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main

# Exponer el puerto
EXPOSE 8000

# El comando se especifica en docker-compose para forzar CWD
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"] 