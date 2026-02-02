from redis import Redis
from app.settings import settings

_redis: Redis | None = None


def get_redis() -> Redis | None:
    global _redis
    if not settings.USE_REDIS:
        return None
    if _redis is None:
        _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis
