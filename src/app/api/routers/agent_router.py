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
        
        # Por ahora, retornamos una respuesta temporal mientras se inicializa la búsqueda semántica
        return {"respuesta": f"Tu pregunta sobre '{pregunta}' está siendo procesada. La búsqueda semántica se está inicializando. Por favor, intenta nuevamente en unos minutos."}
        
    except Exception as e:
        logger.error(f"Error en endpoint /ask: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

logger.info("agent_router.py cargado en versión mínima.")
