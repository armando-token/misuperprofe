from typing import Optional
from pydantic import Field, field_validator

from .base import BaseSchema, TimestampSchema


class ResultadoBase(BaseSchema):
    """Atributos comunes para crear y leer resultados."""
    respuesta: str = Field(..., min_length=1, max_length=1)
    es_correcta: bool
    feedback: Optional[str] = None

    @field_validator('respuesta')
    def validar_respuesta(cls, v: str) -> str:
        v = v.upper()
        if v not in ['A', 'B', 'C', 'D']:
            raise ValueError('La respuesta debe ser A, B, C o D')
        return v


class ResultadoCreate(ResultadoBase):
    """Atributos para crear un resultado."""
    capitulo_id: int


class ResultadoUpdate(BaseSchema):
    """Atributos que se pueden actualizar de un resultado."""
    feedback: Optional[str] = None


class Resultado(ResultadoBase, TimestampSchema):
    """Atributos completos de un resultado."""
    id: int
    capitulo_id: int


class LessonResultCreate(BaseSchema):
    """Payload para registrar el resultado de una lección evaluada por un LLM."""
    student_id: str = Field(..., description="Identificador único del estudiante.")
    chapter_id: int = Field(..., description="ID del capítulo al que pertenece la evaluación.")
    is_correct: bool = Field(..., description="Indica si la respuesta del usuario fue correcta.")
    user_response: Optional[str] = Field(None, description="Respuesta textual proporcionada por el usuario.")
    llm_question: Optional[str] = Field(None, description="Texto de la pregunta generada por el LLM.")
    llm_feedback: Optional[str] = Field(None, description="Feedback específico proporcionado por el LLM tras la respuesta.")
 