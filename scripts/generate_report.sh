#!/usr/bin/env bash
# =================================================================
# generate_report.sh
# Genera graficos y reportes a partir de resultados de benchmarks.
# =================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Directorio base de outputs (puede pasarse como argumento)
OUTPUT_BASE="${1:-${PROJECT_ROOT}/benchmarks/outputs}"
PLOTS_DIR="${OUTPUT_BASE}/plots"
REPORTS_DIR="${OUTPUT_BASE}/reports"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $(date '+%H:%M:%S') $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $(date '+%H:%M:%S') $*"; }

echo "============================================================"
echo "  GENERACION DE REPORTES Y GRAFICOS"
echo "============================================================"
log_info "Directorio base: ${OUTPUT_BASE}"
log_info "Plots: ${PLOTS_DIR}"
log_info "Reports: ${REPORTS_DIR}"
echo ""

# Crear directorios
mkdir -p "$PLOTS_DIR" "$REPORTS_DIR"

# Ejecutar script de analisis
log_info "Ejecutando analisis y generacion de reportes..."

PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}/src')

from concert_ticketing.apps.analysis.analyzer import BenchmarkAnalyzer
from concert_ticketing.apps.analysis.plotter import BenchmarkPlotter
from concert_ticketing.apps.analysis.reporter import BenchmarkReporter
from concert_ticketing.apps.analysis.utils import extract_latencies, load_all_results

print('=== Cargando resultados...')
analyzer = BenchmarkAnalyzer('${OUTPUT_BASE}')
analyzer.load_results()

print(f'  Direct summaries: {len(analyzer.direct.summaries)}')
print(f'  Direct results: {len(analyzer.direct.results)}')
print(f'  Indirect summaries: {len(analyzer.indirect.summaries)}')
print(f'  Indirect results: {len(analyzer.indirect.results)}')

print('\n=== Comparando arquitecturas...')
comparison = analyzer.compare_architectures()
print(f'  Benchmarks comparados: {len(comparison)}')

print('\n=== Calculando tabla resumen...')
summary_table = analyzer.get_summary_table()
print(f'  Filas en tabla: {len(summary_table)}')

print('\n=== Analizando escalabilidad...')
scalability = analyzer.analyze_scalability()
has_scalability = any(bool(v) for v in scalability.values())
print(f'  Datos de escalabilidad: {\"si\" if has_scalability else \"no\"}')

print('\n=== Analizando contencion...')
contention = analyzer.analyze_contention()
has_contention = any(
    bool(v.get('normal', {}).get('total_operations', 0))
    for v in contention.values()
)
print(f'  Datos de contencion: {\"si\" if has_contention else \"no\"}')

print('\n=== Generando graficos...')
plotter = BenchmarkPlotter('${PLOTS_DIR}')

# Extraer latencias
direct_latencies = []
indirect_latencies = []
for results in analyzer.direct.results.values():
    direct_latencies.extend(extract_latencies(results))
for results in analyzer.indirect.results.values():
    indirect_latencies.extend(extract_latencies(results))

plots = plotter.save_all_plots(
    comparison=comparison,
    scalability_data=scalability if has_scalability else None,
    contention_data=contention if has_contention else None,
    direct_latencies=direct_latencies if direct_latencies else None,
    indirect_latencies=indirect_latencies if indirect_latencies else None,
)
print(f'  Graficos generados: {len(plots)}')
for p in plots:
    print(f'    - {p}')

print('\n=== Generando reportes...')
reporter = BenchmarkReporter('${REPORTS_DIR}', '${PLOTS_DIR}')

md_path = reporter.generate_markdown_report(
    comparison=comparison,
    scalability=scalability if has_scalability else None,
    contention=contention if has_contention else None,
    summary_table=summary_table,
    generated_plots=[str(p) for p in plots],
)
print(f'  Markdown: {md_path}')

html_path = reporter.generate_html_report(
    comparison=comparison,
    scalability=scalability if has_scalability else None,
    contention=contention if has_contention else None,
    summary_table=summary_table,
    generated_plots=[str(p) for p in plots],
)
print(f'  HTML: {html_path}')

table_path = reporter.generate_summary_table(summary_table)
print(f'  Summary table: {table_path}')

print('\n=== REPORTE COMPLETADO ===')
"

log_ok "Analisis completado."
log_info "Plots en: ${PLOTS_DIR}"
log_info "Reportes en: ${REPORTS_DIR}"

# Intentar abrir reporte HTML
if command -v xdg-open &>/dev/null; then
    log_info "Abriendo reporte HTML..."
    xdg-open "${REPORTS_DIR}/benchmark_report.html" 2>/dev/null || true
elif command -v open &>/dev/null; then
    open "${REPORTS_DIR}/benchmark_report.html" 2>/dev/null || true
fi

echo "============================================================"
log_ok "REPORTES GENERADOS EXITOSAMENTE"
echo "============================================================"
