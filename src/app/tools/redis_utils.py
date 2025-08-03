import os
import redis
import json
import time
from app.config import settings  # Importar settings
from datetime import datetime # Asegurar que datetime está importado aquí
from typing import Optional
import logging # Añadido para logging

logger = logging.getLogger(__name__) # Añadido para logging

# Retry logic para conexión Redis
for _ in range(3):
    try:
        redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.ping()
        break
    except Exception as e:
        print(f"Redis connection failed: {e}, retrying...")
        time.sleep(1)
else:
    redis_client = None
    print("Redis connection failed after retries.")

# Claves de Redis con session_id
LESSON_QUEUE = "lesson:{user_id}:{session_id}:queue"
ERROR_QUEUE = "lesson:{user_id}:{session_id}:error_queue"
# LEADERBOARD_WEEKLY ya no se usará directamente, la clave se genera dinámicamente
REDIS_ERROR_FLAG_PREFIX = "error_flag:"

# Helper para generar la clave semanal del leaderboard
def _get_current_weekly_leaderboard_key(base_league_id: str) -> str:
    now = datetime.utcnow()
    year, week, _ = now.isocalendar() # weekday no se usa aquí
    # Usar : como separador general y - para la fecha para evitar confusiones
    return f"leaderboard:weekly:{base_league_id}:{year}-{week:02d}" # Asegurar week con dos dígitos

# Funciones para la cola de la lección

def push_lesson_queue(user_id, session_id, item_ids):
    key = LESSON_QUEUE.format(user_id=user_id, session_id=session_id)
    if redis_client:
        redis_client.delete(key)
        if item_ids:
            serialized = [json.dumps(item) if isinstance(item, dict) else str(item) for item in item_ids]
            redis_client.rpush(key, *serialized)

def pop_lesson_queue(user_id, session_id):
    key = LESSON_QUEUE.format(user_id=user_id, session_id=session_id)
    if redis_client:
        item = redis_client.lpop(key)
        try:
            return json.loads(item)
        except Exception:
            return item
    return None

def lesson_queue_size(user_id, session_id):
    key = LESSON_QUEUE.format(user_id=user_id, session_id=session_id)
    if redis_client:
        return redis_client.llen(key)
    return 0

# Funciones para la cola de errores

def push_error_queue(user_id, session_id, item_id):
    key = ERROR_QUEUE.format(user_id=user_id, session_id=session_id)
    if redis_client:
        max_size = 10
        if redis_client.llen(key) < max_size:
            val = json.dumps(item_id) if isinstance(item_id, dict) else str(item_id)
            redis_client.rpush(key, val)

def pop_error_queue(user_id, session_id):
    key = ERROR_QUEUE.format(user_id=user_id, session_id=session_id)
    if redis_client:
        item = redis_client.lpop(key)
        try:
            return json.loads(item)
        except Exception:
            return item
    return None

def error_queue_size(user_id, session_id):
    key = ERROR_QUEUE.format(user_id=user_id, session_id=session_id)
    if redis_client:
        return redis_client.llen(key)
    return 0

def clear_queues(user_id, session_id):
    if redis_client:
        redis_client.delete(LESSON_QUEUE.format(user_id=user_id, session_id=session_id))
        redis_client.delete(ERROR_QUEUE.format(user_id=user_id, session_id=session_id))

# Funciones para leaderboard semanal

async def add_xp_leaderboard(base_league_id: str, user_id: str, xp_increment: int):
    if not redis_client or xp_increment == 0: # No hacer nada si no hay cliente o no hay XP que añadir
        return
    key = _get_current_weekly_leaderboard_key(base_league_id)
    redis_client.zincrby(key, float(xp_increment), user_id) # Redis zincrby score must be float

def get_leaderboard(base_league_id: str, top_n: int = 10):
    logger.debug(f"get_leaderboard_DEBUG: Entrando a la función con base_league_id='{base_league_id}', top_n={top_n}")
    if not redis_client:
        logger.warning("redis_client es None. Retornando lista vacía.")
        return []
    key = _get_current_weekly_leaderboard_key(base_league_id)
    logger.debug(f"get_leaderboard_DEBUG: Clave generada para Redis: '{key}'")
    
    raw_data = None
    try:
        logger.debug(f"get_leaderboard_DEBUG: Intentando zrevrange en la clave '{key}'")
        raw_data = redis_client.zrevrange(key, 0, top_n - 1, withscores=True)
        logger.debug(f"get_leaderboard_DEBUG: Datos crudos de Redis: {raw_data}")
    except redis.exceptions.RedisError as e:
        logger.error(f"Error de Redis al ejecutar zrevrange: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error inesperado al ejecutar zrevrange: {e}", exc_info=True)
        return []

    result = []
    if isinstance(raw_data, (list, tuple)):
        for entry in raw_data:
            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                uid_bytes, xp_score_bytes = entry
                uid = uid_bytes.decode('utf-8') if isinstance(uid_bytes, bytes) else str(uid_bytes)
                xp_score_str = xp_score_bytes.decode('utf-8') if isinstance(xp_score_bytes, bytes) else str(xp_score_bytes)
                
                try:
                    xp = int(float(xp_score_str))
                except (ValueError, TypeError):
                    logger.warning(f"No se pudo convertir el score '{xp_score_str}' a int para el uid '{uid}'. Usando 0.")
                    xp = 0
                result.append((uid, xp))
            else:
                logger.warning(f"Entrada inesperada en raw_data, se esperaba tupla de 2 elementos: {entry}")
    else:
        logger.warning(f"raw_data no es una lista o tupla, o está vacío: {raw_data}")
        
    logger.debug(f"get_leaderboard_DEBUG: Leaderboard procesado: {result}")
    return result

def get_user_rank_in_leaderboard(base_league_id: str, user_id: str) -> Optional[int]:
    if not redis_client:
        return None
    key = _get_current_weekly_leaderboard_key(base_league_id)
    rank = redis_client.zrevrank(key, user_id) # zrevrank es 0-indexed
    if rank is not None:
        return rank + 1 # Convertir a 1-indexed
    return None # Usuario no encontrado en el leaderboard 