"""Esquemas de la aplicación."""

from .curso import CursoSchema, CursoCreate, CursoUpdate
# Elimino la importación problemática para evitar el error de importación circular
# from app.schemas import UserProgressState, ChapterWithProgress, CourseChapterListResponse

__all__ = [
    "CursoSchema",
    "CursoCreate",
    "CursoUpdate",
]