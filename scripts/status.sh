#!/usr/bin/env bash
# =================================================================
# status.sh - Muestra el estado de todos los servicios
# =================================================================
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log_header "ESTADO DEL SISTEMA"

# Helpers
check_port() {
    (echo >/dev/tcp/localhost/"$1") 2>/dev/null && return 0 || return 1
}

print_status() {
    local name="$1"
    local port="$2"
    local extra="${3:-}"
    if check_port "$port"; then
        echo -e "  ${GREEN}●${NC}  $name  →  puerto $port  ${extra}"
    else
        echo -e "  ${RED}○${NC}  $name  →  puerto $port  (NO DISPONIBLE)"
    fi
}

# ── Docker Containers ────────────────────────────────────────────
echo -e "${BOLD}Docker Containers:${NC}"
if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -q "concert-ticketing"; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep "concert-ticketing" | while read -r line; do
        echo -e "  ${GREEN}●${NC}  $line"
    done
else
    echo -e "  ${RED}○${NC}  No hay contenedores corriendo"
fi
echo ""

# ── Servicios ────────────────────────────────────────────────────
echo -e "${BOLD}Servicios:${NC}"
print_status "Redis" 6379
print_status "RabbitMQ" 5672 "(mgmt: 15672)"
print_status "API Directa #0" 8000
print_status "API Directa #1" 8001
print_status "NGINX (balanceo)" 80
print_status "Gateway Indirecto" 8080
echo ""

# ── Procesos Python ──────────────────────────────────────────────
echo -e "${BOLD}Procesos Python (registrados):${NC}"
found=false
for pidfile in "$PIDS_DIR"/*.pid; do
    [[ -f "$pidfile" ]] || continue
    found=true
    name=$(basename "$pidfile" .pid)
    pid=$(cat "$pidfile")
    if is_running "$pid"; then
        echo -e "  ${GREEN}●${NC}  $name  (PID $pid)"
    else
        echo -e "  ${RED}○${NC}  $name  (PID $pid - MUERTO)"
    fi
done
if ! $found; then
    echo -e "  ${YELLOW}─${NC}  No hay procesos registrados"
fi
echo ""

# ── Health Checks ────────────────────────────────────────────────
echo -e "${BOLD}Health Checks:${NC}"

for endpoint in "http://localhost:8000/health:API_Directa_0" "http://localhost:8001/health:API_Directa_1" "http://localhost:80/health:NGINX" "http://localhost:8080/health:Gateway_Indirecto"; do
    url="${endpoint%%:*}"
    name="${endpoint##*:}"
    response=$(curl -sf -w "%{http_code}" -o /dev/null "$url" 2>/dev/null) && \
        echo -e "  ${GREEN}✔${NC}  $name  →  HTTP $response" || \
        echo -e "  ${RED}✘${NC}  $name  →  No responde"
done
echo ""

# ── Puertos en uso ───────────────────────────────────────────────
echo -e "${BOLD}Puertos relevantes en uso:${NC}"
for port in 6379 5672 15672 8000 8001 80 8080; do
    pid_info=$(lsof -ti :"$port" 2>/dev/null | head -1)
    if [[ -n "$pid_info" ]]; then
        proc=$(ps -p "$pid_info" -o comm= 2>/dev/null || echo "?")
        echo -e "  ${GREEN}●${NC}  :$port  →  $proc (PID $pid_info)"
    fi
done
echo ""
