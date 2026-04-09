#!/usr/bin/env bash
# =================================================================
# start_without_nginx.sh - Levanta el sistema SIN NGINX
# =================================================================
# Ideal para desarrollo local donde NGINX no está instalado.
# Las APIs se acceden directamente por sus puertos:
#   - API Directa:       http://localhost:8000 y http://localhost:8001
#   - Gateway Indirecto: http://localhost:8080
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "LEVANTANDO SISTEMA (SIN NGINX)"
check_requirements

# ── 1. Docker (Redis + RabbitMQ) ──────────────────────────────────
start_docker_services redis rabbitmq
wait_for_port 6379 "Redis" 30
wait_for_port 5672 "RabbitMQ" 30

# ── 2. Inicializar Redis ──────────────────────────────────────────
init_redis_state

# ── 3. API Directa (2 instancias) ────────────────────────────────
run_python_bg "direct_api_0" "concert_ticketing.apps.direct_api.main" \
    DIRECT_API_PORT=8000
run_python_bg "direct_api_1" "concert_ticketing.apps.direct_api.main" \
    DIRECT_API_PORT=8001

wait_for_port 8000 "API Directa :8000" 15
wait_for_port 8001 "API Directa :8001" 15

# ── 4. Gateway Indirecto ─────────────────────────────────────────
run_python_bg "indirect_gateway" "concert_ticketing.apps.indirect_gateway.main"
wait_for_port 8080 "Gateway Indirecto" 15

# ── 5. Workers (3 instancias) ────────────────────────────────────
for i in 0 1 2; do
    run_python_bg "worker_${i}" "concert_ticketing.apps.worker.main"
    sleep 0.5
done
log_ok "3 Workers arrancados"

# ── Resumen ──────────────────────────────────────────────────────
log_header "SISTEMA LEVANTADO (SIN NGINX)"
echo -e "  ${GREEN}●${NC} Redis             → localhost:6379"
echo -e "  ${GREEN}●${NC} RabbitMQ          → localhost:5672  (mgmt: http://localhost:15672)"
echo -e "  ${GREEN}●${NC} API Directa #0    → http://localhost:8000"
echo -e "  ${GREEN}●${NC} API Directa #1    → http://localhost:8001"
echo -e "  ${YELLOW}○${NC} NGINX             → NO usado (accede directamente a :8000/:8001)"
echo -e "  ${GREEN}●${NC} Gateway Indirecto → http://localhost:8080"
echo -e "  ${GREEN}●${NC} Workers           → 3 instancias"
echo ""
echo -e "  ${CYAN}Health check:${NC}  curl http://localhost:8000/health"
echo -e "  ${CYAN}Benchmark:${NC}     BASE_URL=http://localhost:8000 ./scripts/run_direct_benchmark.sh"
echo ""
echo -e "  ${CYAN}Logs:${NC}  $LOGS_DIR/"
echo -e "  ${CYAN}PIDs:${NC}  $PIDS_DIR/"
echo ""
echo -e "  ${YELLOW}Parar todo:${NC}  ./scripts/stop_all.sh"
echo ""
echo -e "  ${BLUE}NOTA:${NC} Sin NGINX no hay balanceo de carga."
echo -e "  ${BLUE}      ${NC} Para benchmarks, usa BASE_URL=http://localhost:8000"
echo -e "  ${BLUE}      ${NC} o http://localhost:8001 directamente."
echo ""
