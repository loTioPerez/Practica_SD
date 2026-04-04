"""Esquemas HTTP de peticion y respuesta para la API REST."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class UnnumberedPurchaseRequestSchema(BaseModel):
    """Body para compra de entradas no numeradas."""

    client_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)


class NumberedPurchaseRequestSchema(BaseModel):
    """Body para compra de entradas numeradas."""

    client_id: str = Field(..., min_length=1)
    seat_id: int
    request_id: str = Field(..., min_length=1)


class PurchaseResponseSchema(BaseModel):
    """Respuesta HTTP basada en PurchaseResult."""

    status: str
    request_id: str
    client_id: str
    reason: str
    ticket_type: Optional[str] = None
    seat_id: Optional[int] = None
    remaining: Optional[int] = None
    duplicate: bool = False


class HealthResponseSchema(BaseModel):
    """Estado de salud minimo del servicio."""

    status: str
    redis_healthy: bool
    redis_detail: Optional[str] = None


class RequestLookupResponseSchema(BaseModel):
    """Respuesta de consulta por request_id."""

    request_id: str
    found: bool
    result: Optional[dict[str, Any]] = None


class InventoryResponseSchema(BaseModel):
    """Entradas disponibles para un tipo de ticket."""

    ticket_type: str
    available: int


class SeatStatusResponseSchema(BaseModel):
    """Estado de un asiento numerado."""

    seat_id: int
    status: str
    owner: Optional[str] = None


class ClientPurchasesResponseSchema(BaseModel):
    """Historial de compras de un cliente."""

    client_id: str
    purchases: list[dict[str, Any]]


class StatsResponseSchema(BaseModel):
    """Estadisticas basicas del inventario actual."""

    unnumbered_available: int
    numbered_available: int
