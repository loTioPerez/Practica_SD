"""Punto central para la carga de configuración desde entorno y YAML."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from . import constants


@dataclass
class RedisConfig:
    """Configuración de conexión a Redis."""
    host: str = constants.REDIS_HOST
    port: int = constants.REDIS_PORT
    db: int = constants.REDIS_DB
    decode_responses: bool = constants.REDIS_DECODE_RESPONSES
    password: str | None = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True

    @classmethod
    def from_env(cls) -> RedisConfig:
        """Carga la configuración Redis desde variables de entorno."""
        return cls(
            host=os.getenv("REDIS_HOST", constants.REDIS_HOST),
            port=int(os.getenv("REDIS_PORT", str(constants.REDIS_PORT))),
            db=int(os.getenv("REDIS_DB", str(constants.REDIS_DB))),
            password=os.getenv("REDIS_PASSWORD"),
        )


@dataclass
class AppConfig:
    """Configuración global de la aplicación."""
    total_tickets: int = constants.TOTAL_TICKETS
    redis: RedisConfig = field(default_factory=RedisConfig)
    log_level: str = "INFO"
    ticket_type: str = "unnumbered"  # 'unnumbered' o 'numbered'

    @classmethod
    def from_env(cls) -> AppConfig:
        """Carga toda la configuración desde variables de entorno."""
        return cls(
            total_tickets=int(os.getenv("TOTAL_TICKETS", str(constants.TOTAL_TICKETS))),
            redis=RedisConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            ticket_type=os.getenv("TICKET_TYPE", "unnumbered"),
        )
