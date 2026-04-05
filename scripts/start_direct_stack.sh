#!/usr/bin/env bash
# =================================================================
# start_direct_stack.sh - Levanta la pila de la arquitectura directa
# =================================================================
# Wrapper mejorado que usa start_direct_only.sh
# Mantenido por compatibilidad con scripts existentes.
# =================================================================
set -euo pipefail
exec "$(dirname "${BASH_SOURCE[0]}")/start_direct_only.sh" "$@"
