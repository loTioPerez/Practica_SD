"""Serialización común para mensajes, respuestas y resultados."""

from __future__ import annotations

import json
from typing import Any

from ..core.domain.models import PurchaseResult
from ..core.domain.enums import PurchaseStatus, TicketType


def purchase_result_to_dict(result: PurchaseResult) -> dict[str, Any]:
    """Serializa un PurchaseResult a diccionario."""
    d: dict[str, Any] = {
        "status": result.status.value,
        "request_id": result.request_id,
        "client_id": result.client_id,
        "reason": result.reason,
        "duplicate": result.duplicate,
    }
    if result.ticket_type is not None:
        d["ticket_type"] = result.ticket_type.value
    if result.seat_id is not None:
        d["seat_id"] = result.seat_id
    if result.remaining is not None:
        d["remaining"] = result.remaining
    return d


def purchase_result_to_json(result: PurchaseResult) -> str:
    """Serializa un PurchaseResult a JSON."""
    return json.dumps(purchase_result_to_dict(result))


def dict_to_purchase_result(data: dict[str, Any]) -> PurchaseResult:
    """Deserializa un diccionario a PurchaseResult."""
    return PurchaseResult(
        status=PurchaseStatus(data["status"]),
        request_id=data["request_id"],
        client_id=data["client_id"],
        reason=data.get("reason", "ok"),
        ticket_type=TicketType(data["ticket_type"]) if data.get("ticket_type") else None,
        seat_id=data.get("seat_id"),
        remaining=data.get("remaining"),
        duplicate=data.get("duplicate", False),
    )
