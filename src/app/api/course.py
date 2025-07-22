"""
Endpoints para cursos y capítulos.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import logging
from typing import Optional, List

from app.db.session import get_session
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.config import settings

router = APIRouter(prefix="/course", tags=["course"])
logger = logging.getLogger(__name__)

# Modelos Pydantic
class ChapterInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    titulo: str
    orden: int
    curso_id: int
    resumen: Optional[str] = None

class CourseChaptersResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    course_id: str
    course_name: str
    chapters: List[ChapterInfo]
    total_chapters: int

def verify_bearer_token(request: Request):
    """Verifica el Bearer token."""
    auth = request.headers.get("Authorization")
    if not auth or auth != f"Bearer {settings.API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@router.get("/{course_name}/chapters", response_model=CourseChaptersResponse)
async def get_course_chapters(
    course_name: str = Path(..., description="Nombre del curso"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    request: Request = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Obtiene los capítulos de un curso específico con paginación.
    """
    verify_bearer_token(request)
    
    try:
        # Buscar el curso por nombre (case insensitive)
        curso_result = await db.execute(
            select(Curso).filter(Curso.nombre.ilike(f"%{course_name}%"))
        )
        curso = curso_result.scalars().first()
        
        if not curso:
            raise HTTPException(status_code=404, detail=f"Curso '{course_name}' no encontrado")
        
        # Obtener capítulos del curso con paginación
        offset = (page - 1) * page_size
        
        chapters_result = await db.execute(
            select(Capitulo)
            .filter(Capitulo.curso_id == curso.id)
            .order_by(Capitulo.orden)
            .offset(offset)
            .limit(page_size)
        )
        chapters = chapters_result.scalars().all()
        
        # Contar total de capítulos
        total_result = await db.execute(
            select(func.count(Capitulo.id))
            .filter(Capitulo.curso_id == curso.id)
        )
        total_chapters = total_result.scalar()
        
        # Preparar respuesta
        chapter_list = []
        for chapter in chapters:
            # Crear resumen del contenido
            content = chapter.contenido_html or chapter.contenido_md or ""
            if len(content) > 200:
                content = content[:200] + "..."
            
            chapter_info = ChapterInfo(
                id=chapter.id,
                titulo=chapter.titulo,
                orden=chapter.orden,
                curso_id=chapter.curso_id,
                resumen=content
            )
            chapter_list.append(chapter_info)
        
        return CourseChaptersResponse(
            course_id=course_name,
            course_name=curso.nombre,
            chapters=chapter_list,
            total_chapters=total_chapters
        )
        
    except Exception as e:
        logger.error(f"Error en get_course_chapters: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{course_name}/chapters/{chapter_id}")
async def get_chapter_detail(
    course_name: str = Path(..., description="Nombre del curso"),
    chapter_id: int = Path(..., description="ID del capítulo"),
    request: Request = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Obtiene el detalle de un capítulo específico.
    """
    verify_bearer_token(request)
    
    try:
        # Buscar el curso
        curso_result = await db.execute(
            select(Curso).filter(Curso.nombre.ilike(f"%{course_name}%"))
        )
        curso = curso_result.scalars().first()
        
        if not curso:
            raise HTTPException(status_code=404, detail=f"Curso '{course_name}' no encontrado")
        
        # Buscar el capítulo
        chapter_result = await db.execute(
            select(Capitulo)
            .filter(Capitulo.id == chapter_id, Capitulo.curso_id == curso.id)
        )
        chapter = chapter_result.scalars().first()
        
        if not chapter:
            raise HTTPException(status_code=404, detail=f"Capítulo {chapter_id} no encontrado en el curso '{course_name}'")
        
        return {
            "id": chapter.id,
            "titulo": chapter.titulo,
            "orden": chapter.orden,
            "curso_id": chapter.curso_id,
            "contenido_html": chapter.contenido_html,
            "contenido_md": chapter.contenido_md,
            "curso_nombre": curso.nombre
        }
        
    except Exception as e:
        logger.error(f"Error en get_chapter_detail: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{course_name}/last-chapter")
async def get_last_chapter(
    course_name: str = Path(..., description="Nombre del curso"),
    request: Request = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Obtiene el último capítulo de un curso.
    """
    verify_bearer_token(request)
    
    try:
        # Buscar el curso
        curso_result = await db.execute(
            select(Curso).filter(Curso.nombre.ilike(f"%{course_name}%"))
        )
        curso = curso_result.scalars().first()
        
        if not curso:
            raise HTTPException(status_code=404, detail=f"Curso '{course_name}' no encontrado")
        
        # Obtener el último capítulo (orden más alto)
        last_chapter_result = await db.execute(
            select(Capitulo)
            .filter(Capitulo.curso_id == curso.id)
            .order_by(Capitulo.orden.desc())
            .limit(1)
        )
        last_chapter = last_chapter_result.scalars().first()
        
        if not last_chapter:
            raise HTTPException(status_code=404, detail=f"No hay capítulos disponibles para el curso '{course_name}'")
        
        return {
            "id": last_chapter.id,
            "titulo": last_chapter.titulo,
            "orden": last_chapter.orden,
            "curso_id": last_chapter.curso_id,
            "contenido_html": last_chapter.contenido_html,
            "contenido_md": last_chapter.contenido_md,
            "curso_nombre": curso.nombre,
            "es_ultimo": True
        }
        
    except Exception as e:
        logger.error(f"Error en get_last_chapter: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}") 