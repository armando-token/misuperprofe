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
from sqlalchemy import text

@mcp.tool()
async def recomendar_plan_estudio(
    user_id: str,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Genera un plan de estudio personalizado basado en el rendimiento.
    
    Args:
        user_id: ID del usuario (email)
        db: Sesión de base de datos asíncrona
        
    Returns:
        Dict con:
            - prioridades: Lista de materias ordenadas por prioridad
            - recomendaciones: Dict con recomendaciones por materia
    """
    try:
        # Obtener datos del usuario desde la tabla resultado
        query = text("""
        SELECT 
            cur.nombre as materia,
            COUNT(*) as total_intentos,
            SUM(CASE WHEN r.es_correcta THEN 1 ELSE 0 END) as aciertos,
            SUM(CASE WHEN NOT r.es_correcta THEN 1 ELSE 0 END) as errores
        FROM resultado r
        JOIN capitulo c ON r.capitulo_id = c.id
        JOIN curso cur ON c.curso_id = cur.id
        WHERE r.estudiante_id = :user_id
        GROUP BY cur.nombre
        ORDER BY (SUM(CASE WHEN r.es_correcta THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) ASC
        """)
        
        result = await db.execute(query, {"user_id": user_id})
        metricas = result.fetchall()
        
        if not metricas:
            return {
                "prioridades": [],
                "recomendaciones": {},
                "mensaje": "No hay datos de rendimiento disponibles para este usuario"
            }
            
        # Generar recomendaciones
        recomendaciones = {}
        prioridades = []
        
        for row in metricas:
            materia = row.materia
            total = row.total_intentos
            aciertos = row.aciertos
            errores = row.errores
            
            porcentaje_correcto = (aciertos / total * 100) if total > 0 else 0
            prioridades.append(materia)
            
            if porcentaje_correcto < 60:
                nivel = "alto"
                msg = "Necesita refuerzo urgente"
            elif porcentaje_correcto < 80:
                nivel = "medio"
                msg = "Puede mejorar"
            else:
                nivel = "bajo"
                msg = "Buen rendimiento"
                
            recomendaciones[materia] = {
                "nivel_prioridad": nivel,
                "mensaje": msg,
                "porcentaje_actual": round(porcentaje_correcto, 2),
                "total_intentos": total,
                "aciertos": aciertos,
                "errores": errores
            }
            
        return {
            "prioridades": prioridades,
            "recomendaciones": recomendaciones,
            "usuario": user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar recomendaciones: {str(e)}"
        ) 