"""
PDF-to-Markdown Extractor - Redis Client.

Redis connection helper with connection pooling and health checks.
"""

import os
from typing import Optional

import redis
from loguru import logger
from redis.connection import ConnectionPool


class RedisClient:
    """
    Redis client with connection pooling and health monitoring.

    This class provides a singleton Redis connection pool for efficient
    connection management across the application.

    Attributes:
        _instance: Singleton instance of RedisClient
        _pool: Redis connection pool
        _client: Redis client instance

    Example:
        >>> client = RedisClient.get_instance()
        >>> if client.ping():
        ...     print("Redis is connected")
        >>> client.set("key", "value", ex=3600)
        >>> value = client.get("key")
    """

    _instance: Optional["RedisClient"] = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis client with connection pooling.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0").
                      If not provided, uses REDIS_URL environment variable.

        Raises:
            ValueError: If redis_url is not provided and REDIS_URL env var is not set.
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        if not self.redis_url:
            raise ValueError(
                "Redis URL must be provided or set in REDIS_URL environment variable"
            )

        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """
        Initialize the Redis connection pool.

        Creates a connection pool with optimized settings for production use.
        """
        try:
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,  # Maximum connections in pool
                socket_timeout=5,    # Socket timeout in seconds
                socket_connect_timeout=5,  # Connection timeout
                socket_keepalive=True,     # Keep connections alive
                retry_on_timeout=True,     # Retry on timeout
                decode_responses=True,     # Auto-decode bytes to strings
            )
            self._client = redis.Redis(connection_pool=self._pool)
            logger.info(f"Redis connection pool initialized: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection pool: {e}")
            raise

    @classmethod
    def get_instance(cls, redis_url: Optional[str] = None) -> "RedisClient":
        """
        Get singleton instance of RedisClient.

        Args:
            redis_url: Redis connection URL (only used on first call).

        Returns:
            RedisClient: Singleton instance.

        Example:
            >>> client = RedisClient.get_instance()
            >>> same_client = RedisClient.get_instance()
            >>> assert client is same_client
        """
        if cls._instance is None:
            cls._instance = cls(redis_url)
        return cls._instance

    def ping(self) -> bool:
        """
        Health check: Ping Redis server.

        Returns:
            bool: True if Redis is reachable, False otherwise.

        Example:
            >>> client = RedisClient.get_instance()
            >>> if client.ping():
            ...     print("Redis is healthy")
        """
        try:
            return self._client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def get_client(self) -> redis.Redis:
        """
        Get the underlying Redis client instance.

        Returns:
            redis.Redis: Redis client for direct operations.

        Example:
            >>> client = RedisClient.get_instance()
            >>> redis_conn = client.get_client()
            >>> redis_conn.set("key", "value")
        """
        return self._client

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis.

        Args:
            key: Redis key.
            value: Value to store.
            ex: Expiration time in seconds (optional).

        Returns:
            bool: True if successful, False otherwise.

        Example:
            >>> client = RedisClient.get_instance()
            >>> client.set("session:123", "user_data", ex=3600)
        """
        try:
            return self._client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET failed for key '{key}': {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis.

        Args:
            key: Redis key.

        Returns:
            Optional[str]: Value if exists, None otherwise.

        Example:
            >>> client = RedisClient.get_instance()
            >>> value = client.get("session:123")
        """
        try:
            return self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed for key '{key}': {e}")
            return None

    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from Redis.

        Args:
            *keys: Keys to delete.

        Returns:
            int: Number of keys deleted.

        Example:
            >>> client = RedisClient.get_instance()
            >>> deleted = client.delete("key1", "key2")
        """
        try:
            return self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE failed: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """
        Check if one or more keys exist in Redis.

        Args:
            *keys: Keys to check.

        Returns:
            int: Number of existing keys.

        Example:
            >>> client = RedisClient.get_instance()
            >>> if client.exists("session:123"):
            ...     print("Session exists")
        """
        try:
            return self._client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis EXISTS failed: {e}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Redis key.
            seconds: Expiration time in seconds.

        Returns:
            bool: True if successful, False otherwise.

        Example:
            >>> client = RedisClient.get_instance()
            >>> client.expire("temp:data", 300)  # Expire in 5 minutes
        """
        try:
            return self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE failed for key '{key}': {e}")
            return False

    def disconnect(self) -> None:
        """
        Gracefully disconnect from Redis.

        Closes the connection pool and cleans up resources.

        Example:
            >>> client = RedisClient.get_instance()
            >>> client.disconnect()
        """
        try:
            if self._pool:
                self._pool.disconnect()
                logger.info("Redis connection pool disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")

    def reconnect(self) -> bool:
        """
        Reconnect to Redis (reinitialize pool).

        Returns:
            bool: True if reconnection successful, False otherwise.

        Example:
            >>> client = RedisClient.get_instance()
            >>> if not client.ping():
            ...     client.reconnect()
        """
        try:
            self.disconnect()
            self._initialize_pool()
            return self.ping()
        except Exception as e:
            logger.error(f"Redis reconnection failed: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# ==========================================
# Convenience Functions
# ==========================================

def get_redis_client(redis_url: Optional[str] = None) -> RedisClient:
    """
    Get Redis client instance (convenience function).

    Args:
        redis_url: Redis connection URL (optional).

    Returns:
        RedisClient: Redis client instance.

    Example:
        >>> from src.utils.redis_client import get_redis_client
        >>> client = get_redis_client()
        >>> if client.ping():
        ...     print("Connected to Redis")
    """
    return RedisClient.get_instance(redis_url)
