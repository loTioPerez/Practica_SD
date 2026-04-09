#!/usr/bin/env bash
# =================================================================
# run_full_analysis.sh
# Pipeline completo: benchmarks + analisis + graficos + reporte.
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $(date '+%H:%M:%S') $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $(date '+%H:%M:%S') $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $*"; }

OUTPUT_BASE="${PROJECT_ROOT}/benchmarks/outputs"
UNNUMBERED_BENCHMARK="${PROJECT_ROOT}/benchmarks/input/benchmark_unnumbered_20000.txt"
NUMBERED_BENCHMARK="${PROJECT_ROOT}/benchmarks/input/benchmark_numbered_60000.txt"

restart_stack() {
    local worker_count="${1:-3}"
    bash "${SCRIPT_DIR}/stop_all.sh"
    WORKER_COUNT="$worker_count" bash "${SCRIPT_DIR}/start_all.sh"
}

echo "============================================================"
echo "  PIPELINE COMPLETO DE ANALISIS"
echo "============================================================"
echo ""

# Paso 1: Ejecutar benchmarks base directo/indirecto
log_info "PASO 1/6: Ejecutando benchmarks base..."
mkdir -p "${OUTPUT_BASE}/direct" "${OUTPUT_BASE}/indirect"
rm -f "${OUTPUT_BASE}/direct"/*_summary.json "${OUTPUT_BASE}/direct"/*_results.jsonl
rm -f "${OUTPUT_BASE}/indirect"/*_summary.json "${OUTPUT_BASE}/indirect"/*_results.jsonl
rm -rf "${OUTPUT_BASE}/scalability/latest" "${OUTPUT_BASE}/contention/latest" "${OUTPUT_BASE}/plots" "${OUTPUT_BASE}/reports"

restart_stack 3
bash "${SCRIPT_DIR}/run_direct_benchmark.sh" "$UNNUMBERED_BENCHMARK"

restart_stack 3
bash "${SCRIPT_DIR}/run_direct_benchmark.sh" "$NUMBERED_BENCHMARK"

restart_stack 3
bash "${SCRIPT_DIR}/run_indirect_benchmark.sh" "$UNNUMBERED_BENCHMARK"

restart_stack 3
bash "${SCRIPT_DIR}/run_indirect_benchmark.sh" "$NUMBERED_BENCHMARK"

log_ok "Benchmarks base completados."

# Paso 2: Verificar correctitud
echo ""
log_info "PASO 2/6: Verificando correctitud..."
if bash "${SCRIPT_DIR}/verify_correctness.sh" "${OUTPUT_BASE}"; then
    log_ok "Correctitud verificada."
else
    log_error "La verificacion de correctitud detecto problemas."
fi

# Paso 3: Test de escalabilidad
echo ""
log_info "PASO 3/6: Ejecutando test de escalabilidad..."
if bash "${SCRIPT_DIR}/run_scalability_test.sh"; then
    log_ok "Test de escalabilidad completado."
else
    log_error "Test de escalabilidad fallo. Continuando..."
fi

# Paso 4: Test de contencion
echo ""
log_info "PASO 4/6: Ejecutando test de contencion..."
if bash "${SCRIPT_DIR}/run_contention_test.sh"; then
    log_ok "Test de contencion completado."
else
    log_error "Test de contencion fallo. Continuando..."
fi

# Paso 5: Analizar resultados y generar graficos
echo ""
log_info "PASO 5/6: Analizando resultados y generando graficos..."
bash "${SCRIPT_DIR}/generate_report.sh" "${OUTPUT_BASE}"

# Paso 6: Resumen final
echo ""
log_info "PASO 6/6: Resumen final"
echo ""
echo "============================================================"
log_ok "PIPELINE DE ANALISIS COMPLETADO"
echo ""
log_info "Estructura de resultados:"
echo "  ${OUTPUT_BASE}/"
echo "  - direct/        Resultados directos"
echo "  - indirect/      Resultados indirectos"
echo "  - scalability/   Tests de escalabilidad"
echo "  - contention/    Tests de contencion"
echo "  - plots/         Graficos generados"
echo "  - reports/       Reportes MD y HTML"
echo ""
log_info "Reporte HTML: ${OUTPUT_BASE}/reports/benchmark_report.html"
log_info "Reporte MD:   ${OUTPUT_BASE}/reports/benchmark_report.md"
echo "============================================================"
