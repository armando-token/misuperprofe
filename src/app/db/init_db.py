from sqlalchemy.orm import Session

from ..models import Base
from .session import engine


def init_db() -> None:
    """Inicializa la base de datos creando todas las tablas."""
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Elimina todas las tablas de la base de datos."""
    Base.metadata.drop_all(bind=engine) 