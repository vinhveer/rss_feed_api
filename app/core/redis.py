import redis.asyncio as redis
from app.core.config import REDIS_URL
import json
from typing import Any, Optional


class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis and parse JSON"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value to Redis with TTL"""
        try:
            json_value = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, json_value)
            return True
        except Exception:
            return False

    async def delete(self, *keys: str) -> bool:
        """Delete keys from Redis"""
        try:
            await self.redis.delete(*keys)
            return True
        except Exception:
            return False

    async def close(self):
        """Close Redis connection"""
        await self.redis.close()


# Global Redis instance
redis_client = RedisClient()