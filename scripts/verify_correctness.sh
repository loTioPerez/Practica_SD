#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET_DIR="${1:-${PROJECT_ROOT}/benchmarks/outputs}"

echo "============================================================"
echo "  VERIFICACION DE CORRECTITUD"
echo "============================================================"
echo "Analizando: ${TARGET_DIR}"
echo ""

PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
python3 - "$TARGET_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


base = Path(sys.argv[1])
summary_files = sorted(base.rglob("*_summary.json"))

if not summary_files:
    print("No se encontraron ficheros *_summary.json")
    sys.exit(1)

failures: list[str] = []

for summary_path in summary_files:
    results_path = summary_path.with_name(summary_path.name.replace("_summary.json", "_results.jsonl"))
    summary = load_json(summary_path)
    results = load_jsonl(results_path) if results_path.exists() else []
    name = summary_path.stem.replace("_summary", "")

    print(f"[CHECK] {summary_path.relative_to(base)}")

    transport_errors = summary.get("transport_errors", 0)
    if transport_errors != 0:
        failures.append(f"{name}: hay errores de transporte ({transport_errors})")

    ticket_types = {str(row.get("ticket_type", "")).lower() for row in results}
    is_unnumbered = "unnumbered" in name or "unnumbered" in ticket_types
    is_numbered_like = (
        ("numbered" in name and "unnumbered" not in name)
        or "hotspot" in name
        or "numbered" in ticket_types
    )

    if is_unnumbered:
        accepted = summary.get("accepted", 0)
        total = summary.get("total_operations", 0)
        expected = min(total, 20000)
        print(f"  - accepted={accepted}, total={total}, expected={expected}")
        if accepted != expected:
            failures.append(f"{name}: aceptadas={accepted}, esperado={expected}")

    if is_numbered_like:
        accepted_seats = []
        for row in results:
            body = row.get("response_body") or {}
            if body.get("status") == "ACCEPTED" and not body.get("duplicate", False):
                seat_id = row.get("seat_id")
                if seat_id is not None:
                    accepted_seats.append(seat_id)
        unique_seats = len(set(accepted_seats))
        print(
            "  - accepted_rows="
            f"{len(accepted_seats)}, accepted_unique_seats={unique_seats}"
        )
        if unique_seats != len(accepted_seats):
            failures.append(f"{name}: se detectaron asientos vendidos mas de una vez")

if failures:
    print("")
    print("FALLOS DE CORRECTITUD:")
    for failure in failures:
        print(f" - {failure}")
    sys.exit(1)

print("")
print("Correctitud verificada sin fallos.")
PY
