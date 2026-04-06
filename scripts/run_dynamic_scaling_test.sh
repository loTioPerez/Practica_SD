#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BENCHMARK_FILE="${BENCHMARK_FILE:-${PROJECT_ROOT}/benchmarks/input/benchmark_unnumbered_20000.txt}"
BASE_URL="${INDIRECT_BASE_URL:-http://localhost:8080}"
INITIAL_WORKERS="${INITIAL_WORKERS:-2}"
TARGET_WORKERS="${TARGET_WORKERS:-4}"
SCALE_AFTER_SECONDS="${SCALE_AFTER_SECONDS:-20}"
CONCURRENCY="${BENCHMARK_CONCURRENCY:-50}"
TIMEOUT="${BENCHMARK_TIMEOUT:-60}"
OUTPUT_BASE="${PROJECT_ROOT}/benchmarks/outputs/dynamic_scaling/latest"

scale_workers() {
    if (( TARGET_WORKERS > INITIAL_WORKERS )); then
        bash "${SCRIPT_DIR}/scale_workers_up.sh" "$TARGET_WORKERS"
    elif (( TARGET_WORKERS < INITIAL_WORKERS )); then
        bash "${SCRIPT_DIR}/scale_workers_down.sh" "$TARGET_WORKERS"
    else
        log_info "El numero objetivo de workers coincide con el inicial. No se aplicara escalado."
    fi
}

write_metadata() {
    local output_dir="$1"
    local start_ts="$2"
    local scale_ts="$3"
    local end_ts="$4"
    local metadata_path="${output_dir}/dynamic_scaling_metadata.json"
    local metadata_path_py

    metadata_path_py=$(to_python_path "$metadata_path")

    python3 -c "import json; data = {
        'benchmark_file': r'${BENCHMARK_FILE}',
        'base_url': r'${BASE_URL}',
        'initial_workers': ${INITIAL_WORKERS},
        'target_workers': ${TARGET_WORKERS},
        'scale_after_seconds': ${SCALE_AFTER_SECONDS},
        'started_at': '${start_ts}',
        'scaled_at': '${scale_ts}',
        'finished_at': '${end_ts}',
    }; open(r'${metadata_path_py}', 'w', encoding='utf-8').write(json.dumps(data, indent=2, ensure_ascii=False))"
}

echo "============================================================"
echo "  TEST DE ESCALADO DINAMICO"
echo "============================================================"
log_info "Benchmark: $(basename "$BENCHMARK_FILE")"
log_info "Workers iniciales: ${INITIAL_WORKERS}"
log_info "Workers objetivo: ${TARGET_WORKERS}"
log_info "Escalado tras: ${SCALE_AFTER_SECONDS}s"
echo ""

bash "${SCRIPT_DIR}/stop_all.sh"
WORKER_COUNT="$INITIAL_WORKERS" bash "${SCRIPT_DIR}/start_all.sh"

if ! curl -sf "${BASE_URL}/health" >/dev/null 2>&1; then
    log_error "El gateway indirecto no esta disponible en ${BASE_URL}"
    exit 1
fi

rm -rf "$OUTPUT_BASE"
mkdir -p "$OUTPUT_BASE"

start_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
python3 -m concert_ticketing.apps.benchmark_runner.main \
    --benchmark "$BENCHMARK_FILE" \
    --base-url "$BASE_URL" \
    --concurrency "$CONCURRENCY" \
    --timeout "$TIMEOUT" \
    --output-dir "$OUTPUT_BASE" \
    > "${OUTPUT_BASE}/dynamic_scaling.log" 2>&1 &
BENCHMARK_PID=$!

log_info "Benchmark lanzado en background (PID ${BENCHMARK_PID})"
sleep "$SCALE_AFTER_SECONDS"

scale_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
scale_workers

wait "$BENCHMARK_PID"
end_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
write_metadata "$OUTPUT_BASE" "$start_ts" "$scale_ts" "$end_ts"

if bash "${SCRIPT_DIR}/verify_correctness.sh" "$OUTPUT_BASE"; then
    log_ok "Correctitud validada tras el escalado dinamico"
else
    log_warn "El benchmark termino, pero la verificacion de correctitud detecto incidencias"
fi

echo ""
log_ok "ESCALADO DINAMICO COMPLETADO"
log_info "Resultados en: ${OUTPUT_BASE}"
