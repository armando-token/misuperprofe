# Este archivo está intencionalmente vacío.
# Los esquemas Pydantic para preguntas generadas dinámicamente (si son necesarios)
# se definirán aquí en el futuro, sin depender de un modelo de base de datos.

from typing import Optional, List
from pydantic import BaseModel, Field

class QuestionRequest(BaseModel):
    """Request schema for generating questions."""
    course: str = Field(..., description="Course name")
    chapter_id: int = Field(..., description="Chapter ID or order")

class GeneratedQuestion(BaseModel):
    """Response schema for generated questions."""
    pregunta: str = Field(..., description="The question text")
    opciones: List[str] = Field(..., description="Multiple choice options")
    respuesta_correcta: str = Field(..., description="Correct answer")
    explicacion: Optional[str] = Field(None, description="Explanation for the answer") 