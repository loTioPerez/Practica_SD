#!/usr/bin/env bash
# =================================================================
# start_direct_only.sh - Solo arquitectura DIRECTA
# =================================================================
# Servicios:
#   - Docker: Redis (solo)
#   - Seed de Redis
#   - API Directa: 2 instancias (puertos 8000, 8001)
#   - NGINX: balanceador (puerto 80)
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "LEVANTANDO ARQUITECTURA DIRECTA"
check_requirements
log_step "Limpiando puertos residuales antes del arranque..."
kill_port_listener 8000
kill_port_listener 8001

# ── 1. Docker (solo Redis) ────────────────────────────────────────
start_docker_services redis
wait_for_port 6379 "Redis" 30

# ── 2. Inicializar Redis ──────────────────────────────────────────
init_redis_state

# ── 3. API Directa (2 instancias) ────────────────────────────────
run_python_bg "direct_api_0" "concert_ticketing.apps.direct_api.main" \
    DIRECT_API_PORT=8000
run_python_bg "direct_api_1" "concert_ticketing.apps.direct_api.main" \
    DIRECT_API_PORT=8001

wait_for_port 8000 "API Directa :8000" 15
wait_for_port 8001 "API Directa :8001" 15

# ── 4. NGINX (opcional) ──────────────────────────────────────────
NGINX_OK=false
log_step "Configurando y arrancando NGINX..."
NGINX_CONF="$ROOT_DIR/deploy/nginx"
if command -v nginx &>/dev/null; then
    sudo nginx -s stop 2>/dev/null || true
    sleep 1
    if sudo nginx -c "$NGINX_CONF/nginx.conf" -p "$NGINX_CONF/" 2>/dev/null; then
        if wait_for_port 80 "NGINX" 10 2>/dev/null; then
            NGINX_OK=true
        else
            log_warn "NGINX arrancó pero no responde en puerto 80"
        fi
    else
        log_warn "NGINX falló al arrancar (revisa deploy/nginx/nginx.conf y mime.types)"
    fi
else
    log_warn "NGINX no instalado."
fi
if ! $NGINX_OK; then
    log_warn "Continuando SIN NGINX. Usa :8000 o :8001 directamente."
    log_info "Para instalar: sudo apt install nginx"
    log_info "Consulta: docs/NGINX_TROUBLESHOOTING.md"
fi

# ── Resumen ──────────────────────────────────────────────────────
log_header "ARQUITECTURA DIRECTA LEVANTADA"
echo -e "  ${GREEN}●${NC} Redis             → localhost:6379"
echo -e "  ${GREEN}●${NC} API Directa #0    → http://localhost:8000"
echo -e "  ${GREEN}●${NC} API Directa #1    → http://localhost:8001"
if $NGINX_OK; then
    echo -e "  ${GREEN}●${NC} NGINX (balanceo)  → http://localhost:80"
else
    echo -e "  ${YELLOW}○${NC} NGINX (balanceo)  → NO activo (usa :8000 o :8001)"
fi
echo ""
echo -e "  ${CYAN}Health check:${NC}  curl http://localhost:8000/health"
echo -e "  ${CYAN}Benchmark:${NC}     ./scripts/run_direct_benchmark.sh"
echo -e "  ${YELLOW}Parar:${NC}         ./scripts/stop_all.sh"
echo ""
