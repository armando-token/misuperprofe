from sqlalchemy import Column, Integer, String, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base


class Capitulo(Base):
    __tablename__ = 'capitulo'
    """Modelo para representar un capítulo de un curso."""
    
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey("curso.id"), nullable=False)
    titulo = Column(String(200), nullable=False)
    contenido_md = Column(Text, nullable=False)
    contenido_html = Column(Text, nullable=False)
    orden = Column(Integer, nullable=False, default=0)
    beta_difficulty = Column(Numeric(5,3), nullable=False, default=0.0, server_default="0.0")  # Dificultad IRT
    
    curso = relationship("Curso", back_populates="capitulos")
    progress_units = relationship("ProgressUnit", back_populates="capitulo", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Capitulo {self.id}: {self.titulo}>"

# preguntas = relationship("Pregunta", back_populates="capitulo", cascade="all, delete-orphan") 