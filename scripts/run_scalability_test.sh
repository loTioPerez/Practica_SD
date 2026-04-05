#!/usr/bin/env bash
# =================================================================
# run_scalability_test.sh
# Test de escalabilidad: mide throughput vs numero de workers.
# Genera datos especificos para graficos de escalabilidad.
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuracion
if [[ -n "${DIRECT_BASE_URL:-}" ]]; then
    DIRECT_BASE_URL="$DIRECT_BASE_URL"
elif curl -sf "http://localhost/health" >/dev/null 2>&1; then
    DIRECT_BASE_URL="http://localhost"
else
    DIRECT_BASE_URL="http://localhost:8000"
fi
INDIRECT_BASE_URL="${INDIRECT_BASE_URL:-http://localhost:8080}"
BENCHMARK_FILE="${BENCHMARK_FILE:-${PROJECT_ROOT}/benchmarks/input/benchmark_unnumbered_20000.txt}"
CONCURRENCY="${BENCHMARK_CONCURRENCY:-50}"
TIMEOUT="${BENCHMARK_TIMEOUT:-60}"
read -r -a WORKERS <<< "${WORKERS_LIST:-1 2 4 8}"
OUTPUT_BASE="${PROJECT_ROOT}/benchmarks/outputs/scalability/latest"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $(date '+%H:%M:%S') $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $(date '+%H:%M:%S') $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $(date '+%H:%M:%S') $*"; }

run_single_benchmark() {
    local arch="$1"
    local workers="$2"
    local output_dir="$3"

    local base_url
    [ "$arch" = "direct" ] && base_url="$DIRECT_BASE_URL" || base_url="$INDIRECT_BASE_URL"

    mkdir -p "$output_dir"

    PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
    python3 -m concert_ticketing.apps.benchmark_runner.main \
        --benchmark "$BENCHMARK_FILE" \
        --base-url "$base_url" \
        --concurrency "$CONCURRENCY" \
        --timeout "$TIMEOUT" \
        --output-dir "$output_dir" \
        2>&1 | tee "${output_dir}/scalability_${arch}_w${workers}.log"
}

restart_stack() {
    local worker_count="$1"
    bash "${SCRIPT_DIR}/stop_all.sh"
    WORKER_COUNT="$worker_count" bash "${SCRIPT_DIR}/start_all.sh"
}

echo "============================================================"
echo "  TEST DE ESCALABILIDAD"
echo "============================================================"
log_info "Benchmark: $(basename "$BENCHMARK_FILE")"
log_info "Workers: ${WORKERS[*]}"
log_info "Concurrencia: ${CONCURRENCY}"
echo ""

# Fichero de datos para graficos
SCALABILITY_CSV="${OUTPUT_BASE}/scalability_data.csv"
rm -rf "$OUTPUT_BASE"
mkdir -p "$OUTPUT_BASE"
echo "workers,architecture,throughput_ops_s,latency_mean_ms,total_time_s" > "$SCALABILITY_CSV"

for num_workers in "${WORKERS[@]}"; do
    echo ""
    log_info "=== Testing with ${num_workers} worker(s) ==="

    for arch in direct indirect; do
        restart_stack "$num_workers"
        WORKER_DIR="${OUTPUT_BASE}/workers_${num_workers}/${arch}"
        log_info "Running ${arch} benchmark with ${num_workers} workers..."

        if run_single_benchmark "$arch" "$num_workers" "$WORKER_DIR"; then
            # Extraer metricas del summary
            SUMMARY_FILE=$(find "$WORKER_DIR" -name "*_summary.json" | head -1)
            if [ -n "$SUMMARY_FILE" ] && [ -f "$SUMMARY_FILE" ]; then
                SUMMARY_FILE_PY=$(to_python_path "$SUMMARY_FILE")
                TP=$(python3 -c "import json; d=json.load(open(r'$SUMMARY_FILE_PY', encoding='utf-8')); print(d.get('throughput_ops_per_second', 0))")
                LAT=$(python3 -c "import json; d=json.load(open(r'$SUMMARY_FILE_PY', encoding='utf-8')); print(d.get('average_latency_ms', 0))")
                TIME=$(python3 -c "import json; d=json.load(open(r'$SUMMARY_FILE_PY', encoding='utf-8')); print(d.get('total_time_seconds', 0))")
                echo "${num_workers},${arch},${TP},${LAT},${TIME}" >> "$SCALABILITY_CSV"
                log_ok "${arch}: TP=${TP} ops/s, Lat=${LAT}ms, Time=${TIME}s"
            fi
        else
            log_warn "${arch} benchmark failed with ${num_workers} workers"
            echo "${num_workers},${arch},0,0,0" >> "$SCALABILITY_CSV"
        fi
    done
done

restart_stack 3

echo ""
echo "============================================================"
log_ok "TEST DE ESCALABILIDAD COMPLETADO"
log_info "Datos CSV: ${SCALABILITY_CSV}"
log_info "Resultados: ${OUTPUT_BASE}"
echo "============================================================"

# Mostrar tabla resumen
echo ""
echo "--- Resumen de escalabilidad ---"
column -t -s',' "$SCALABILITY_CSV" 2>/dev/null || cat "$SCALABILITY_CSV"
