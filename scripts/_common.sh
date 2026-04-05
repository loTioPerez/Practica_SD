#!/usr/bin/env bash
# =================================================================
# _common.sh - Funciones comunes para todos los scripts
# =================================================================

# Directorio raíz del proyecto
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Directorios
LOGS_DIR="$ROOT_DIR/logs"
PIDS_DIR="$ROOT_DIR/.pids"
SCRIPTS_DIR="$ROOT_DIR/scripts"

# Crear directorios si no existen
mkdir -p "$LOGS_DIR" "$PIDS_DIR"

# ---- Colores ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ---- Funciones de logging ----
log_info()    { echo -e "${BLUE}[INFO]${NC}    $(date '+%H:%M:%S') $*"; }
log_ok()      { echo -e "${GREEN}[  OK  ]${NC}  $(date '+%H:%M:%S') $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $(date '+%H:%M:%S') $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $(date '+%H:%M:%S') $*"; }
log_step()    { echo -e "${CYAN}[STEP]${NC}    $(date '+%H:%M:%S') $*"; }
log_header()  {
    echo ""
    echo -e "${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  $*${NC}"
    echo -e "${BOLD}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# ---- Verificación de requisitos ----
check_command() {
    if ! command -v "$1" &>/dev/null; then
        log_error "$1 no está instalado. Instálalo antes de continuar."
        return 1
    fi
}

check_requirements() {
    local ok=true
    log_step "Verificando requisitos..."

    for cmd in docker python3 pip; do
        if command -v "$cmd" &>/dev/null; then
            log_ok "$cmd encontrado: $(command -v "$cmd")"
        else
            log_error "$cmd NO encontrado"
            ok=false
        fi
    done

    if docker compose version &>/dev/null; then
        log_ok "docker compose disponible"
    elif docker-compose --version &>/dev/null; then
        log_ok "docker-compose disponible"
        DOCKER_COMPOSE="docker-compose"
    else
        log_error "docker compose NO disponible"
        ok=false
    fi

    if ! $ok; then
        log_error "Faltan requisitos. Instálalos antes de continuar."
        exit 1
    fi
    echo ""
}

# Docker compose command
DOCKER_COMPOSE="docker compose"
if ! docker compose version &>/dev/null 2>&1; then
    if docker-compose --version &>/dev/null 2>&1; then
        DOCKER_COMPOSE="docker-compose"
    fi
fi
COMPOSE_FILE="$ROOT_DIR/tools/local_dev/docker-compose.yml"

# ---- Funciones de gestión de procesos ----
save_pid() {
    local name="$1"
    local pid="$2"
    echo "$pid" > "$PIDS_DIR/${name}.pid"
}

get_pid() {
    local name="$1"
    local pidfile="$PIDS_DIR/${name}.pid"
    if [[ -f "$pidfile" ]]; then
        cat "$pidfile"
    fi
}

is_running() {
    local pid="$1"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

stop_process() {
    local name="$1"
    local pid
    pid=$(get_pid "$name")
    if [[ -n "$pid" ]] && is_running "$pid"; then
        kill "$pid" 2>/dev/null && log_ok "Detenido $name (PID $pid)" || true
        # Esperar a que termine
        for i in $(seq 1 10); do
            if ! is_running "$pid"; then break; fi
            sleep 0.5
        done
        # Forzar si sigue vivo
        if is_running "$pid"; then
            kill -9 "$pid" 2>/dev/null || true
            log_warn "Forzado kill de $name (PID $pid)"
        fi
    fi
    rm -f "$PIDS_DIR/${name}.pid" 2>/dev/null || true
}

# ---- Funciones de espera ----
wait_for_port() {
    local port="$1"
    local name="${2:-servicio}"
    local max_wait="${3:-30}"
    local waited=0

    while ! (echo >/dev/tcp/localhost/"$port") 2>/dev/null; do
        if (( waited >= max_wait )); then
            log_error "$name no respondió en puerto $port tras ${max_wait}s"
            return 1
        fi
        sleep 1
        ((waited++))
    done
    log_ok "$name listo en puerto $port (${waited}s)"
}

wait_for_http() {
    local url="$1"
    local name="${2:-servicio}"
    local max_wait="${3:-30}"
    local waited=0

    while ! curl -sf "$url" &>/dev/null; do
        if (( waited >= max_wait )); then
            log_error "$name no respondió en $url tras ${max_wait}s"
            return 1
        fi
        sleep 1
        ((waited++))
    done
    log_ok "$name respondiendo en $url (${waited}s)"
}

wait_for_rabbitmq_ready() {
    local max_wait="${1:-60}"
    local waited=0

    while true; do
        if PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
            python3 -c "from concert_ticketing.shared.health import check_rabbitmq_health; import sys; result = check_rabbitmq_health(); sys.exit(0 if result.healthy else 1)" \
            >/dev/null 2>&1; then
            log_ok "RabbitMQ operativo (${waited}s)"
            return 0
        fi
        if (( waited >= max_wait )); then
            log_error "RabbitMQ no quedó operativo tras ${max_wait}s"
            return 1
        fi
        sleep 1
        ((waited++))
    done
}

# ---- Funciones de Docker ----
start_docker_services() {
    local services="$*"
    log_step "Levantando Docker: $services"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d $services
}

stop_docker_services() {
    log_step "Parando contenedores Docker..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down 2>/dev/null || true
}

# ---- Funciones de Python ----
run_python_bg() {
    local name="$1"
    local module="$2"
    local logfile="$LOGS_DIR/${name}.log"
    shift 2
    local extra_env=()
    if (( $# > 0 )); then
        extra_env=("$@")
    fi
    local env_cmd=(
        env
        "PYTHONPATH=$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
    )
    if (( ${#extra_env[@]} > 0 )); then
        env_cmd+=("${extra_env[@]}")
    fi
    env_cmd+=(
        python3
        -m
        "$module"
    )

    log_step "Arrancando $name..."
    "${env_cmd[@]}" > "$logfile" 2>&1 &
    local pid=$!
    save_pid "$name" "$pid"
    log_info "$name arrancado (PID $pid) → log: $logfile"
}

init_redis_state() {
    log_step "Inicializando estado en Redis (seed_state.py)..."
    PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
        python3 "$ROOT_DIR/tools/local_dev/seed_state.py" --ticket-type all 2>&1
    log_ok "Estado de Redis inicializado"
}

# ---- Kill genérico por patrón ----
kill_pattern() {
    local pattern="$1"
    local pids
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill 2>/dev/null || true
        log_ok "Procesos '$pattern' detenidos"
    fi
}

kill_port_listener() {
    local port="$1"
    local pids

    pids=$(netstat -ano 2>/dev/null | grep LISTENING | grep ":${port}[[:space:]]" | awk '{print $NF}' | sort -u || true)
    if [[ -z "$pids" ]]; then
        return 0
    fi

    for pid in $pids; do
        [[ -n "$pid" ]] || continue
        taskkill.exe //F //PID "$pid" >/dev/null 2>&1 || true
        log_ok "Puerto ${port} liberado (PID ${pid})"
    done
}

to_python_path() {
    local path="$1"
    if command -v cygpath >/dev/null 2>&1; then
        cygpath -w "$path"
    else
        echo "$path"
    fi
}
