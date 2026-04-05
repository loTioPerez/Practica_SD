#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCHMARK_FILE="${1:-$ROOT_DIR/benchmarks/input/benchmark_unnumbered_20000.txt}"
BASE_URL="${BASE_URL:-http://localhost:8080}"
CONCURRENCY="${CONCURRENCY:-50}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/benchmarks/outputs/indirect}"

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
python3 -m concert_ticketing.apps.benchmark_runner.main \
  --benchmark "$BENCHMARK_FILE" \
  --base-url "$BASE_URL" \
  --concurrency "$CONCURRENCY" \
  --output-dir "$OUTPUT_DIR"
