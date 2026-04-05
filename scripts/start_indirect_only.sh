#!/usr/bin/env bash
# =================================================================
# start_indirect_only.sh - Solo arquitectura INDIRECTA
# =================================================================
# Servicios:
#   - Docker: Redis + RabbitMQ
#   - Seed de Redis
#   - Gateway Indirecto (puerto 8080)
#   - Workers: 3 instancias
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

NUM_WORKERS="${1:-3}"

log_header "LEVANTANDO ARQUITECTURA INDIRECTA"
check_requirements

# ── 1. Docker (Redis + RabbitMQ) ──────────────────────────────────
start_docker_services redis rabbitmq
wait_for_port 6379 "Redis" 30
wait_for_port 5672 "RabbitMQ" 30

# ── 2. Inicializar Redis ──────────────────────────────────────────
init_redis_state

# ── 3. Gateway Indirecto ─────────────────────────────────────────
run_python_bg "indirect_gateway" "concert_ticketing.apps.indirect_gateway.main"
wait_for_port 8080 "Gateway Indirecto" 15

# ── 4. Workers ───────────────────────────────────────────────────
log_step "Arrancando $NUM_WORKERS workers..."
for i in $(seq 0 $((NUM_WORKERS - 1))); do
    run_python_bg "worker_${i}" "concert_ticketing.apps.worker.main"
    sleep 0.5
done
log_ok "$NUM_WORKERS Workers arrancados"

# ── Resumen ──────────────────────────────────────────────────────
log_header "ARQUITECTURA INDIRECTA LEVANTADA"
echo -e "  ${GREEN}●${NC} Redis             → localhost:6379"
echo -e "  ${GREEN}●${NC} RabbitMQ          → localhost:5672  (mgmt: http://localhost:15672)"
echo -e "  ${GREEN}●${NC} Gateway Indirecto → http://localhost:8080"
echo -e "  ${GREEN}●${NC} Workers           → $NUM_WORKERS instancias"
echo ""
echo -e "  ${CYAN}Health check:${NC}  curl http://localhost:8080/health"
echo -e "  ${CYAN}Benchmark:${NC}     ./scripts/run_indirect_benchmark.sh"
echo -e "  ${YELLOW}Parar:${NC}         ./scripts/stop_all.sh"
echo ""
echo -e "  ${CYAN}Tip:${NC} Puedes cambiar el número de workers:"
echo -e "       ./scripts/start_indirect_only.sh 5"
echo ""
