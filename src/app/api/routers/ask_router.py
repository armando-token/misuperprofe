from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
import logging

from app.tools.semantic_search_optimized import get_semantic_search, SerializedSemanticSearch

logger = logging.getLogger(__name__)
ask_router = APIRouter()

@ask_router.get("/ask", response_model=Dict[str, Any])
async def ask_question(
    query: str = Query(..., description="La pregunta del usuario"),
    semantic_search: SerializedSemanticSearch = Depends(get_semantic_search)
):
    """
    Recibe una pregunta, utiliza el motor de búsqueda semántica para encontrar
    el fragmento de teoría más relevante y lo devuelve.
    """
    if not query:
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía.")

    if not semantic_search.is_initialized:
        logger.error("El motor de búsqueda semántica no está inicializado.")
        raise HTTPException(status_code=503, detail="El servicio no está listo, por favor intente de nuevo en unos momentos.")

    logger.info(f"Buscando respuesta para la consulta: '{query}'")
    
    # La versión anterior tenía una lógica de búsqueda compleja con fallbacks.
    # Por ahora, usaremos la búsqueda semántica directa que es la más optimizada.
    # El documento old_server.md menciona otros fallbacks que se pueden añadir aquí si es necesario.
    results = await semantic_search.search(query, k=1)

    if not results:
        logger.warning(f"No se encontraron resultados para la consulta: '{query}'")
        # TODO: Implementar la lógica de fallback como se describe en old_server.md,
        # por ahora, devolvemos un 404.
        raise HTTPException(status_code=404, detail="No se encontró contenido relevante para su pregunta.")

    best_match, score = results[0]
    
    logger.info(f"Mejor resultado encontrado para '{query}': Capítulo '{best_match.titulo}' con un score de {score:.4f}")

    return {
        "titulo": best_match.titulo,
        "contenido": best_match.contenido_html or best_match.contenido_md,
        "score": score,
        "tipo": "semantic_v2" # Indica que la respuesta viene del motor optimizado
    } 