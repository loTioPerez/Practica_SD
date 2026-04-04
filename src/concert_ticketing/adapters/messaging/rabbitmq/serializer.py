"""Serializacion/deserializacion de mensajes RabbitMQ."""

from __future__ import annotations

import json
from typing import Any


def serialize_request(data: dict[str, Any]) -> bytes:
    """Serializa un dict de peticion de compra a bytes JSON."""
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def deserialize_request(body: bytes) -> dict[str, Any]:
    """Deserializa bytes JSON a un dict de peticion."""
    return json.loads(body.decode("utf-8"))


def serialize_result(data: dict[str, Any]) -> bytes:
    """Serializa un dict de resultado a bytes JSON."""
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def deserialize_result(body: bytes) -> dict[str, Any]:
    """Deserializa bytes JSON a un dict de resultado."""
    return json.loads(body.decode("utf-8"))
