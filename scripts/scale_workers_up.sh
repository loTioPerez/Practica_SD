#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

target_count="${1:-}"

current_workers=()
for pidfile in "$PIDS_DIR"/worker_*.pid; do
    [[ -f "$pidfile" ]] || continue
    name="$(basename "$pidfile" .pid)"
    pid="$(cat "$pidfile")"
    if is_running "$pid"; then
        current_workers+=("$name")
    else
        rm -f "$pidfile"
    fi
done

current_count="${#current_workers[@]}"
if [[ -z "$target_count" ]]; then
    target_count=$(( current_count + 1 ))
fi

if (( target_count <= current_count )); then
    log_info "Ya hay ${current_count} worker(s) activos. No hace falta escalar hacia arriba."
    exit 0
fi

log_header "ESCALANDO WORKERS HACIA ARRIBA"
log_info "Workers actuales: ${current_count}"
log_info "Workers objetivo: ${target_count}"

for (( i=current_count; i<target_count; i++ )); do
    run_python_bg "worker_${i}" "concert_ticketing.apps.worker.main"
    sleep 1
done

log_ok "Workers escalados a ${target_count}"
