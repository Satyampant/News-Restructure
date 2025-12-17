"""
Redis Cache Service for Entity Extraction.
"""

import json
import hashlib
import logging
from typing import Optional, Any, Dict
from datetime import timedelta
from src.configuration.loader import get_config

logger = logging.getLogger(__name__)

try:
    import redis
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not installed. Install with: pip install redis")

class RedisCacheService:
    """Shared Redis cache with TTL management."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = None,
        password: str = None,
        ttl_seconds: int = None,
        key_prefix: str = "marketmuni:entities:"
    ):
        config = get_config()
        
        # Load from config or use overrides
        # Note: Assuming config object structure matches the new settings.py
        self.host = host or config.redis.host
        self.port = port or config.redis.port
        self.db = db or getattr(config.redis, 'db', 0)
        self.password = password or getattr(config.redis, 'password', None)
        self.ttl_seconds = ttl_seconds or getattr(config.redis, 'ttl_seconds', 3600)
        self.key_prefix = key_prefix
        
        self.client: Optional[redis.Redis] = None
        self.is_connected = False
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            return
        
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection with retry logic."""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            self.client.ping()
            self.is_connected = True
            logger.info(f"✓ Redis connected: {self.host}:{self.port} (db={self.db})")
            
        except (RedisConnectionError, RedisError) as e:
            logger.warning(f"Redis connection failed: {e}")
            logger.warning("Entity extraction will work without caching")
            self.is_connected = False
            self.client = None
    
    def _make_key(self, article_id: str) -> str:
        # Hash ID to ensure fixed length and avoid invalid char issues
        hashed_id = hashlib.md5(article_id.encode()).hexdigest()
        return f"{self.key_prefix}{hashed_id}"
    
    def get(self, article_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected or self.client is None:
            return None
        
        try:
            key = self._make_key(article_id)
            cached_data = self.client.get(key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis GET error for {article_id}: {e}")
            return None
    
    def set(
        self,
        article_id: str,
        entity_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        if not self.is_connected or self.client is None:
            return False
        
        try:
            key = self._make_key(article_id)
            cache_ttl = ttl or self.ttl_seconds
            
            self.client.setex(
                name=key,
                time=timedelta(seconds=cache_ttl),
                value=json.dumps(entity_data)
            )
            return True
            
        except (RedisError, TypeError, ValueError) as e:
            logger.error(f"Redis SET error for {article_id}: {e}")
            return False
    
    def delete(self, article_id: str) -> bool:
        if not self.is_connected or self.client is None:
            return False
        
        try:
            key = self._make_key(article_id)
            deleted = self.client.delete(key)
            return deleted > 0
            
        except RedisError as e:
            logger.error(f"Redis DELETE error for {article_id}: {e}")
            return False
    
    def clear_all(self) -> int:
        """Clear all keys matching the prefix."""
        if not self.is_connected or self.client is None:
            return 0
        
        try:
            pattern = f"{self.key_prefix}*"
            keys = list(self.client.scan_iter(match=pattern, count=100))
            
            if not keys:
                return 0
            
            # Pipeline delete for performance
            pipeline = self.client.pipeline()
            for key in keys:
                pipeline.delete(key)
            pipeline.execute()
            
            return len(keys)
            
        except RedisError as e:
            logger.error(f"Redis CLEAR error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.is_connected or self.client is None:
            return {"connected": False, "cached_keys": 0, "total_keys": 0, "memory_used": "0 MB"}
        
        try:
            pattern = f"{self.key_prefix}*"
            cached_keys = sum(1 for _ in self.client.scan_iter(match=pattern, count=100))
            
            info = self.client.info('memory')
            memory_used_mb = info.get('used_memory', 0) / (1024 * 1024)
            
            return {
                "connected": True,
                "cached_keys": cached_keys,
                "total_keys": self.client.dbsize(),
                "memory_used": f"{memory_used_mb:.2f} MB",
                "ttl_seconds": self.ttl_seconds,
                "host": self.host,
                "port": self.port,
                "db": self.db
            }
            
        except RedisError as e:
            logger.error(f"Redis STATS error: {e}")
            return {"connected": False, "error": str(e)}
    
    def health_check(self) -> bool:
        if not self.is_connected or self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except RedisError:
            self.is_connected = False
            return False
    
    def reconnect(self) -> bool:
        if not REDIS_AVAILABLE:
            return False
        self._connect()
        return self.is_connected
    
    def close(self) -> None:
        if self.client is not None:
            try:
                self.client.close()
                logger.info("Redis connection closed")
            except RedisError as e:
                logger.warning(f"Error closing Redis: {e}")
            finally:
                self.is_connected = False
                self.client = None