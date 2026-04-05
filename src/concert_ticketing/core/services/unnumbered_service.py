"""Logica de negocio para compra de entradas no numeradas."""

from __future__ import annotations

from ..domain.models import PurchaseResult
from ..ports.inventory_repository import InventoryRepository


class UnnumberedService:
    """Delega la compra no numerada al repositorio de inventario."""

    def __init__(self, inventory: InventoryRepository) -> None:
        self._inventory = inventory

    def buy(self, client_id: str, request_id: str) -> PurchaseResult:
        """Ejecuta la compra de una entrada no numerada."""
        return self._inventory.buy_unnumbered(client_id, request_id)
