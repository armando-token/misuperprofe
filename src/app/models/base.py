from datetime import datetime
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import as_declarative, declared_attr, declarative_base
from app.db.custom_types import NaiveDateTime

Base = declarative_base()

@as_declarative()
class ModelBase:
    """Clase base para todos los modelos."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Genera el nombre de la tabla automáticamente."""
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(NaiveDateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(NaiveDateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# --- NO IMPORTAR MODELOS CONCRETOS AQUÍ PARA EVITAR CÍRCULOS --- 