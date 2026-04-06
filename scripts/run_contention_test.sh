#!/usr/bin/env bash
# =================================================================
# run_contention_test.sh
# Test de contencion: compara rendimiento con distribucion
# uniforme vs alta contencion (hotspot).
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuracion
DIRECT_BASE_URL="${DIRECT_BASE_URL:-http://localhost}"
INDIRECT_BASE_URL="${INDIRECT_BASE_URL:-http://localhost:8080}"

# Benchmarks
NORMAL_BENCHMARK="${NORMAL_BENCHMARK:-${PROJECT_ROOT}/benchmarks/input/benchmark_numbered_60000.txt}"
HOTSPOT_BENCHMARK="${HOTSPOT_BENCHMARK:-${PROJECT_ROOT}/benchmarks/generated/hotspot_benchmark.txt}"

CONCURRENCY="${BENCHMARK_CONCURRENCY:-50}"
TIMEOUT="${BENCHMARK_TIMEOUT:-60}"
OUTPUT_BASE="${PROJECT_ROOT}/benchmarks/outputs/contention/latest"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $(date '+%H:%M:%S') $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $(date '+%H:%M:%S') $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $(date '+%H:%M:%S') $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $*"; }

run_benchmark() {
    local arch="$1"
    local benchmark="$2"
    local scenario="$3"  # normal | hotspot
    local output_dir="$4"

    local base_url
    [ "$arch" = "direct" ] && base_url="$DIRECT_BASE_URL" || base_url="$INDIRECT_BASE_URL"

    mkdir -p "$output_dir"

    PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
    python3 -m concert_ticketing.apps.benchmark_runner.main \
        --benchmark "$benchmark" \
        --base-url "$base_url" \
        --concurrency "$CONCURRENCY" \
        --timeout "$TIMEOUT" \
        --output-dir "$output_dir" \
        2>&1 | tee "${output_dir}/contention_${arch}_${scenario}.log"
}

restart_stack() {
    bash "${SCRIPT_DIR}/stop_all.sh"
    WORKER_COUNT="${WORKER_COUNT:-3}" bash "${SCRIPT_DIR}/start_all.sh"
}

echo "============================================================"
echo "  TEST DE CONTENCION"
echo "============================================================"
log_info "Benchmark normal: $(basename "$NORMAL_BENCHMARK")"
log_info "Benchmark hotspot: $(basename "$HOTSPOT_BENCHMARK")"
log_info "Concurrencia: ${CONCURRENCY}"
echo ""

if ! curl -sf "${DIRECT_BASE_URL}/health" >/dev/null 2>&1; then
    log_error "NGINX o el punto unico de entrada directo no esta disponible en ${DIRECT_BASE_URL}"
    log_error "Para la fase 5 se exige ejecutar la arquitectura directa a traves del balanceador."
    exit 1
fi

# Generar hotspot benchmark si no existe
if [ ! -f "$HOTSPOT_BENCHMARK" ]; then
    log_info "Generando benchmark hotspot..."
    HOTSPOT_DIR=$(dirname "$HOTSPOT_BENCHMARK")
    mkdir -p "$HOTSPOT_DIR"

    if [ -f "${PROJECT_ROOT}/benchmarks/generated/generate_hotspot.py" ]; then
        cd "$PROJECT_ROOT"
        PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
        python3 benchmarks/generated/generate_hotspot.py \
            --output "$HOTSPOT_BENCHMARK" \
            --total-ops 60000 \
            --hotspot-pct 80 \
            --hotspot-seats-pct 5 || {
            log_warn "No se pudo generar hotspot benchmark. Usando numbered como fallback."
            HOTSPOT_BENCHMARK="$NORMAL_BENCHMARK"
        }
    else
        log_warn "Script de generacion hotspot no encontrado. Usando numbered como fallback."
        HOTSPOT_BENCHMARK="$NORMAL_BENCHMARK"
    fi
fi

rm -rf "$OUTPUT_BASE"
mkdir -p "$OUTPUT_BASE"

# Escenario Normal
echo ""
log_info "=== ESCENARIO: DISTRIBUCION NORMAL ==="
for arch in direct indirect; do
    restart_stack
    if [[ "$arch" == "direct" ]] && ! curl -sf "${DIRECT_BASE_URL}/health" >/dev/null 2>&1; then
        log_error "Tras el rearranque no hay punto unico de entrada disponible en ${DIRECT_BASE_URL}"
        exit 1
    fi
    OUTPUT_DIR="${OUTPUT_BASE}/normal/${arch}"
    log_info "Ejecutando ${arch} con distribucion normal..."
    run_benchmark "$arch" "$NORMAL_BENCHMARK" "normal" "$OUTPUT_DIR" || \
        log_warn "${arch} normal benchmark fallo"
done

# Escenario Hotspot
echo ""
log_info "=== ESCENARIO: ALTA CONTENCION (HOTSPOT) ==="
for arch in direct indirect; do
    restart_stack
    if [[ "$arch" == "direct" ]] && ! curl -sf "${DIRECT_BASE_URL}/health" >/dev/null 2>&1; then
        log_error "Tras el rearranque no hay punto unico de entrada disponible en ${DIRECT_BASE_URL}"
        exit 1
    fi
    OUTPUT_DIR="${OUTPUT_BASE}/hotspot/${arch}"
    log_info "Ejecutando ${arch} con alta contencion..."
    run_benchmark "$arch" "$HOTSPOT_BENCHMARK" "hotspot" "$OUTPUT_DIR" || \
        log_warn "${arch} hotspot benchmark fallo"
done

# Resumen comparativo
echo ""
echo "============================================================"
log_ok "TEST DE CONTENCION COMPLETADO"
log_info "Resultados en: ${OUTPUT_BASE}"
echo ""

# Tabla resumen
log_info "--- Resumen comparativo ---"
for arch in direct indirect; do
    for scenario in normal hotspot; do
        SUMMARY=$(find "${OUTPUT_BASE}/${scenario}/${arch}" -name "*_summary.json" 2>/dev/null | head -1)
        if [ -n "$SUMMARY" ] && [ -f "$SUMMARY" ]; then
            SUMMARY_PY=$(to_python_path "$SUMMARY")
            TP=$(python3 -c "import json; d=json.load(open(r'$SUMMARY_PY', encoding='utf-8')); print(f\"{d.get('throughput_ops_per_second', 0):.1f}\")")
            LAT=$(python3 -c "import json; d=json.load(open(r'$SUMMARY_PY', encoding='utf-8')); print(f\"{d.get('average_latency_ms', 0):.1f}\")")
            echo -e "  ${arch}/${scenario}: TP=${TP} ops/s | Lat=${LAT}ms"
        else
            echo -e "  ${arch}/${scenario}: No data"
        fi
    done
done
echo "============================================================"
