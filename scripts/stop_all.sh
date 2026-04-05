#!/usr/bin/env bash
# =================================================================
# stop_all.sh - Para TODOS los servicios del sistema
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "PARANDO TODOS LOS SERVICIOS"

# ── 1. Parar procesos Python por PID file ────────────────────────
log_step "Parando procesos registrados..."
for pidfile in "$PIDS_DIR"/*.pid; do
    [[ -f "$pidfile" ]] || continue
    name=$(basename "$pidfile" .pid)
    stop_process "$name"
done

# ── 2. Kill de seguridad por patrón ─────────────────────────────
log_step "Limpiando procesos residuales..."
kill_pattern "concert_ticketing.apps.direct_api"
kill_pattern "concert_ticketing.apps.indirect_gateway"
kill_pattern "concert_ticketing.apps.worker"
kill_port_listener 8000
kill_port_listener 8001
kill_port_listener 8080

# ── 3. Parar NGINX ──────────────────────────────────────────────
if command -v nginx &>/dev/null; then
    log_step "Parando NGINX..."
    sudo nginx -s stop 2>/dev/null && log_ok "NGINX detenido" || log_info "NGINX no estaba corriendo"
fi

# ── 4. Parar Docker ─────────────────────────────────────────────
stop_docker_services

# ── 5. Limpiar PID files ────────────────────────────────────────
rm -f "$PIDS_DIR"/*.pid

# ── Resumen ──────────────────────────────────────────────────────
log_header "TODOS LOS SERVICIOS DETENIDOS"
echo -e "  ${GREEN}✔${NC} Procesos Python parados"
echo -e "  ${GREEN}✔${NC} NGINX parado"
echo -e "  ${GREEN}✔${NC} Docker containers parados"
echo -e "  ${GREEN}✔${NC} PID files limpiados"
echo ""
