"""Funciones de validacion y parseo de entradas del sistema."""

from __future__ import annotations

import re
from typing import Optional, Tuple

from ...shared.constants import TOTAL_TICKETS

_UNNUMBERED_RE = re.compile(r"^BUY\s+(\S+)\s+(\S+)$")
_NUMBERED_RE = re.compile(r"^BUY\s+(\S+)\s+(\d+)\s+(\S+)$")


def validate_client_id(client_id: str) -> bool:
    """Devuelve True si el client_id es valido."""
    return isinstance(client_id, str) and len(client_id.strip()) > 0


def validate_request_id(request_id: str) -> bool:
    """Devuelve True si el request_id es valido."""
    return isinstance(request_id, str) and len(request_id.strip()) > 0


def validate_seat_id(seat_id: int) -> bool:
    """Devuelve True si el seat_id es valido (entre 1 y TOTAL_TICKETS)."""
    return isinstance(seat_id, int) and 1 <= seat_id <= TOTAL_TICKETS


def parse_unnumbered_line(line: str) -> Optional[Tuple[str, str]]:
    """Parsea una linea de benchmark no numerado.

    Formato: BUY <client_id> <request_id>
    Devuelve (client_id, request_id) o None.
    """
    match = _UNNUMBERED_RE.match(line.strip())
    if match is None:
        return None
    client_id, request_id = match.group(1), match.group(2)
    return (client_id, request_id)


def parse_numbered_line(line: str) -> Optional[Tuple[str, int, str]]:
    """Parsea una linea de benchmark numerado.

    Formato: BUY <client_id> <seat_id> <request_id>
    Devuelve (client_id, seat_id, request_id) o None.
    """
    match = _NUMBERED_RE.match(line.strip())
    if match is None:
        return None
    client_id = match.group(1)
    seat_id = int(match.group(2))
    request_id = match.group(3)
    return (client_id, seat_id, request_id)
