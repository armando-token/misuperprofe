from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base
# Importar la tabla de asociación
from .associations import grupo_clase_curso_association


class Curso(Base):
    __tablename__ = 'curso'
    """Modelo para representar un curso."""
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, index=True, nullable=False)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(500))
    
    capitulos = relationship("Capitulo", back_populates="curso", cascade="all, delete-orphan")

    # Relación muchos-a-muchos con GrupoClase
    grupos_clase = relationship(
        "GrupoClase",
        secondary=grupo_clase_curso_association,
        back_populates="cursos"
    )
    
    def __repr__(self) -> str:
        return f"<Curso {self.nombre}>" 