"""Tool MCP para recomendar planes de estudio."""

from typing import Dict, Any, List
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import case

from app.db.session import get_session
from app.models.resultado import Resultado
from app.models.capitulo import Capitulo
from app.models.curso import Curso
from app.resources.metricas import obtener_metricas_por_materia
from app.core.mcp import mcp

@mcp.tool()
async def recomendar_plan_estudio(
    alumno_id: int,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Genera un plan de estudio personalizado basado en el rendimiento.
    
    Args:
        alumno_id: ID del alumno
        db: Sesión de base de datos asíncrona
        
    Returns:
        Dict con:
            - prioridades: Lista de materias ordenadas por prioridad
            - recomendaciones: Dict con recomendaciones por materia
    """
    try:
        # Obtener métricas actuales
        metricas = await obtener_metricas_por_materia(alumno_id, db)
        
        if not metricas:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron métricas para el alumno"
            )
            
        # Ordenar materias por rendimiento (menor a mayor)
        materias_ordenadas = sorted(
            metricas,
            key=lambda x: (x.aciertos / (x.aciertos + x.errores) * 100) if (x.aciertos + x.errores) > 0 else 0
        )
        
        # Generar recomendaciones
        recomendaciones = {}
        for materia in materias_ordenadas:
            total = materia.aciertos + materia.errores
            porcentaje_correcto = (materia.aciertos / total * 100) if total > 0 else 0
            if porcentaje_correcto < 60:
                nivel = "alto"
                msg = "Necesita refuerzo urgente"
            elif porcentaje_correcto < 80:
                nivel = "medio"
                msg = "Puede mejorar"
            else:
                nivel = "bajo"
                msg = "Buen rendimiento"
            recomendaciones[materia.materia] = {
                "nivel_prioridad": nivel,
                "mensaje": msg,
                "porcentaje_actual": porcentaje_correcto
            }
            
        return {
            "prioridades": [m.materia for m in materias_ordenadas],
            "recomendaciones": recomendaciones
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar recomendaciones: {str(e)}"
        ) 