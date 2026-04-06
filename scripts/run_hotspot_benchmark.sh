#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

DIRECT_BASE_URL="${DIRECT_BASE_URL:-http://localhost}"
INDIRECT_BASE_URL="${INDIRECT_BASE_URL:-http://localhost:8080}"
HOTSPOT_BENCHMARK="${HOTSPOT_BENCHMARK:-${PROJECT_ROOT}/benchmarks/generated/hotspot_benchmark.txt}"
OUTPUT_BASE="${PROJECT_ROOT}/benchmarks/outputs/hotspot/latest"
CONCURRENCY="${BENCHMARK_CONCURRENCY:-50}"
TIMEOUT="${BENCHMARK_TIMEOUT:-60}"
TOTAL_OPS="${HOTSPOT_TOTAL_OPS:-60000}"
HOTSPOT_PCT="${HOTSPOT_PCT:-80}"
HOTSPOT_SEATS_PCT="${HOTSPOT_SEATS_PCT:-5}"

run_single_benchmark() {
    local arch="$1"
    local output_dir="$2"
    local base_url="$INDIRECT_BASE_URL"

    if [[ "$arch" == "direct" ]]; then
        base_url="$DIRECT_BASE_URL"
    fi

    mkdir -p "$output_dir"

    PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
    python3 -m concert_ticketing.apps.benchmark_runner.main \
        --benchmark "$HOTSPOT_BENCHMARK" \
        --base-url "$base_url" \
        --concurrency "$CONCURRENCY" \
        --timeout "$TIMEOUT" \
        --output-dir "$output_dir" \
        2>&1 | tee "${output_dir}/hotspot_${arch}.log"
}

restart_stack() {
    local worker_count="${1:-3}"
    bash "${SCRIPT_DIR}/stop_all.sh"
    WORKER_COUNT="$worker_count" bash "${SCRIPT_DIR}/start_all.sh"
}

echo "============================================================"
echo "  HOTSPOT BENCHMARK"
echo "============================================================"
log_info "Benchmark hotspot: $(basename "$HOTSPOT_BENCHMARK")"
log_info "Concurrencia: ${CONCURRENCY}"
echo ""

if [[ ! -f "$HOTSPOT_BENCHMARK" ]]; then
    log_step "Generando benchmark hotspot..."
    mkdir -p "$(dirname "$HOTSPOT_BENCHMARK")"
    PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
    python3 "${PROJECT_ROOT}/benchmarks/generated/generate_hotspot.py" \
        --output "$HOTSPOT_BENCHMARK" \
        --total-ops "$TOTAL_OPS" \
        --hotspot-pct "$HOTSPOT_PCT" \
        --hotspot-seats-pct "$HOTSPOT_SEATS_PCT"
fi

if ! curl -sf "${DIRECT_BASE_URL}/health" >/dev/null 2>&1; then
    log_error "NGINX o el punto unico de entrada directo no esta disponible en ${DIRECT_BASE_URL}"
    exit 1
fi

rm -rf "$OUTPUT_BASE"
mkdir -p "$OUTPUT_BASE/direct" "$OUTPUT_BASE/indirect"

for arch in direct indirect; do
    echo ""
    log_info "Ejecutando escenario hotspot en arquitectura ${arch}..."
    restart_stack "${WORKER_COUNT:-3}"
    if [[ "$arch" == "direct" ]] && ! curl -sf "${DIRECT_BASE_URL}/health" >/dev/null 2>&1; then
        log_error "Tras el rearranque no hay punto unico de entrada disponible en ${DIRECT_BASE_URL}"
        exit 1
    fi
    run_single_benchmark "$arch" "${OUTPUT_BASE}/${arch}"
done

echo ""
log_ok "HOTSPOT COMPLETADO"
log_info "Resultados en: ${OUTPUT_BASE}"
