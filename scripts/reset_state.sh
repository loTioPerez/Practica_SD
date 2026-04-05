#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "RESETEANDO ESTADO ENTRE BENCHMARKS"
check_requirements

worker_names=()
for pidfile in "$PIDS_DIR"/worker_*.pid; do
    [[ -f "$pidfile" ]] || continue
    name="$(basename "$pidfile" .pid)"
    pid="$(cat "$pidfile")"
    if is_running "$pid"; then
        worker_names+=("$name")
    fi
done

gateway_was_running=false
gateway_pid="$(get_pid indirect_gateway || true)"
if [[ -n "$gateway_pid" ]] && is_running "$gateway_pid"; then
    gateway_was_running=true
fi

if (( ${#worker_names[@]} > 0 )); then
    log_step "Parando workers para asegurar un reset limpio..."
    for worker_name in "${worker_names[@]}"; do
        stop_process "$worker_name"
    done
fi

if $gateway_was_running; then
    log_step "Reiniciando gateway indirecto para limpiar cola de respuestas..."
    stop_process "indirect_gateway"
fi

log_step "Asegurando infraestructura Docker..."
start_docker_services redis rabbitmq
wait_for_port 6379 "Redis" 45
wait_for_port 5672 "RabbitMQ" 60
wait_for_rabbitmq_ready 60

log_step "Limpiando Redis (FLUSHALL)..."
docker exec concert-ticketing-redis redis-cli FLUSHALL >/dev/null \
    && log_ok "Redis limpiado" \
    || {
        log_error "No se pudo limpiar Redis"
        exit 1
    }

log_step "Purgando cola principal de RabbitMQ..."
if PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -c "from concert_ticketing.shared.config import AppConfig; from concert_ticketing.adapters.messaging.rabbitmq.connection import create_channel, create_rabbitmq_connection; from concert_ticketing.adapters.messaging.rabbitmq.queue_setup import PURCHASE_QUEUE, setup_queues; cfg = AppConfig.from_env(); conn = create_rabbitmq_connection(cfg.rabbitmq); ch = create_channel(conn); setup_queues(ch); ch.queue_purge(queue=PURCHASE_QUEUE); conn.close()" \
    >/dev/null 2>&1; then
    log_ok "Cola principal de RabbitMQ purgada"
else
    log_warn "No se pudo purgar la cola principal de RabbitMQ"
fi

log_step "Reinicializando inventario base..."
init_redis_state

if $gateway_was_running; then
    run_python_bg "indirect_gateway" "concert_ticketing.apps.indirect_gateway.main"
    wait_for_http "http://localhost:8080/health" "Gateway Indirecto" 30
fi

if (( ${#worker_names[@]} > 0 )); then
    log_step "Rearrancando workers..."
    for worker_name in "${worker_names[@]}"; do
        run_python_bg "$worker_name" "concert_ticketing.apps.worker.main"
        sleep 1
    done
fi

log_header "ESTADO RESETEADO"
echo -e "  ${GREEN}OK${NC} Redis limpio e inicializado"
echo -e "  ${GREEN}OK${NC} Cola principal de RabbitMQ preparada"
echo ""
