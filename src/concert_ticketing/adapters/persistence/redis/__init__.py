"""Persistencia basada en Redis como backend principal del proyecto.

Implementación 100% Python usando WATCH/MULTI/EXEC (optimistic locking).
"""

from .connection import create_redis_client
from .key_schema import KeySchema
from .repositories import (
    RedisInventoryRepository,
    RedisIdempotencyRepository,
    RedisResultRepository,
)

__all__ = [
    "create_redis_client",
    "KeySchema",
    "RedisInventoryRepository",
    "RedisIdempotencyRepository",
    "RedisResultRepository",
]
