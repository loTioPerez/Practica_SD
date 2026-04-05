#!/usr/bin/env bash
# =================================================================
# logs.sh - Ver logs en tiempo real
# =================================================================
# Uso:
#   ./scripts/logs.sh           → Todos los logs
#   ./scripts/logs.sh direct    → Solo logs de API Directa
#   ./scripts/logs.sh indirect  → Solo logs de Gateway + Workers
#   ./scripts/logs.sh worker    → Solo logs de Workers
#   ./scripts/logs.sh gateway   → Solo log del Gateway
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

FILTER="${1:-all}"

get_log_files() {
    case "$FILTER" in
        direct)
            find "$LOGS_DIR" -name "direct_api_*.log" 2>/dev/null
            ;;
        indirect)
            find "$LOGS_DIR" -name "indirect_gateway.log" -o -name "worker_*.log" 2>/dev/null
            ;;
        worker|workers)
            find "$LOGS_DIR" -name "worker_*.log" 2>/dev/null
            ;;
        gateway)
            find "$LOGS_DIR" -name "indirect_gateway.log" 2>/dev/null
            ;;
        all|*)
            find "$LOGS_DIR" -name "*.log" 2>/dev/null
            ;;
    esac
}

log_files=$(get_log_files)

if [[ -z "$log_files" ]]; then
    log_warn "No hay archivos de log para '$FILTER' en $LOGS_DIR/"
    echo ""
    echo "Logs disponibles:"
    ls -la "$LOGS_DIR"/*.log 2>/dev/null || echo "  (ninguno)"
    exit 0
fi

echo -e "${BOLD}Mostrando logs: $FILTER${NC}"
echo -e "${CYAN}Archivos:${NC}"
echo "$log_files" | while read -r f; do
    echo "  • $f"
done
echo ""
echo -e "${YELLOW}Ctrl+C para salir${NC}"
echo "────────────────────────────────────────────────────────────"

# shellcheck disable=SC2086
tail -f $log_files
