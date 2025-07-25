from fastapi import APIRouter, Depends, HTTPException
import logging
import hashlib
import json
from typing import Dict, Optional

logger = logging.getLogger(__name__)

agent_router = APIRouter()

# Cache para resultados de búsqueda semántica
_search_cache: Dict[str, Dict] = {}

def _get_cache_key(pregunta: str) -> str:
    """Genera una clave de cache para la pregunta"""
    return hashlib.md5(pregunta.lower().strip().encode()).hexdigest()

@agent_router.post("/agent/chat")
async def agent_chat_placeholder():
    logger.warning("El endpoint /agent/chat ha sido deshabilitado temporalmente para depuración.")
    raise HTTPException(status_code=503, detail="Endpoint deshabilitado temporalmente.")

# Endpoints de negocio
@agent_router.post("/courses")
async def list_courses():
    """
    Endpoint para obtener la lista de cursos disponibles
    """
    logger.info("🔍 [AGENT_COURSES] Petición recibida en /courses (POST)")
    
    try:
        courses = [
            {
                "id": "biologia",
                "name": "Biología",
                "description": "Estudio de los seres vivos y sus procesos",
                "chapters": 5
            },
            {
                "id": "historia",
                "name": "Historia",
                "description": "Estudio del pasado humano y sus eventos",
                "chapters": 4
            },
            {
                "id": "lenguaje",
                "name": "Lenguaje",
                "description": "Comunicación y expresión escrita",
                "chapters": 3
            },
            {
                "id": "geografia",
                "name": "Geografía",
                "description": "Estudio de la Tierra y sus características",
                "chapters": 4
            },
            {
                "id": "filosofia",
                "name": "Filosofía",
                "description": "Reflexión sobre la existencia y el conocimiento",
                "chapters": 3
            },
            {
                "id": "literatura",
                "name": "Literatura",
                "description": "Arte de la expresión escrita",
                "chapters": 4
            },
            {
                "id": "economia",
                "name": "Economía",
                "description": "Estudio de la producción y distribución de recursos",
                "chapters": 3
            },
            {
                "id": "civica",
                "name": "Cívica",
                "description": "Derechos y deberes ciudadanos",
                "chapters": 3
            },
            {
                "id": "psicologia",
                "name": "Psicología",
                "description": "Estudio del comportamiento humano",
                "chapters": 4
            },
            {
                "id": "cultura_general",
                "name": "Cultura General",
                "description": "Conocimientos generales y actualidad",
                "chapters": 5
            }
        ]
        
        response = {"courses": courses, "total": len(courses)}
        logger.info("✅ [AGENT_COURSES] Respuesta exitosa: %s", response)
        return response
        
    except Exception as e:
        logger.error("❌ [AGENT_COURSES] Error en /courses: %s", str(e))
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@agent_router.post("/ask")
async def ask_question(payload: dict):
    """
    Endpoint para buscar respuestas en la base de datos usando búsqueda semántica (OPTIMIZADO)
    """
    logger.info(f"Endpoint /ask llamado con payload: {payload}")
    
    try:
        # Validar que payload sea un diccionario
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Payload debe ser un objeto JSON válido")
        
        pregunta = payload.get("pregunta", "")
        if not pregunta:
            raise HTTPException(status_code=400, detail="La pregunta es requerida")
        
        # Validar tamaño de la pregunta
        if len(pregunta) > 1000:
            raise HTTPException(status_code=400, detail="La pregunta es demasiado larga (máximo 1000 caracteres)")
        
        # Verificar cache primero
        cache_key = _get_cache_key(pregunta)
        if cache_key in _search_cache:
            logger.info(f"Resultado encontrado en cache para: {pregunta[:50]}...")
            return _search_cache[cache_key]
        
        # Importar y usar la búsqueda semántica optimizada
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
                
                # Crear respuesta con información del capítulo
                respuesta = f"Según el capítulo '{chapter.titulo}':\n\n{contenido[:500]}..."
                
                result = {"respuesta": respuesta}
                
                # Guardar en cache (máximo 1000 entradas)
                if len(_search_cache) < 1000:
                    _search_cache[cache_key] = result
                
                return result
            else:
                result = {"respuesta": "No encontré información específica sobre tu pregunta. ¿Podrías reformularla o ser más específico?"}
                
                # Guardar en cache
                if len(_search_cache) < 1000:
                    _search_cache[cache_key] = result
                
                return result
                
        except Exception as search_error:
            logger.error(f"Error en búsqueda semántica: {search_error}")
            return {"respuesta": f"Tu pregunta sobre '{pregunta}' está siendo procesada. La búsqueda semántica se está inicializando. Por favor, intenta nuevamente en unos minutos."}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /ask: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

logger.info("agent_router.py cargado en versión optimizada.")
