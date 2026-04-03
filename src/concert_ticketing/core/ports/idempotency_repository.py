"""Puerto para almacenar y consultar solicitudes ya procesadas."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class IdempotencyRepository(ABC):
    """Interface para el registro de idempotencia.

    NOTA: En la implementación actual con Lua, la idempotencia se maneja
    dentro del propio script atómico. Esta interface existe para
    extensibilidad futura y consultas de estado.
    """

    @abstractmethod
    def get_request_result(self, request_id: str) -> Optional[dict[str, Any]]:
        """Consulta el resultado almacenado de un request_id previo."""
        ...

    @abstractmethod
    def request_exists(self, request_id: str) -> bool:
        """Comprueba si un request_id ya fue procesado."""
        ...