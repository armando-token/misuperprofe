"""Configuración de la aplicación."""

from typing import List, Optional
from pydantic_settings import BaseSettings
import socket

class Settings(BaseSettings):
    """Configuración de la aplicación."""
    
    # Aplicación
    APP_ENV: str = "development"
    APP_NAME: str = "NTID"
    APP_VERSION: str = "1.0.0"
    APP_PORT: int = 8001 # Puerto para el servidor del agente (forzado a 8001)
    
    # Base de datos (leer del .env)
    DB_USER: str = "mysuper_user"
    DB_PASSWORD: str = "postgres_password"
    DB_NAME: str = "mysuper_bd"
    DB_HOST: str = "db"
    DB_PORT: int = 5432

    # API & JWT General (ej. para API Key global o usos internos si los hay)
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NTID"
    SECRET_KEY: str = "super_secret_key_for_dev_change_in_prod" # Clave genérica
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 # Por ejemplo, 1 hora
    DOMAIN: str = "app.misuperprofe.com"

    # JWT para Autenticación OAuth 2.0 (Integración ChatGPT Team)
    JWT_OAUTH_SECRET_KEY: str = "another_super_secret_key_for_oauth_change_in_prod"
    JWT_OAUTH_ALGORITHM: str = "HS256"
    JWT_OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Tokens de OAuth suelen ser más cortos
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:5175", # Añadido para el puerto del agente
        "https://copilotero.com",
        "https://misuperprofe.com",  # Origen del iframe que contiene el chat
        "https://app.misuperprofe.com"
    ]
    
    # Redis
    # REDIS_URL: str = "redis://redis:6379/0" # Usar para despliegue con Docker Compose donde 'redis' es un hostname
    REDIS_URL: str = "redis://localhost:6379/0" # Usar para ejecución directa en host (ej. pruebas locales/EC2 directo)

    # Gamificación
    XP_BASE_POINTS: int = 10
    XP_STREAK_BONUS: int = 2
    HEART_MAX_COUNT: int = 5
    LEAGUE_SIZE: int = 30
    XP_PER_CHEST: int = 50 # Nuevo: Puntos de XP necesarios para ganar un cofre

    # Adaptive Learning
    DIFFICULTY_MIN: float = 0.1
    DIFFICULTY_MAX: float = 3.0
    SPACED_REPETITION_INTERVALS: list = [1, 3, 7, 14, 30]

    # Gemini / LLM Settings
    GEMINI_HISTORY_MAX_CHARS: int = 20000 # Límite de caracteres para el historial enviado a Gemini
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash-latest" # Nombre del modelo de Gemini a utilizar
    GOOGLE_API_KEY: Optional[str] = None # Clave API para los servicios de Google (Gemini)
    OPENAI_API_KEY: Optional[str] = None # Clave API para los servicios de OpenAI
    OPENAI_MODEL_NAME: Optional[str] = "gpt-4o" # Nombre del modelo de OpenAI a utilizar (ej. gpt-4o, gpt-3.5-turbo)

    # Gamificación avanzada
    STREAK_BONUS_MULTIPLIER: float = 1.5
    DIFFICULTY_THRESHOLDS: list = [0.5, 1.0, 2.0]

    @property
    def EFFECTIVE_DB_HOST(self) -> str:
        # Si no se puede resolver el host, usar localhost (solo para desarrollo)
        try:
            socket.gethostbyname(self.DB_HOST)
            return self.DB_HOST
        except socket.gaierror:
            return "localhost"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.EFFECTIVE_DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def ALEMBIC_DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        """Configuración de Pydantic."""
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings() 