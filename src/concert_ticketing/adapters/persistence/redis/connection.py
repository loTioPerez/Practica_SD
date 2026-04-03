"""Conexión Redis y factorías de cliente compartidas."""

from __future__ import annotations

import redis as redis_lib

from ....shared.config import RedisConfig
from ....shared.logger import get_logger
from ....shared.exceptions import RedisConnectionError

logger = get_logger(__name__)


def create_redis_client(config: RedisConfig | None = None) -> redis_lib.Redis:
    """Crea y valida una conexión a Redis.

    Args:
        config: Configuración Redis.  Si es None usa valores por defecto.

    Returns:
        Cliente Redis conectado.

    Raises:
        RedisConnectionError: Si Redis no responde al PING.
    """
    if config is None:
        config = RedisConfig()

    try:
        client = redis_lib.Redis(
            host=config.host,
            port=config.port,
            db=config.db,
            password=config.password,
            decode_responses=config.decode_responses,
            socket_timeout=config.socket_timeout,
            socket_connect_timeout=config.socket_connect_timeout,
            retry_on_timeout=config.retry_on_timeout,
        )
        client.ping()
        logger.info("Conectado a Redis en %s:%d/%d", config.host, config.port, config.db)
        return client
    except redis_lib.ConnectionError as exc:
        raise RedisConnectionError(f"No se pudo conectar a Redis: {exc}") from exc
