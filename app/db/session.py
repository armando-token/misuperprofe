from app.config import settings
from sqlalchemy.engine.url import make_url

url = make_url(settings.DATABASE_URL)

if url.drivername.endswith("asyncpg"):
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.APP_ENV == "development",
        future=True,
        pool_size=10,           # Tamaño del pool de conexiones
        max_overflow=20,        # Conexiones extra permitidas
        pool_timeout=30,        # Tiempo de espera para obtener una conexión
        pool_recycle=1800       # Reciclar conexiones cada 30 minutos
    )
    # Create async session factory
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    async def get_session() -> AsyncSession:
        """Dependency para obtener una sesión de base de datos asíncrona."""
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close() 
else:
    from sqlalchemy import create_engine
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.APP_ENV == "development",
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800
    )
    # No se usa AsyncSession ni get_session en modo sync

async def init_db():
    """Inicializa la base de datos creando todas las tablas."""
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 