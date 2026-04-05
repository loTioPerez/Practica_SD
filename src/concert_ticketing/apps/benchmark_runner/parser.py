"""Parser compartido de ficheros benchmark y cargas derivadas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...core.domain.enums import TicketType
from ...core.services.validation_service import (
    parse_numbered_line,
    parse_unnumbered_line,
)


@dataclass(frozen=True)
class BenchmarkOperation:
    """Operacion individual leida desde un fichero benchmark."""

    line_number: int
    ticket_type: TicketType
    client_id: str
    request_id: str
    seat_id: int | None = None

    @property
    def endpoint(self) -> str:
        if self.ticket_type == TicketType.UNNUMBERED:
            return "/buy/unnumbered"
        return "/buy/numbered"

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "client_id": self.client_id,
            "request_id": self.request_id,
        }
        if self.seat_id is not None:
            payload["seat_id"] = self.seat_id
        return payload


def parse_benchmark_file(path: str | Path) -> list[BenchmarkOperation]:
    """Parsea un fichero benchmark en una lista de operaciones."""
    benchmark_path = Path(path)
    operations: list[BenchmarkOperation] = []

    with benchmark_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue

            # Ignorar líneas de comentario
            if line.startswith("#"):
                continue

            numbered = parse_numbered_line(line)
            if numbered is not None:
                client_id, seat_id, request_id = numbered
                operations.append(
                    BenchmarkOperation(
                        line_number=line_number,
                        ticket_type=TicketType.NUMBERED,
                        client_id=client_id,
                        request_id=request_id,
                        seat_id=seat_id,
                    )
                )
                continue

            unnumbered = parse_unnumbered_line(line)
            if unnumbered is not None:
                client_id, request_id = unnumbered
                operations.append(
                    BenchmarkOperation(
                        line_number=line_number,
                        ticket_type=TicketType.UNNUMBERED,
                        client_id=client_id,
                        request_id=request_id,
                    )
                )
                continue

            raise ValueError(
                f"Linea de benchmark invalida en {benchmark_path}:{line_number}: {line}"
            )

    return operations
