import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.tools.semantic_search_optimized import get_semantic_search

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando warmup del backend...")
    try:
        logger.info("⚡ Precargando motor semántico...")
        semantic_search = await get_semantic_search()
        logger.info("✅ Motor semántico precargado")
        test_results = await semantic_search.search("test", k=1)
        logger.info(f"🧪 Prueba de warmup: {len(test_results)} resultados")
        logger.info("🎉 Warmup completado - Backend listo para tráfico")
    except Exception as e:
        logger.error(f"❌ Error en warmup: {e}", exc_info=True)
    yield
    logger.info("🔄 Cerrando backend...") 