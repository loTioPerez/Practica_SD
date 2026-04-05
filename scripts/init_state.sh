#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "INICIALIZANDO ESTADO DEL SISTEMA"
check_requirements

log_step "Asegurando infraestructura Docker..."
start_docker_services redis rabbitmq
wait_for_port 6379 "Redis" 45
wait_for_port 5672 "RabbitMQ" 60
wait_for_rabbitmq_ready 60

log_step "Inicializando Redis con estado base..."
init_redis_state

log_header "ESTADO INICIALIZADO"
echo -e "  ${GREEN}OK${NC} Redis inicializado"
echo -e "  ${GREEN}OK${NC} RabbitMQ operativo"
echo ""
