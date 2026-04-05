#!/usr/bin/env bash
# =================================================================
# reset_system.sh - Reset completo del sistema
# =================================================================
# Acciones:
#   1. Para todos los servicios
#   2. Limpia datos de Redis
#   3. Limpia colas de RabbitMQ
#   4. Re-inicializa Redis con seed_state.py
#   5. Limpia logs
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "RESET COMPLETO DEL SISTEMA"

# ── 1. Parar todos los servicios ─────────────────────────────────
log_step "Parando todos los servicios..."
bash "$SCRIPTS_DIR/stop_all.sh" 2>/dev/null || true

# ── 2. Levantar infra para limpiar ──────────────────────────────
log_step "Levantando infraestructura para limpieza..."
start_docker_services redis rabbitmq
wait_for_port 6379 "Redis" 30
wait_for_port 5672 "RabbitMQ" 30

# ── 3. Limpiar Redis ────────────────────────────────────────────
log_step "Limpiando Redis (FLUSHALL)..."
docker exec concert-ticketing-redis redis-cli FLUSHALL 2>/dev/null \
    && log_ok "Redis limpiado" \
    || log_warn "No se pudo limpiar Redis"

# ── 4. Limpiar RabbitMQ ─────────────────────────────────────────
log_step "Reseteando colas de RabbitMQ..."
docker exec concert-ticketing-rabbitmq rabbitmqctl stop_app 2>/dev/null || true
docker exec concert-ticketing-rabbitmq rabbitmqctl reset 2>/dev/null || true
docker exec concert-ticketing-rabbitmq rabbitmqctl start_app 2>/dev/null || true
log_ok "RabbitMQ reseteado"

# ── 5. Re-inicializar estado de Redis ────────────────────────────
init_redis_state

# ── 6. Limpiar logs ─────────────────────────────────────────────
log_step "Limpiando logs..."
rm -f "$LOGS_DIR"/*.log
log_ok "Logs limpiados"

# ── 7. Limpiar PIDs ─────────────────────────────────────────────
rm -f "$PIDS_DIR"/*.pid

# ── 8. Parar infra ──────────────────────────────────────────────
stop_docker_services

# ── Resumen ──────────────────────────────────────────────────────
log_header "SISTEMA RESETEADO"
echo -e "  ${GREEN}✔${NC} Servicios parados"
echo -e "  ${GREEN}✔${NC} Redis limpiado y re-inicializado"
echo -e "  ${GREEN}✔${NC} RabbitMQ colas reseteadas"
echo -e "  ${GREEN}✔${NC} Logs limpiados"
echo -e "  ${GREEN}✔${NC} Infraestructura Docker parada"
echo ""
echo -e "  ${CYAN}Siguiente paso:${NC} Elige qué levantar:"
echo -e "    ./scripts/start_all.sh"
echo -e "    ./scripts/start_direct_only.sh"
echo -e "    ./scripts/start_indirect_only.sh"
echo ""
