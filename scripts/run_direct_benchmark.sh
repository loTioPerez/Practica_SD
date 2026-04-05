#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCHMARK_FILE="${1:-$ROOT_DIR/benchmarks/input/benchmark_unnumbered_20000.txt}"
if [[ -n "${BASE_URL:-}" ]]; then
  RESOLVED_BASE_URL="$BASE_URL"
elif curl -sf "http://localhost/health" >/dev/null 2>&1; then
  RESOLVED_BASE_URL="http://localhost"
else
  RESOLVED_BASE_URL="http://localhost:8000"
fi
CONCURRENCY="${CONCURRENCY:-50}"
TIMEOUT="${TIMEOUT:-60}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/benchmarks/outputs/direct}"

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
python3 -m concert_ticketing.apps.benchmark_runner.main \
  --benchmark "$BENCHMARK_FILE" \
  --base-url "$RESOLVED_BASE_URL" \
  --concurrency "$CONCURRENCY" \
  --timeout "$TIMEOUT" \
  --output-dir "$OUTPUT_DIR"
