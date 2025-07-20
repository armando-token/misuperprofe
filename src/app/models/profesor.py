from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base # Asumiendo que Base está en app.models.base
from app.db.custom_types import NaiveDateTime # Para created_at, updated_at
from sqlalchemy.sql import func # Para server_default

# Importar la tabla de asociación definida en associations.py
from .associations import profesor_grupo_clase_association

class Profesor(Base):
    __tablename__ = "profesor"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(NaiveDateTime, server_default=func.now(), nullable=False)
    updated_at = Column(NaiveDateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relación muchos a muchos con GrupoClase
    # Se usará la tabla de asociación definida en associations.py
    grupos_clase = relationship(
        "GrupoClase",
        secondary=profesor_grupo_clase_association, # Usar el objeto Table importado
        back_populates="profesores"
    )

    def __repr__(self):
        return f"<Profesor {self.email}>" 