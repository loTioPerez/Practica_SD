#!/usr/bin/env bash
# =================================================================
# start_indirect_stack.sh - Levanta la pila de la arquitectura indirecta
# =================================================================
# Wrapper mejorado que usa start_indirect_only.sh
# Mantenido por compatibilidad con scripts existentes.
# =================================================================
set -euo pipefail
exec "$(dirname "${BASH_SOURCE[0]}")/start_indirect_only.sh" "$@"
