# Este archivo está intencionalmente vacío.
# Los esquemas Pydantic para preguntas generadas dinámicamente (si son necesarios)
# se definirán aquí en el futuro, sin depender de un modelo de base de datos.

# from typing import Optional
# from pydantic import Field, field_validator

# from .base import BaseSchema, TimestampSchema


# class PreguntaBase(BaseSchema):
#     """Atributos comunes para crear y leer preguntas."""
#     enunciado: str = Field(..., min_length=10)
#     opcion_a: str = Field(..., min_length=1, max_length=500)
#     opcion_b: str = Field(..., min_length=1, max_length=500)
#     opcion_c: str = Field(..., min_length=1, max_length=500)
#     opcion_d: str = Field(..., min_length=1, max_length=500)
#     correcta: str = Field(..., min_length=1, max_length=1)
#     explicacion: Optional[str] = None

#     @field_validator('correcta')
#     def validar_opcion_correcta(cls, v: str) -> str:
#         v = v.upper()
#         if v not in ['A', 'B', 'C', 'D']:
#             raise ValueError('La opción correcta debe ser A, B, C o D')
#         return v


# class PreguntaCreate(PreguntaBase):
#     """Atributos para crear una pregunta."""
#     capitulo_id: int


# class PreguntaUpdate(BaseSchema):
#     """Atributos que se pueden actualizar de una pregunta."""
#     enunciado: Optional[str] = Field(None, min_length=10)
#     opcion_a: Optional[str] = Field(None, min_length=1, max_length=500)
#     opcion_b: Optional[str] = Field(None, min_length=1, max_length=500)
#     opcion_c: Optional[str] = Field(None, min_length=1, max_length=500)
#     opcion_d: Optional[str] = Field(None, min_length=1, max_length=500)
#     correcta: Optional[str] = Field(None, min_length=1, max_length=1)
#     explicacion: Optional[str] = None


# class Pregunta(PreguntaBase, TimestampSchema):
#     """Atributos completos de una pregunta."""
#     id: int
#     capitulo_id: int


# class PreguntaResponse(PreguntaBase):
#     """Respuesta del endpoint de preguntas."""
#     id: int
#     capitulo_id: int 