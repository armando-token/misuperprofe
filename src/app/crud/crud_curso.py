from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import logging

from app.models.curso import Curso

logger = logging.getLogger(__name__)

async def get_all_cursos(db: AsyncSession) -> List[Curso]:
    """
    Obtiene todos los cursos de la base de datos.
    """
    result = await db.execute(select(Curso).order_by(Curso.nombre))
    cursos = list(result.scalars().all())
    logger.info("Cursos recuperados por get_all_cursos:")
    for curso_obj in cursos:
        nombre_db = curso_obj.nombre
        logger.info(f"  ID: {curso_obj.id}, Nombre en DB: '|{nombre_db}|', Longitud: {len(nombre_db)}, Ordinales: {[ord(c) for c in nombre_db]}")
    return cursos

async def get_curso_by_nombre(db: AsyncSession, nombre: str) -> Curso | None:
    """
    Obtiene un curso por su nombre.
    """
    result = await db.execute(
        select(Curso).filter(func.lower(Curso.nombre) == func.lower(nombre))
    )
    return result.scalars().first() 