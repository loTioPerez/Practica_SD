"""Punto de entrada para lanzadores de benchmark compartidos.

Su responsabilidad es reproducir cargas y recoger resultados, no actuar como
servicio de entrada de la arquitectura indirecta.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
from pathlib import Path

import httpx

from .parser import BenchmarkOperation, parse_benchmark_file
from .reporting import BenchmarkRequestResult, build_summary, write_results, write_summary


def parse_args() -> argparse.Namespace:
    """Parsea argumentos del benchmark runner."""
    parser = argparse.ArgumentParser(description="Benchmark runner para la arquitectura directa.")
    parser.add_argument(
        "--benchmark",
        required=True,
        help="Ruta al fichero benchmark a ejecutar.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BENCHMARK_BASE_URL", "http://localhost"),
        help="URL base del punto de entrada REST o NGINX.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=int(os.getenv("BENCHMARK_CONCURRENCY", "50")),
        help="Numero maximo de peticiones concurrentes.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("BENCHMARK_TIMEOUT_SECONDS", "60")),
        help="Timeout por peticion en segundos.",
    )
    parser.add_argument(
        "--output-dir",
        default="benchmarks/outputs/direct",
        help="Directorio donde guardar resultados y resumen.",
    )
    return parser.parse_args()


async def run_operation(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    operation: BenchmarkOperation,
) -> BenchmarkRequestResult:
    """Ejecuta una operacion individual del benchmark."""
    async with semaphore:
        start = time.perf_counter()
        try:
            response = await client.post(operation.endpoint, json=operation.to_payload())
            elapsed_ms = (time.perf_counter() - start) * 1000
            try:
                body = response.json()
            except ValueError:
                body = {"raw_text": response.text}
            return BenchmarkRequestResult(
                line_number=operation.line_number,
                endpoint=operation.endpoint,
                request_id=operation.request_id,
                client_id=operation.client_id,
                ticket_type=operation.ticket_type.value,
                seat_id=operation.seat_id,
                http_status=response.status_code,
                elapsed_ms=elapsed_ms,
                response_body=body,
            )
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.perf_counter() - start) * 1000
            return BenchmarkRequestResult(
                line_number=operation.line_number,
                endpoint=operation.endpoint,
                request_id=operation.request_id,
                client_id=operation.client_id,
                ticket_type=operation.ticket_type.value,
                seat_id=operation.seat_id,
                http_status=0,
                elapsed_ms=elapsed_ms,
                error=str(exc),
            )


async def run_benchmark(
    operations: list[BenchmarkOperation],
    base_url: str,
    concurrency: int,
    timeout: float,
) -> list[BenchmarkRequestResult]:
    """Lanza el benchmark concurrente contra la arquitectura directa."""
    semaphore = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(
        max_keepalive_connections=concurrency,
        max_connections=concurrency,
    )
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        limits=limits,
    ) as client:
        tasks = [
            run_operation(client, semaphore, operation)
            for operation in operations
        ]
        return await asyncio.gather(*tasks)


def print_summary(summary: dict[str, object]) -> None:
    """Imprime un resumen corto por consola."""
    print("=== Resumen benchmark directo ===")
    print(f"Operaciones totales: {summary['total_operations']}")
    print(f"Tiempo total (s): {summary['total_time_seconds']}")
    print(f"Throughput (ops/s): {summary['throughput_ops_per_second']}")
    print(f"Latencia media (ms): {summary['average_latency_ms']}")
    print(f"Aceptadas: {summary['accepted']}")
    print(f"Rechazadas: {summary['rejected']}")
    print(f"Duplicadas: {summary['duplicates']}")
    print(f"Errores de transporte: {summary['transport_errors']}")


def main() -> None:
    """Punto de entrada CLI para benchmark directo."""
    args = parse_args()
    operations = parse_benchmark_file(args.benchmark)

    start = time.perf_counter()
    results = asyncio.run(
        run_benchmark(
            operations=operations,
            base_url=args.base_url,
            concurrency=args.concurrency,
            timeout=args.timeout,
        )
    )
    total_seconds = time.perf_counter() - start

    summary = build_summary(results, total_seconds)
    output_dir = Path(args.output_dir)
    benchmark_name = Path(args.benchmark).stem

    write_summary(output_dir / f"{benchmark_name}_summary.json", summary)
    write_results(output_dir / f"{benchmark_name}_results.jsonl", results)
    print_summary(summary)


if __name__ == "__main__":
    main()
