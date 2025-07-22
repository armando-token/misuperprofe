"""Esquemas para el modelo Curso."""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from .base import BaseSchema, TimestampSchema


class CursoBase(BaseSchema):
    """Esquema base para Curso."""
    identificador: str
    nombre: str
    descripcion: str


class CursoCreate(CursoBase):
    """Esquema para crear un Curso."""
    pass


class CursoUpdate(CursoBase):
    """Esquema para actualizar un Curso."""
    pass


class CursoSchema(CursoBase):
    """Esquema completo de Curso."""
    id: int 
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CursoPublico(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CursoPublicoListResponse(BaseModel):
    cursos: List[CursoPublico] 