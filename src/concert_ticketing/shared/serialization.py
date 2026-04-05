"""Utilidades de serializacion entre modelos de dominio y dicts."""

from __future__ import annotations

import json
from typing import Any

from ..core.domain.models import PurchaseResult


def purchase_result_to_dict(result: PurchaseResult) -> dict[str, Any]:
    """Convierte un PurchaseResult a diccionario serializable."""
    data: dict[str, Any] = {
        "status": result.status.value if hasattr(result.status, "value") else str(result.status),
        "request_id": result.request_id,
        "client_id": result.client_id,
        "reason": result.reason,
        "duplicate": result.duplicate,
    }
    if result.ticket_type is not None:
        data["ticket_type"] = result.ticket_type
    if result.seat_id is not None:
        data["seat_id"] = result.seat_id
    if result.remaining is not None:
        data["remaining"] = result.remaining
    return data


def to_json(obj: Any) -> str:
    """Serializa un objeto a cadena JSON."""
    return json.dumps(obj, ensure_ascii=False, default=str)


def from_json(raw: str) -> Any:
    """Deserializa una cadena JSON."""
    return json.loads(raw)
