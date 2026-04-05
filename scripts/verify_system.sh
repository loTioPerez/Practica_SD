#!/usr/bin/env bash
# =================================================================
# verify_system.sh - Verifica que todos los servicios funcionan
# =================================================================
# Ejecuta health checks sobre todos los componentes y muestra un
# resumen claro de qué funciona y qué no, con sugerencias de fix.
# =================================================================
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "VERIFICACIÓN DEL SISTEMA"

TOTAL=0
OK=0
FAIL=0
WARN=0

check_service() {
    local name="$1"
    local check_type="$2"  # port | http | docker
    local target="$3"
    local fix_hint="${4:-}"

    ((TOTAL++)) || true

    case "$check_type" in
        port)
            if (echo >/dev/tcp/localhost/"$target") 2>/dev/null; then
                echo -e "  ${GREEN}✔${NC} $name → puerto $target abierto"
                ((OK++)) || true
            else
                echo -e "  ${RED}✘${NC} $name → puerto $target NO accesible"
                [[ -n "$fix_hint" ]] && echo -e "    ${YELLOW}→ $fix_hint${NC}"
                ((FAIL++)) || true
            fi
            ;;
        http)
            local status
            status=$(curl -sf -o /dev/null -w "%{http_code}" "$target" 2>/dev/null || echo "000")
            if [[ "$status" =~ ^2 ]]; then
                echo -e "  ${GREEN}✔${NC} $name → $target (HTTP $status)"
                ((OK++)) || true
            elif [[ "$status" == "000" ]]; then
                echo -e "  ${RED}✘${NC} $name → $target (sin respuesta)"
                [[ -n "$fix_hint" ]] && echo -e "    ${YELLOW}→ $fix_hint${NC}"
                ((FAIL++)) || true
            else
                echo -e "  ${YELLOW}⚠${NC} $name → $target (HTTP $status)"
                [[ -n "$fix_hint" ]] && echo -e "    ${YELLOW}→ $fix_hint${NC}"
                ((WARN++)) || true
            fi
            ;;
        docker)
            local container_status
            container_status=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" ps --format '{{.Status}}' "$target" 2>/dev/null || echo "")
            if [[ "$container_status" == *"Up"* ]] || [[ "$container_status" == *"healthy"* ]]; then
                echo -e "  ${GREEN}✔${NC} $name → contenedor corriendo"
                ((OK++)) || true
            elif [[ -z "$container_status" ]]; then
                echo -e "  ${RED}✘${NC} $name → contenedor no existe"
                [[ -n "$fix_hint" ]] && echo -e "    ${YELLOW}→ $fix_hint${NC}"
                ((FAIL++)) || true
            else
                echo -e "  ${YELLOW}⚠${NC} $name → estado: $container_status"
                [[ -n "$fix_hint" ]] && echo -e "    ${YELLOW}→ $fix_hint${NC}"
                ((WARN++)) || true
            fi
            ;;
    esac
}

# ── Infraestructura Docker ────────────────────────────────────────
echo -e "\n${BOLD}  Infraestructura Docker${NC}"
echo -e "  ─────────────────────────────────────"
check_service "Redis (Docker)" docker redis \
    "Ejecuta: docker compose -f tools/local_dev/docker-compose.yml up -d redis"
check_service "RabbitMQ (Docker)" docker rabbitmq \
    "Ejecuta: docker compose -f tools/local_dev/docker-compose.yml up -d rabbitmq"

# ── Puertos de infraestructura ────────────────────────────────────
echo -e "\n${BOLD}  Puertos de Infraestructura${NC}"
echo -e "  ─────────────────────────────────────"
check_service "Redis (puerto)" port 6379 \
    "Verifica Docker: docker ps | grep redis"
check_service "RabbitMQ (AMQP)" port 5672 \
    "Verifica Docker: docker ps | grep rabbitmq"
check_service "RabbitMQ (Management)" port 15672 \
    "Abre http://localhost:15672 (guest/guest)"

# ── APIs Directas ─────────────────────────────────────────────────
echo -e "\n${BOLD}  APIs Directas${NC}"
echo -e "  ─────────────────────────────────────"
check_service "API Directa #0 (health)" http "http://localhost:8000/health" \
    "Revisa log: $LOGS_DIR/direct_api_0.log"
check_service "API Directa #1 (health)" http "http://localhost:8001/health" \
    "Revisa log: $LOGS_DIR/direct_api_1.log"

# ── NGINX ─────────────────────────────────────────────────────────
echo -e "\n${BOLD}  NGINX (opcional)${NC}"
echo -e "  ─────────────────────────────────────"
check_service "NGINX balanceador" http "http://localhost:80/health" \
    "NGINX es opcional. APIs disponibles en :8000 y :8001 directamente"

# ── Arquitectura Indirecta ────────────────────────────────────────
echo -e "\n${BOLD}  Arquitectura Indirecta${NC}"
echo -e "  ─────────────────────────────────────"
check_service "Gateway Indirecto (health)" http "http://localhost:8080/health" \
    "Revisa log: $LOGS_DIR/indirect_gateway.log"

# ── Workers (verificar procesos) ──────────────────────────────────
echo -e "\n${BOLD}  Workers${NC}"
echo -e "  ─────────────────────────────────────"
WORKER_COUNT=0
for pidfile in "$PIDS_DIR"/worker_*.pid; do
    [[ -f "$pidfile" ]] || continue
    pid=$(cat "$pidfile")
    name=$(basename "$pidfile" .pid)
    ((TOTAL++)) || true
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "  ${GREEN}✔${NC} $name → PID $pid corriendo"
        ((OK++)) || true
        ((WORKER_COUNT++)) || true
    else
        echo -e "  ${RED}✘${NC} $name → PID $pid NO corriendo"
        echo -e "    ${YELLOW}→ Revisa log: $LOGS_DIR/${name}.log${NC}"
        ((FAIL++)) || true
    fi
done
if [[ $WORKER_COUNT -eq 0 ]]; then
    # No se encontraron PIDs de workers, verificar con pgrep
    pgrep_count=$(pgrep -fc "concert_ticketing.apps.worker" 2>/dev/null) || pgrep_count=0
    pgrep_count=$(echo "$pgrep_count" | tr -d '[:space:]')
    if [[ "$pgrep_count" -gt 0 ]]; then
        echo -e "  ${GREEN}✔${NC} $pgrep_count worker(s) detectados (sin PID registrado)"
    else
        echo -e "  ${YELLOW}⚠${NC} No se detectaron workers corriendo"
        echo -e "    ${YELLOW}→ Ejecuta: ./scripts/start_all.sh${NC}"
    fi
fi

# ── Logs recientes ────────────────────────────────────────────────
echo -e "\n${BOLD}  Logs recientes (últimos errores)${NC}"
echo -e "  ─────────────────────────────────────"
HAS_ERRORS=false
for logfile in "$LOGS_DIR"/*.log; do
    [[ -f "$logfile" ]] || continue
    name=$(basename "$logfile")
    error_count=$(grep -ci "error\|exception\|traceback" "$logfile" 2>/dev/null) || error_count=0
    error_count=$(echo "$error_count" | tr -d '[:space:]')
    if [[ "$error_count" -gt 0 ]]; then
        echo -e "  ${RED}⚠${NC} $name → $error_count errores encontrados"
        # Mostrar última línea de error
        last_error=$(grep -i "error\|exception" "$logfile" 2>/dev/null | tail -1)
        if [[ -n "$last_error" ]]; then
            echo -e "    ${CYAN}Último: ${last_error:0:100}${NC}"
        fi
        HAS_ERRORS=true
    fi
done
if ! $HAS_ERRORS; then
    echo -e "  ${GREEN}✔${NC} Sin errores en los logs"
fi

# ── Resumen ───────────────────────────────────────────────────────
echo ""
log_header "RESUMEN DE VERIFICACIÓN"
echo -e "  Total verificaciones: ${BOLD}$TOTAL${NC}"
echo -e "  ${GREEN}Correctos:${NC}  $OK"
echo -e "  ${RED}Fallidos:${NC}   $FAIL"
echo -e "  ${YELLOW}Warnings:${NC}   $WARN"
echo ""

if (( FAIL == 0 && WARN == 0 )); then
    echo -e "  ${GREEN}${BOLD}✔ SISTEMA OPERATIVO — Todo funciona correctamente${NC}"
elif (( FAIL == 0 )); then
    echo -e "  ${YELLOW}${BOLD}⚠ SISTEMA PARCIALMENTE OPERATIVO — Hay warnings${NC}"
else
    echo -e "  ${RED}${BOLD}✘ SISTEMA CON PROBLEMAS — $FAIL servicio(s) fallidos${NC}"
    echo ""
    echo -e "  ${BOLD}Pasos sugeridos:${NC}"
    echo -e "    1. Verifica Docker: docker ps"
    echo -e "    2. Revisa los logs: ls -la $LOGS_DIR/"
    echo -e "    3. Reinicia todo:   ./scripts/stop_all.sh && ./scripts/start_all.sh"
    echo -e "    4. Reset completo:  ./scripts/reset_system.sh"
fi
echo ""
