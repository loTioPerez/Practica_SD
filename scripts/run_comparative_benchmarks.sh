#!/usr/bin/env bash
# =================================================================
# run_comparative_benchmarks.sh
# Script maestro de comparacion: ejecuta benchmarks en ambas
# arquitecturas con diferentes configuraciones de workers.
# =================================================================
set -euo pipefail

# ---- Configuracion ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# URLs base por defecto
DIRECT_BASE_URL="${DIRECT_BASE_URL:-http://localhost}"
INDIRECT_BASE_URL="${INDIRECT_BASE_URL:-http://localhost:8080}"

# Benchmarks de entrada
BENCHMARK_UNNUMBERED="${PROJECT_ROOT}/benchmarks/input/benchmark_unnumbered_20000.txt"
BENCHMARK_NUMBERED="${PROJECT_ROOT}/benchmarks/input/benchmark_numbered_60000.txt"

# Concurrencia
CONCURRENCY="${BENCHMARK_CONCURRENCY:-50}"
TIMEOUT="${BENCHMARK_TIMEOUT:-60}"

# Workers a probar
WORKERS=(${WORKERS_LIST:-"1 2 4 8"})

# Directorio de salida
OUTPUT_BASE="${PROJECT_ROOT}/benchmarks/outputs/comparative/${TIMESTAMP}"

# Colores para logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No color

# ---- Funciones ----
log_info()  { echo -e "${BLUE}[INFO]${NC}  $(date '+%H:%M:%S') $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $(date '+%H:%M:%S') $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $(date '+%H:%M:%S') $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $*"; }

run_benchmark() {
    local arch="$1"        # direct | indirect
    local benchmark="$2"   # ruta al fichero benchmark
    local workers="$3"     # numero de workers
    local output_dir="$4"  # directorio de salida

    local base_url
    if [ "$arch" = "direct" ]; then
        base_url="$DIRECT_BASE_URL"
    else
        base_url="$INDIRECT_BASE_URL"
    fi

    local bench_name
    bench_name=$(basename "$benchmark" .txt)

    log_info "  Ejecutando: arch=${arch} benchmark=${bench_name} workers=${workers}"
    log_info "  URL: ${base_url} | Concurrency: ${CONCURRENCY} | Timeout: ${TIMEOUT}s"

    mkdir -p "$output_dir"

    PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
    python3 -m concert_ticketing.apps.benchmark_runner.main \
        --benchmark "$benchmark" \
        --base-url "$base_url" \
        --concurrency "$CONCURRENCY" \
        --timeout "$TIMEOUT" \
        --output-dir "$output_dir" \
        2>&1 | tee "${output_dir}/${bench_name}_${arch}_w${workers}.log"

    log_ok "  Completado: ${bench_name} (${arch}, ${workers} workers)"
}

# ---- Main ----
echo "============================================================"
echo "  BENCHMARKS COMPARATIVOS - ${TIMESTAMP}"
echo "============================================================"
log_info "Directorio de salida: ${OUTPUT_BASE}"
log_info "Workers a probar: ${WORKERS[*]}"
log_info "Concurrencia: ${CONCURRENCY}"
log_info ""

mkdir -p "$OUTPUT_BASE"

# Guardar configuracion de la ejecucion
cat > "${OUTPUT_BASE}/config.json" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "direct_base_url": "${DIRECT_BASE_URL}",
    "indirect_base_url": "${INDIRECT_BASE_URL}",
    "concurrency": ${CONCURRENCY},
    "timeout": ${TIMEOUT},
    "workers": [$(IFS=,; echo "${WORKERS[*]}")],
    "benchmarks": ["unnumbered", "numbered"]
}
EOF

# Iterar por cada numero de workers
for num_workers in "${WORKERS[@]}"; do
    echo ""
    echo "------------------------------------------------------------"
    log_info "CONFIGURACION: ${num_workers} worker(s)"
    echo "------------------------------------------------------------"

    WORKER_DIR="${OUTPUT_BASE}/workers_${num_workers}"
    mkdir -p "${WORKER_DIR}/direct" "${WORKER_DIR}/indirect"

    # Direct - Unnumbered
    if [ -f "$BENCHMARK_UNNUMBERED" ]; then
        log_info "[Direct] Benchmark unnumbered con ${num_workers} workers"
        run_benchmark "direct" "$BENCHMARK_UNNUMBERED" "$num_workers" "${WORKER_DIR}/direct" || \
            log_warn "Benchmark direct unnumbered fallo (workers=${num_workers})"
    else
        log_warn "Fichero benchmark unnumbered no encontrado: $BENCHMARK_UNNUMBERED"
    fi

    # Direct - Numbered
    if [ -f "$BENCHMARK_NUMBERED" ]; then
        log_info "[Direct] Benchmark numbered con ${num_workers} workers"
        run_benchmark "direct" "$BENCHMARK_NUMBERED" "$num_workers" "${WORKER_DIR}/direct" || \
            log_warn "Benchmark direct numbered fallo (workers=${num_workers})"
    else
        log_warn "Fichero benchmark numbered no encontrado: $BENCHMARK_NUMBERED"
    fi

    # Indirect - Unnumbered
    if [ -f "$BENCHMARK_UNNUMBERED" ]; then
        log_info "[Indirect] Benchmark unnumbered con ${num_workers} workers"
        run_benchmark "indirect" "$BENCHMARK_UNNUMBERED" "$num_workers" "${WORKER_DIR}/indirect" || \
            log_warn "Benchmark indirect unnumbered fallo (workers=${num_workers})"
    else
        log_warn "Fichero benchmark unnumbered no encontrado: $BENCHMARK_UNNUMBERED"
    fi

    # Indirect - Numbered
    if [ -f "$BENCHMARK_NUMBERED" ]; then
        log_info "[Indirect] Benchmark numbered con ${num_workers} workers"
        run_benchmark "indirect" "$BENCHMARK_NUMBERED" "$num_workers" "${WORKER_DIR}/indirect" || \
            log_warn "Benchmark indirect numbered fallo (workers=${num_workers})"
    else
        log_warn "Fichero benchmark numbered no encontrado: $BENCHMARK_NUMBERED"
    fi

    log_ok "Workers ${num_workers} completado."
done

echo ""
echo "============================================================"
log_ok "BENCHMARKS COMPARATIVOS COMPLETADOS"
log_info "Resultados en: ${OUTPUT_BASE}"
log_info "Para generar reportes: ./scripts/generate_report.sh ${OUTPUT_BASE}"
echo "============================================================"
