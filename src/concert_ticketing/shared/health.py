"""Checks de salud y estructuras auxiliares para observabilidad básica."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import redis as redis_lib


@dataclass
class HealthStatus:
    """Estado de salud de un componente."""
    healthy: bool
    component: str
    detail: Optional[str] = None


def check_redis_health(host: str = "localhost", port: int = 6379, db: int = 0) -> HealthStatus:
    """Comprueba que Redis responde a PING."""
    try:
        r = redis_lib.Redis(host=host, port=port, db=db, socket_timeout=2)
        r.ping()
        return HealthStatus(healthy=True, component="redis")
    except Exception as exc:  # noqa: BLE001
        return HealthStatus(healthy=False, component="redis", detail=str(exc))
