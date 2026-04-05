#!/usr/bin/env bash
# =================================================================
# run_full_analysis.sh
# Pipeline completo: benchmarks + analisis + graficos + reporte.
# =================================================================
set -euo pipefail

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

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_BASE="${PROJECT_ROOT}/benchmarks/outputs"

echo "============================================================"
echo "  PIPELINE COMPLETO DE ANALISIS - ${TIMESTAMP}"
echo "============================================================"
echo ""

# Paso 1: Ejecutar benchmarks comparativos
log_info "PASO 1/5: Ejecutando benchmarks comparativos..."
if bash "${SCRIPT_DIR}/run_comparative_benchmarks.sh"; then
    log_ok "Benchmarks comparativos completados."
else
    log_error "Benchmarks comparativos fallaron. Continuando con datos existentes..."
fi

# Paso 2: Test de escalabilidad
echo ""
log_info "PASO 2/5: Ejecutando test de escalabilidad..."
if bash "${SCRIPT_DIR}/run_scalability_test.sh"; then
    log_ok "Test de escalabilidad completado."
else
    log_error "Test de escalabilidad fallo. Continuando..."
fi

# Paso 3: Test de contencion
echo ""
log_info "PASO 3/5: Ejecutando test de contencion..."
if bash "${SCRIPT_DIR}/run_contention_test.sh"; then
    log_ok "Test de contencion completado."
else
    log_error "Test de contencion fallo. Continuando..."
fi

# Paso 4: Analizar resultados y generar graficos
echo ""
log_info "PASO 4/5: Analizando resultados y generando graficos..."
bash "${SCRIPT_DIR}/generate_report.sh" "${OUTPUT_BASE}"

# Paso 5: Resumen final
echo ""
log_info "PASO 5/5: Resumen final"
echo ""
echo "============================================================"
log_ok "PIPELINE DE ANALISIS COMPLETADO"
echo ""
log_info "Estructura de resultados:"
echo "  ${OUTPUT_BASE}/"
echo "  ├── direct/         - Resultados directos"
echo "  ├── indirect/       - Resultados indirectos"
echo "  ├── comparative/    - Benchmarks comparativos"
echo "  ├── scalability/    - Tests de escalabilidad"
echo "  ├── contention/     - Tests de contencion"
echo "  ├── plots/          - Graficos generados"
echo "  └── reports/        - Reportes MD y HTML"
echo ""
log_info "Reporte HTML: ${OUTPUT_BASE}/reports/benchmark_report.html"
log_info "Reporte MD:   ${OUTPUT_BASE}/reports/benchmark_report.md"
echo "============================================================"
