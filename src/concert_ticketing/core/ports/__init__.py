"""Puertos que aislan el nucleo del detalle de infraestructura."""

from .idempotency_repository import IdempotencyRepository
from .inventory_repository import InventoryRepository
from .result_repository import ResultRepository

__all__ = [
    "IdempotencyRepository",
    "InventoryRepository",
    "ResultRepository",
]