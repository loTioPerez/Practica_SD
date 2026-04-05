#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

target_count="${1:-}"

worker_names=()
for pidfile in "$PIDS_DIR"/worker_*.pid; do
    [[ -f "$pidfile" ]] || continue
    name="$(basename "$pidfile" .pid)"
    pid="$(cat "$pidfile")"
    if is_running "$pid"; then
        worker_names+=("$name")
    else
        rm -f "$pidfile"
    fi
done

current_count="${#worker_names[@]}"
if [[ -z "$target_count" ]]; then
    target_count=$(( current_count > 0 ? current_count - 1 : 0 ))
fi

if (( target_count < 0 )); then
    target_count=0
fi

if (( target_count >= current_count )); then
    log_info "Ya hay ${current_count} worker(s) activos. No hace falta escalar hacia abajo."
    exit 0
fi

log_header "ESCALANDO WORKERS HACIA ABAJO"
log_info "Workers actuales: ${current_count}"
log_info "Workers objetivo: ${target_count}"

for (( i=current_count-1; i>=target_count; i-- )); do
    stop_process "worker_${i}"
done

log_ok "Workers reducidos a ${target_count}"
