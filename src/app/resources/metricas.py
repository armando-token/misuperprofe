"""Resource MCP para obtener métricas de estudiantes."""

from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, select, cast
from sqlalchemy import Integer

from app.db.session import get_session
from app.models.resultado import Resultado
from app.models.capitulo import Capitulo
from app.models.curso import Curso
from app.schemas.metricas import MetricasPorMateria
from app.core.mcp import mcp

@mcp.router.get("/resource/metricas_por_materia/{alumno_id}", response_model=List[MetricasPorMateria])
async def obtener_metricas_por_materia(
    alumno_id: int,
    session: AsyncSession = Depends(get_session)
) -> List[MetricasPorMateria]:
    """Obtiene las métricas por materia para un alumno.
    
    Args:
        alumno_id: ID del alumno
        session: Sesión de base de datos
        
    Returns:
        Lista de MetricasPorMateria con aciertos y errores por materia
    """
    query = (
        select(
            Curso.nombre.label("materia"),
            func.sum(cast(Resultado.es_correcta, Integer)).label("aciertos"),
            func.sum(cast(~Resultado.es_correcta, Integer)).label("errores")
        )
        .join(Capitulo, Resultado.capitulo_id == Capitulo.id)
        .join(Curso, Capitulo.curso_id == Curso.id)
        .where(Resultado.estudiante_id == str(alumno_id))  # Convertir a string ya que estudiante_id es String
        .group_by(Curso.nombre)
    )
    
    result = await session.execute(query)
    rows = result.all()
    
    return [
        MetricasPorMateria(
            materia=row.materia,
            aciertos=row.aciertos or 0,
            errores=row.errores or 0
        )
        for row in rows
    ] 