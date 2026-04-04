"""Dependencias y wiring de servicios para la capa HTTP."""

from __future__ import annotations

from functools import lru_cache

from ....core.services.purchase_service import PurchaseService
from ....shared.config import AppConfig


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    """Carga la configuracion general del servicio."""
    return AppConfig.from_env()


@lru_cache(maxsize=1)
def get_redis_client():
    """Construye el cliente Redis compartido por la API."""
    from ...persistence.redis.connection import create_redis_client

    config = get_app_config()
    return create_redis_client(config.redis)


@lru_cache(maxsize=1)
def get_inventory_repository():
    """Instancia el repositorio de inventario sobre Redis."""
    from ...persistence.redis.repositories import RedisInventoryRepository

    return RedisInventoryRepository(get_redis_client())


@lru_cache(maxsize=1)
def get_idempotency_repository():
    """Instancia el repositorio de idempotencia sobre Redis."""
    from ...persistence.redis.repositories import RedisIdempotencyRepository

    return RedisIdempotencyRepository(get_redis_client())


@lru_cache(maxsize=1)
def get_result_repository():
    """Instancia el repositorio de historial de compras sobre Redis."""
    from ...persistence.redis.repositories import RedisResultRepository

    return RedisResultRepository(get_redis_client())


@lru_cache(maxsize=1)
def get_purchase_service() -> PurchaseService:
    """Construye el servicio principal usado por las rutas REST."""
    return PurchaseService(
        inventory=get_inventory_repository(),
        idempotency=get_idempotency_repository(),
        results=get_result_repository(),
    )
