from fastapi import APIRouter, Depends, HTTPException
import logging

logger = logging.getLogger(__name__)

agent_router = APIRouter()

@agent_router.post("/agent/chat")
async def agent_chat_placeholder():
    logger.warning("El endpoint /agent/chat ha sido deshabilitado temporalmente para depuración.")
    raise HTTPException(status_code=503, detail="Endpoint deshabilitado temporalmente.")

# Endpoints de negocio deshabilitados
@agent_router.post("/courses")
async def list_courses_placeholder():
    logger.warning("El endpoint /courses ha sido deshabilitado temporalmente para depuración.")
    raise HTTPException(status_code=503, detail="Endpoint deshabilitado temporalmente.")

@agent_router.post("/ask")
async def ask_question(payload: dict):
    """
    Endpoint para buscar respuestas en la base de datos usando búsqueda semántica.
    """
    logger.info(f"Endpoint /ask llamado con payload: {payload}")
    
    try:
        pregunta = payload.get("pregunta", "")
        if not pregunta:
            raise HTTPException(status_code=400, detail="La pregunta es requerida")
        
        # Importar y usar la búsqueda semántica
        from app.tools.semantic_search_optimized import get_semantic_search
        
        try:
            semantic_search = await get_semantic_search()
            results = await semantic_search.search(pregunta, k=3)
            
            if results and len(results) > 0:
                # Tomar el mejor resultado (primera tupla: (chapter, score))
                best_result = results[0]
                chapter, score = best_result
                
                # Obtener el contenido del capítulo
                contenido = chapter.contenido_html or chapter.contenido_md or ""
                
                # Limpiar HTML si existe
                import re
                contenido = re.sub(r'<[^>]+>', '', contenido)
                
                # Crear respuesta con información del capítulo (sin acceder a curso.nombre)
                respuesta = f"Según el capítulo '{chapter.titulo}':\n\n{contenido[:500]}..."
                
                return {"respuesta": respuesta}
            else:
                return {"respuesta": "No encontré información específica sobre tu pregunta. ¿Podrías reformularla o ser más específico?"}
                
        except Exception as search_error:
            logger.error(f"Error en búsqueda semántica: {search_error}")
            return {"respuesta": f"Tu pregunta sobre '{pregunta}' está siendo procesada. La búsqueda semántica se está inicializando. Por favor, intenta nuevamente en unos minutos."}
        
    except Exception as e:
        logger.error(f"Error en endpoint /ask: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

logger.info("agent_router.py cargado en versión mínima.")
