"""Tool MCP para calificar respuestas de estudiantes."""

from typing import Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_session
from app.models.resultado import Resultado
from app.core.mcp import mcp

@mcp.tool()
async def calificar_respuesta(
    pregunta_id: int,
    respuesta: str,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Califica la respuesta de un estudiante a una pregunta específica.
    
    Args:
        pregunta_id: ID de la pregunta a calificar
        respuesta: Respuesta del estudiante (texto)
        db: Sesión de base de datos asíncrona
        
    Returns:
        Dict con las siguientes claves:
            - correcto: bool indicando si la respuesta es correcta
            - feedback: Texto con retroalimentación
            - puntos: Puntos obtenidos (0-100)
    """
    try:
        # Lógica de calificación deshabilitada: tabla Pregunta eliminada
        raise NotImplementedError('La calificación directa de preguntas está deshabilitada. Solo teoría disponible.')
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de base de datos: {str(e)}"
        ) 