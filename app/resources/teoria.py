"""Resource MCP para obtener contenido teórico de cursos."""

from typing import Optional, Dict, List, Union, Annotated
from fastapi import Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import get_db
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.core.mcp import mcp

@mcp.router.get("/resource/teoria/{curso}")
async def obtener_teoria(
    curso: str,
    capitulo: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Union[str, List[str]]]:
    """Obtiene el contenido teórico de un curso o capítulo específico.
    
    Args:
        curso: Identificador del curso (ej: "biologia", "fisica")
        capitulo: Título del capítulo específico (opcional)
        db: Sesión de base de datos asíncrona
        
    Returns:
        Dict con las siguientes claves:
            - contenido: Contenido markdown del capítulo o curso completo
            - capitulos: Lista de títulos de capítulos incluidos
        
    Raises:
        HTTPException: 
            - 404 si no se encuentra el curso o capítulo
            - 500 si hay error de base de datos
    """
    try:
        # Buscar el curso
        stmt = select(Curso).filter_by(codigo=curso)
        result = await db.execute(stmt)
        curso_db = result.scalar_one_or_none()
        
        if not curso_db:
            raise HTTPException(
                status_code=404,
                detail=f"Curso '{curso}' no encontrado"
            )

        # Si se especifica capítulo, buscar solo ese
        if capitulo:
            stmt = select(Capitulo).filter_by(
                curso_id=curso_db.id,
                titulo=capitulo
            )
            result = await db.execute(stmt)
            cap = result.scalar_one_or_none()
            
            if not cap:
                raise HTTPException(
                    status_code=404,
                    detail=f"Capítulo '{capitulo}' no encontrado en curso '{curso}'"
                )
            
            return {
                "contenido": cap.contenido_md,
                "capitulos": [cap.titulo]
            }
    
        # Si no se especifica capítulo, concatenar todos
        stmt = select(Capitulo).filter_by(curso_id=curso_db.id)
        result = await db.execute(stmt)
        caps = result.scalars().all()
        
        return {
            "contenido": "\n\n".join(cap.contenido_md for cap in caps),
            "capitulos": [cap.titulo for cap in caps]
        }
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de base de datos: {str(e)}"
        ) 