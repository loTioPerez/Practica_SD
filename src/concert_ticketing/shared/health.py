"""Utilidades de health check para servicios externos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import redis as redis_lib


@dataclass(frozen=True)
class HealthStatus:
    """Resultado de un health-check."""

    healthy: bool
    detail: Optional[str] = None


def check_redis_health(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
) -> HealthStatus:
    """Comprueba si Redis responde a PING."""
    try:
        client = redis_lib.Redis(host=host, port=port, db=db, socket_timeout=2)
        client.ping()
        return HealthStatus(healthy=True, detail="redis ok")
    except Exception as exc:  # noqa: BLE001
        return HealthStatus(healthy=False, detail=str(exc))


def check_rabbitmq_health(
    host: str = "localhost",
    port: int = 5672,
    user: str = "guest",
    password: str = "guest",
    vhost: str = "/",
) -> HealthStatus:
    """Comprueba si RabbitMQ acepta conexiones."""
    try:
        import pika

        credentials = pika.PlainCredentials(user, password)
        params = pika.ConnectionParameters(
            host=host, port=port, virtual_host=vhost, credentials=credentials,
            connection_attempts=1, socket_timeout=2,
        )
        connection = pika.BlockingConnection(params)
        connection.close()
        return HealthStatus(healthy=True, detail="rabbitmq ok")
    except Exception as exc:  # noqa: BLE001
        return HealthStatus(healthy=False, detail=str(exc))
