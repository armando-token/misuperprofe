"""Sistema de Cache Inteligente para Optimización de Rendimiento."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import hashlib
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from app.db.session import get_session
from app.core.mcp import mcp

# Configuración de Redis
REDIS_URL = "redis://redis:6379"  # Usar el nombre del servicio Docker
CACHE_TTL = 3600  # 1 hora por defecto

class CacheOptimizer:
    def __init__(self):
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Inicializa conexión a Redis."""
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        except Exception as e:
            print(f"Warning: Redis no disponible: {e}")
            self.redis_client = None
    
    async def get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos del cache."""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Error al obtener cache: {e}")
        return None
    
    async def set_cache(self, key: str, data: Dict[str, Any], ttl: int = CACHE_TTL):
        """Guarda datos en cache."""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            print(f"Error al guardar cache: {e}")
    
    def generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Genera clave de cache basada en parámetros."""
        param_str = json.dumps(params, sort_keys=True)
        return f"{prefix}:{hashlib.md5(param_str.encode()).hexdigest()}"
    
    async def invalidate_cache_pattern(self, pattern: str):
        """Invalida cache por patrón."""
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Error al invalidar cache: {e}")

# Instancia global
cache_optimizer = CacheOptimizer()

@mcp.tool()
async def get_cached_analytics(
    analytics_type: str,
    days: int = 30,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Obtiene analytics con cache inteligente.
    
    Args:
        analytics_type: Tipo de analytics ("overview", "course_performance", "user_activity")
        days: Número de días para analizar
        db: Sesión de base de datos
        
    Returns:
        Dict con analytics y información de cache
    """
    try:
        # Generar clave de cache
        cache_key = cache_optimizer.generate_cache_key(
            f"analytics:{analytics_type}",
            {"days": days}
        )
        
        # Intentar obtener del cache
        cached_data = await cache_optimizer.get_cache(cache_key)
        if cached_data:
            return {
                **cached_data,
                "cache_hit": True,
                "cache_key": cache_key
            }
        
        # Si no está en cache, obtener datos frescos
        if analytics_type == "overview":
            from app.api.analytics import get_analytics_overview
            data = await get_analytics_overview(db, days)
        elif analytics_type == "course_performance":
            from app.api.analytics import get_course_performance
            data = await get_course_performance(db, days)
        elif analytics_type == "user_activity":
            from app.api.analytics import get_user_activity
            data = await get_user_activity(db, days)
        else:
            raise HTTPException(status_code=400, detail="Tipo de analytics no válido")
        
        # Guardar en cache
        await cache_optimizer.set_cache(cache_key, data)
        
        return {
            **data,
            "cache_hit": False,
            "cache_key": cache_key
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener analytics con cache: {str(e)}"
        )

@mcp.tool()
async def optimize_semantic_search_cache(
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Optimiza el cache de búsqueda semántica.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Dict con información de optimización
    """
    try:
        # Obtener estadísticas de uso de embeddings
        query = text("""
        SELECT 
            COUNT(DISTINCT capitulo_id) as capitulos_con_embeddings,
            COUNT(*) as total_embeddings
        FROM capitulo
        """)
        
        result = await db.execute(query)
        stats = result.fetchone()
        
        # Invalidar cache de búsqueda semántica
        await cache_optimizer.invalidate_cache_pattern("semantic_search:*")
        
        return {
            "capitulos_con_embeddings": stats.capitulos_con_embeddings or 0,
            "total_embeddings": stats.total_embeddings or 0,
            "cache_invalidado": True,
            "mensaje": "Cache de búsqueda semántica optimizado"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al optimizar cache: {str(e)}"
        )

@mcp.tool()
async def get_cache_stats() -> Dict[str, Any]:
    """Obtiene estadísticas del cache.
    
    Returns:
        Dict con estadísticas del cache
    """
    try:
        if not cache_optimizer.redis_client:
            return {
                "redis_disponible": False,
                "mensaje": "Redis no está disponible"
            }
        
        # Obtener información de Redis
        info = await cache_optimizer.redis_client.info()
        
        # Obtener patrones de cache
        patterns = [
            "analytics:*",
            "semantic_search:*",
            "user_stats:*",
            "course_data:*"
        ]
        
        cache_stats = {}
        for pattern in patterns:
            keys = await cache_optimizer.redis_client.keys(pattern)
            cache_stats[pattern] = len(keys)
        
        return {
            "redis_disponible": True,
            "redis_version": info.get("redis_version", "unknown"),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "cache_stats": cache_stats,
            "total_keys": sum(cache_stats.values())
        }
        
    except Exception as e:
        return {
            "redis_disponible": False,
            "error": str(e)
        }

@mcp.tool()
async def clear_all_cache() -> Dict[str, Any]:
    """Limpia todo el cache del sistema.
    
    Returns:
        Dict con información de limpieza
    """
    try:
        if not cache_optimizer.redis_client:
            return {
                "redis_disponible": False,
                "mensaje": "Redis no está disponible"
            }
        
        # Limpiar todo el cache
        await cache_optimizer.redis_client.flushdb()
        
        return {
            "redis_disponible": True,
            "cache_limpiado": True,
            "mensaje": "Todo el cache ha sido limpiado"
        }
        
    except Exception as e:
        return {
            "redis_disponible": False,
            "error": str(e)
        } 