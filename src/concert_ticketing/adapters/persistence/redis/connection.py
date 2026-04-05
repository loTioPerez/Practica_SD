"""Creacion del cliente Redis reutilizable."""

from __future__ import annotations

from typing import Optional

import redis

from ....shared.config import AppConfig, RedisConfig
from ....shared.logger import get_logger

logger = get_logger(__name__)


def create_redis_client(config: Optional[RedisConfig] = None) -> redis.Redis:
    """Crea y devuelve un cliente Redis configurado."""
    if config is None:
        config = AppConfig.from_env().redis
    client = redis.Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        decode_responses=config.decode_responses,
        socket_timeout=config.socket_timeout,
        socket_connect_timeout=config.socket_connect_timeout,
        retry_on_timeout=config.retry_on_timeout,
    )
    logger.info("Cliente Redis creado -> %s:%s/%s", config.host, config.port, config.db)
    return client
