#!/usr/bin/env python3
"""
Genera un benchmark de alta contenciÃ³n (hotspot) para asientos numerados.

El X% de las peticiones se concentra en el Y% de los asientos,
simulando un escenario realista donde ciertos asientos son mÃ¡s demandados.
"""

import argparse
import random
import sys
from pathlib import Path


def generate_hotspot_benchmark(
    output: str,
    total_ops: int = 60000,
    total_seats: int = 20000,
    hotspot_pct: int = 80,
    hotspot_seats_pct: int = 5,
    seed: int = 42,
) -> None:
    """Genera archivo de benchmark con distribuciÃ³n hotspot.

    Args:
        output: Ruta del archivo de salida.
        total_ops: NÃºmero total de operaciones a generar.
        total_seats: NÃºmero total de asientos disponibles.
        hotspot_pct: Porcentaje de operaciones dirigidas a asientos hotspot.
        hotspot_seats_pct: Porcentaje de asientos que son hotspot.
        seed: Semilla para reproducibilidad.
    """
    random.seed(seed)

    num_hotspot_seats = max(1, total_seats * hotspot_seats_pct // 100)
    num_cold_seats = total_seats - num_hotspot_seats

    # Los asientos hotspot son los primeros N asientos (1..num_hotspot_seats)
    hotspot_seats = list(range(1, num_hotspot_seats + 1))
    cold_seats = list(range(num_hotspot_seats + 1, total_seats + 1))

    num_hotspot_ops = total_ops * hotspot_pct // 100
    num_cold_ops = total_ops - num_hotspot_ops

    total_clients = max(500, total_ops // 10)

    lines = []
    lines.append("# Concert Ticket Benchmark â€“ Numbered Seats (HOTSPOT)")
    lines.append("# Format: BUY <client_id> <seat_id> <request_id>")
    lines.append(f"# Total operations: {total_ops}")
    lines.append(f"# Hotspot config: {hotspot_pct}% ops -> {hotspot_seats_pct}% seats ({num_hotspot_seats} seats)")
    lines.append(f"# Cold config: {100 - hotspot_pct}% ops -> {100 - hotspot_seats_pct}% seats ({num_cold_seats} seats)")
    lines.append("")

    ops = []
    # Generar operaciones hotspot
    for i in range(num_hotspot_ops):
        client_id = f"client_{random.randint(1, total_clients)}"
        seat_id = random.choice(hotspot_seats)
        request_id = f"req_hot_{i + 1:06d}"
        ops.append(f"BUY {client_id} {seat_id} {request_id}")

    # Generar operaciones cold
    for i in range(num_cold_ops):
        client_id = f"client_{random.randint(1, total_clients)}"
        seat_id = random.choice(cold_seats)
        request_id = f"req_cold_{i + 1:06d}"
        ops.append(f"BUY {client_id} {seat_id} {request_id}")

    # Mezclar para simular acceso concurrente real
    random.shuffle(ops)

    lines.extend(ops)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Hotspot benchmark generado: {output_path}")
    print(f"  Total operaciones: {total_ops}")
    print(f"  Asientos hotspot: {num_hotspot_seats} ({hotspot_seats_pct}%)")
    print(f"  Ops en hotspot: {num_hotspot_ops} ({hotspot_pct}%)")
    print(f"  Ops en cold: {num_cold_ops} ({100 - hotspot_pct}%)")


def main():
    parser = argparse.ArgumentParser(description="Genera benchmark hotspot de alta contenciÃ³n")
    parser.add_argument("--output", required=True, help="Archivo de salida")
    parser.add_argument("--total-ops", type=int, default=60000, help="Total de operaciones")
    parser.add_argument("--total-seats", type=int, default=20000, help="Total de asientos")
    parser.add_argument("--hotspot-pct", type=int, default=80, help="Porcentaje de ops en hotspot")
    parser.add_argument("--hotspot-seats-pct", type=int, default=5, help="Porcentaje de asientos hotspot")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")

    args = parser.parse_args()
    generate_hotspot_benchmark(
        output=args.output,
        total_ops=args.total_ops,
        total_seats=args.total_seats,
        hotspot_pct=args.hotspot_pct,
        hotspot_seats_pct=args.hotspot_seats_pct,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()

