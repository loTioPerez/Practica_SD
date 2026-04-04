"""Coordinacion de exportacion de resultados y metricas de benchmark."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkRequestResult:
    """Resultado individual de una operacion benchmark."""

    line_number: int
    endpoint: str
    request_id: str
    client_id: str
    ticket_type: str
    seat_id: int | None
    http_status: int
    elapsed_ms: float
    response_body: dict[str, Any] | None = None
    error: str | None = None


def build_summary(
    results: list[BenchmarkRequestResult],
    total_seconds: float,
) -> dict[str, Any]:
    """Agrega metricas basicas para una ejecucion benchmark."""
    http_status_counter = Counter(result.http_status for result in results)
    reason_counter = Counter()
    accepted = 0
    rejected = 0
    duplicates = 0
    transport_errors = 0

    for result in results:
        if result.error is not None:
            transport_errors += 1
        body = result.response_body or {}
        reason = body.get("reason")
        if reason is not None:
            reason_counter[str(reason)] += 1
        if body.get("status") == "ACCEPTED":
            accepted += 1
        elif body.get("status") == "REJECTED":
            rejected += 1
        if body.get("duplicate") is True:
            duplicates += 1

    average_latency_ms = (
        sum(result.elapsed_ms for result in results) / len(results) if results else 0.0
    )

    return {
        "total_operations": len(results),
        "total_time_seconds": round(total_seconds, 4),
        "throughput_ops_per_second": round(
            len(results) / total_seconds if total_seconds > 0 else 0.0,
            4,
        ),
        "average_latency_ms": round(average_latency_ms, 4),
        "accepted": accepted,
        "rejected": rejected,
        "duplicates": duplicates,
        "transport_errors": transport_errors,
        "http_status_counts": dict(http_status_counter),
        "reason_counts": dict(reason_counter),
    }


def write_summary(path: str | Path, summary: dict[str, Any]) -> None:
    """Escribe el resumen agregado a un fichero JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_results(path: str | Path, results: list[BenchmarkRequestResult]) -> None:
    """Escribe todos los resultados individuales en JSON Lines."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(asdict(result), ensure_ascii=False)
        for result in results
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
