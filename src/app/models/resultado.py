from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Resultado(Base):
    __tablename__ = 'resultado'
    """Modelo para registrar las respuestas de los estudiantes a las preguntas."""
    
    id = Column(Integer, primary_key=True, index=True)
    estudiante_id = Column(String(100), nullable=False)  # ID externo del estudiante
    capitulo_id = Column(Integer, ForeignKey("capitulo.id"), nullable=False)
    respuesta = Column(String(1), nullable=False)  # 'A', 'B', 'C' o 'D'
    es_correcta = Column(Boolean, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    feedback = Column(Text, nullable=True)
    pregunta_generada = Column(Text, nullable=True) # Pregunta generada por el LLM
    respuesta_usuario = Column(Text, nullable=True) # Respuesta textual del usuario al LLM
    
    capitulo = relationship("Capitulo")
    # pregunta = relationship("Pregunta", back_populates="resultados")
    
    def __repr__(self) -> str:
        return f"<Resultado {self.id} - Est:{self.estudiante_id}>" 