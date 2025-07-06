import redis
from core.config import settings

try:
    redis_client = redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    redis_client.ping()
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None 