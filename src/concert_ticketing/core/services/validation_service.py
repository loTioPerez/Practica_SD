"""Validaciones comunes sobre peticiones de compra y entradas benchmark."""

from __future__ import annotations

import re
from typing import Optional, Tuple

from ...shared.constants import MIN_SEAT_ID, MAX_SEAT_ID

# Patrón para líneas del benchmark
_UNNUMBERED_RE = re.compile(r"^BUY\s+(\S+)\s+(\S+)$")
_NUMBERED_RE = re.compile(r"^BUY\s+(\S+)\s+(\d+)\s+(\S+)$")


def parse_unnumbered_line(line: str) -> Optional[Tuple[str, str]]:
    """Parsea una línea de benchmark unnumbered.

    Retorna (client_id, request_id) o None si no coincide.
    """
    m = _UNNUMBERED_RE.match(line.strip())
    if m:
        return m.group(1), m.group(2)
    return None


def parse_numbered_line(line: str) -> Optional[Tuple[str, int, str]]:
    """Parsea una línea de benchmark numbered.

    Retorna (client_id, seat_id, request_id) o None si no coincide.
    """
    m = _NUMBERED_RE.match(line.strip())
    if m:
        return m.group(1), int(m.group(2)), m.group(3)
    return None


def validate_seat_id(seat_id: int) -> bool:
    """Valida que un seat_id esté dentro del rango válido."""
    return isinstance(seat_id, int) and MIN_SEAT_ID <= seat_id <= MAX_SEAT_ID


def validate_client_id(client_id: str) -> bool:
    """Valida que client_id no esté vacío."""
    return bool(client_id and isinstance(client_id, str) and client_id.strip())


def validate_request_id(request_id: str) -> bool:
    """Valida que request_id no esté vacío."""
    return bool(request_id and isinstance(request_id, str) and request_id.strip())