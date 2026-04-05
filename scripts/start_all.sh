#!/usr/bin/env bash
# =================================================================
# start_all.sh - Levanta TODO el sistema (directa + indirecta)
# =================================================================
# Servicios que arranca:
#   - Docker: Redis + RabbitMQ
#   - Seed de Redis (seed_state.py)
#   - API Directa: 2 instancias (puertos 8000, 8001)
#   - NGINX: balanceador (puerto 80) [opcional]
#   - Gateway Indirecto: (puerto 8080)
#   - Workers: 3 instancias
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "LEVANTANDO SISTEMA COMPLETO"
check_requirements

ERRORS=0

# ── 1. Docker (Redis + RabbitMQ) ──────────────────────────────────
log_step "Paso 1/6: Levantando infraestructura Docker..."
start_docker_services redis rabbitmq

log_info "Esperando a que Redis esté listo..."
if ! wait_for_port 6379 "Redis" 45; then
    log_error "Redis no arrancó. Ejecuta: docker compose -f tools/local_dev/docker-compose.yml logs redis"
    exit 1
fi

log_info "Esperando a que RabbitMQ esté listo..."
if ! wait_for_port 5672 "RabbitMQ" 60; then
    log_error "RabbitMQ no arrancó. Ejecuta: docker compose -f tools/local_dev/docker-compose.yml logs rabbitmq"
    exit 1
fi

# Verificar que RabbitMQ realmente acepta conexiones (a veces el puerto abre antes de estar listo)
log_info "Verificando que RabbitMQ acepte conexiones..."
RMQ_READY=false
for i in $(seq 1 15); do
    if wait_for_port 15672 "RabbitMQ Management" 2 2>/dev/null; then
        RMQ_READY=true
        break
    fi
    sleep 1
done
if $RMQ_READY; then
    log_ok "RabbitMQ completamente listo"
else
    log_warn "RabbitMQ Management no responde (puede tardar más). Continuando..."
fi

# ── 2. Inicializar Redis ──────────────────────────────────────────
log_step "Paso 2/6: Inicializando estado en Redis..."
if init_redis_state; then
    log_ok "Redis inicializado correctamente"
else
    log_error "Fallo al inicializar Redis. Verifica que Redis esté corriendo."
    exit 1
fi

# ── 3. API Directa (2 instancias) ────────────────────────────────
log_step "Paso 3/6: Arrancando APIs Directas..."
run_python_bg "direct_api_0" "concert_ticketing.apps.direct_api.main" \
    DIRECT_API_PORT=8000
run_python_bg "direct_api_1" "concert_ticketing.apps.direct_api.main" \
    DIRECT_API_PORT=8001

log_info "Esperando a que las APIs Directas respondan..."
if wait_for_http "http://localhost:8000/health" "API Directa :8000" 20; then
    log_ok "API Directa #0 respondiendo"
else
    log_warn "API Directa :8000 no responde al health check"
    log_info "  → Revisa log: $LOGS_DIR/direct_api_0.log"
    ((ERRORS++)) || true
fi

if wait_for_http "http://localhost:8001/health" "API Directa :8001" 20; then
    log_ok "API Directa #1 respondiendo"
else
    log_warn "API Directa :8001 no responde al health check"
    log_info "  → Revisa log: $LOGS_DIR/direct_api_1.log"
    ((ERRORS++)) || true
fi

# ── 4. NGINX (opcional — continúa si falla) ───────────────────────
log_step "Paso 4/6: Configurando NGINX (opcional)..."
NGINX_OK=false
NGINX_CONF="$ROOT_DIR/deploy/nginx"
if command -v nginx &>/dev/null; then
    # Parar nginx si ya corre
    sudo nginx -s stop 2>/dev/null || true
    sleep 1
    if sudo nginx -c "$NGINX_CONF/nginx.conf" -p "$NGINX_CONF/" 2>/dev/null; then
        if wait_for_port 80 "NGINX" 10 2>/dev/null; then
            NGINX_OK=true
            log_ok "NGINX activo en puerto 80"
        else
            log_warn "NGINX arrancó pero no responde en puerto 80"
        fi
    else
        log_warn "NGINX falló al arrancar (revisa deploy/nginx/nginx.conf)"
    fi
else
    log_warn "NGINX no instalado (omitido)"
fi
if ! $NGINX_OK; then
    log_warn "Continuando SIN NGINX. Las APIs están disponibles directamente en :8000 y :8001"
    log_info "  → Para instalar NGINX: sudo apt install nginx"
    log_info "  → Consulta: docs/NGINX_TROUBLESHOOTING.md"
fi

# ── 5. Gateway Indirecto ─────────────────────────────────────────
log_step "Paso 5/6: Arrancando Gateway Indirecto..."
run_python_bg "indirect_gateway" "concert_ticketing.apps.indirect_gateway.main"

if wait_for_http "http://localhost:8080/health" "Gateway Indirecto" 30; then
    log_ok "Gateway Indirecto respondiendo"
else
    log_warn "Gateway Indirecto :8080 no responde al health check"
    log_info "  → Revisa log: $LOGS_DIR/indirect_gateway.log"
    log_info "  → Verifica que RabbitMQ esté healthy: docker compose -f tools/local_dev/docker-compose.yml ps"
    ((ERRORS++)) || true
fi

# ── 6. Workers (3 instancias) ────────────────────────────────────
log_step "Paso 6/6: Arrancando Workers..."
for i in 0 1 2; do
    run_python_bg "worker_${i}" "concert_ticketing.apps.worker.main"
    sleep 1
done
log_ok "3 Workers arrancados"

# ── Resumen ──────────────────────────────────────────────────────
echo ""
log_header "SISTEMA COMPLETO LEVANTADO"
echo -e "  ${GREEN}●${NC} Redis             → localhost:6379"
echo -e "  ${GREEN}●${NC} RabbitMQ          → localhost:5672  (mgmt: http://localhost:15672)"
echo -e "  ${GREEN}●${NC} API Directa #0    → http://localhost:8000"
echo -e "  ${GREEN}●${NC} API Directa #1    → http://localhost:8001"
if $NGINX_OK; then
    echo -e "  ${GREEN}●${NC} NGINX (balanceo)  → http://localhost:80"
else
    echo -e "  ${YELLOW}○${NC} NGINX (balanceo)  → NO activo (usa :8000 o :8001)"
fi
echo -e "  ${GREEN}●${NC} Gateway Indirecto → http://localhost:8080"
echo -e "  ${GREEN}●${NC} Workers           → 3 instancias"
echo ""
echo -e "  ${CYAN}Logs:${NC}  $LOGS_DIR/"
echo -e "  ${CYAN}PIDs:${NC}  $PIDS_DIR/"
echo ""

if (( ERRORS > 0 )); then
    log_warn "$ERRORS servicio(s) no respondieron correctamente."
    echo -e "  ${YELLOW}Diagnóstico:${NC}  ./scripts/verify_system.sh"
    echo ""
fi

echo -e "  ${YELLOW}Verificar:${NC}   ./scripts/verify_system.sh"
echo -e "  ${YELLOW}Parar todo:${NC}  ./scripts/stop_all.sh"
echo -e "  ${YELLOW}Estado:${NC}      ./scripts/status.sh"
echo ""
