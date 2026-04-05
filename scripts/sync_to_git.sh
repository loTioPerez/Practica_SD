#!/usr/bin/env bash
# =============================================================================
# sync_to_git.sh - Sincronizar código local con el repo Git del compañero
# =============================================================================
# Uso: ./scripts/sync_to_git.sh [URL_REPO]
#
# Si no se pasa URL como argumento, la pedirá interactivamente.
# =============================================================================
set -euo pipefail

# ── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Directorio del proyecto (donde está este script) ────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Sincronización de código → Repo Git del compañero${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
echo

# ── 1. Obtener URL del repo ──────────────────────────────────────────────────
if [[ $# -ge 1 ]]; then
    REPO_URL="$1"
else
    read -rp "URL del repo de tu compañero (HTTPS o SSH): " REPO_URL
fi

if [[ -z "$REPO_URL" ]]; then
    log_error "No se proporcionó URL del repositorio."
    exit 1
fi

log_info "Repo destino: $REPO_URL"
echo

# ── 2. Clonar en directorio temporal ────────────────────────────────────────
TEMP_DIR="/tmp/practica_sd_git_$(date +%s)"
log_info "Clonando repo en: $TEMP_DIR"

if ! git clone "$REPO_URL" "$TEMP_DIR"; then
    log_error "No se pudo clonar el repositorio. Verifica la URL y tus credenciales."
    exit 1
fi
log_ok "Repo clonado correctamente."
echo

# ── 3. Copiar archivos (excluyendo temporales y generados) ──────────────────
log_info "Copiando archivos del proyecto..."

rsync -av --delete \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='logs/' \
    --exclude='.pids/' \
    --exclude='benchmarks/outputs/' \
    --exclude='.git' \
    --exclude='.env' \
    --exclude='*.log' \
    --exclude='htmlcov/' \
    --exclude='.coverage' \
    "$PROJECT_DIR/" "$TEMP_DIR/"

log_ok "Archivos copiados."
echo

# ── 4. Mostrar resumen de cambios ───────────────────────────────────────────
cd "$TEMP_DIR"

echo -e "${YELLOW}── Resumen de cambios ──────────────────────────────────────${NC}"
echo
git status --short
echo
echo -e "${YELLOW}── Estadísticas ────────────────────────────────────────────${NC}"
git diff --stat 2>/dev/null || true
echo

# Contar archivos nuevos, modificados, eliminados
NEW_FILES=$(git status --short | grep -c '^??' || true)
MOD_FILES=$(git status --short | grep -c '^ M\|^M' || true)
DEL_FILES=$(git status --short | grep -c '^ D\|^D' || true)

echo -e "  Archivos nuevos:      ${GREEN}${NEW_FILES}${NC}"
echo -e "  Archivos modificados: ${YELLOW}${MOD_FILES}${NC}"
echo -e "  Archivos eliminados:  ${RED}${DEL_FILES}${NC}"
echo

# ── 5. Pedir confirmación ───────────────────────────────────────────────────
read -rp "¿Hacer commit y push? (y/n): " CONFIRM

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    log_warn "Operación cancelada por el usuario."
    log_info "Los archivos siguen en: $TEMP_DIR"
    log_info "Puedes revisarlos manualmente y hacer push después."
    exit 0
fi

# ── 6. Pedir mensaje de commit (con default) ────────────────────────────────
DEFAULT_MSG="feat: Add Phase 3-4 - Indirect architecture and benchmarks"
read -rp "Mensaje de commit [$DEFAULT_MSG]: " COMMIT_MSG
COMMIT_MSG="${COMMIT_MSG:-$DEFAULT_MSG}"

# ── 7. Configurar identidad Git si no existe ────────────────────────────────
if [[ -z "$(git config user.name 2>/dev/null)" ]]; then
    read -rp "Tu nombre para Git: " GIT_NAME
    git config user.name "$GIT_NAME"
fi
if [[ -z "$(git config user.email 2>/dev/null)" ]]; then
    read -rp "Tu email para Git: " GIT_EMAIL
    git config user.email "$GIT_EMAIL"
fi

# ── 8. Commit y push ────────────────────────────────────────────────────────
log_info "Añadiendo archivos..."
git add .

log_info "Haciendo commit..."
git commit -m "$COMMIT_MSG"

log_info "Haciendo push..."
if git push; then
    log_ok "¡Push realizado correctamente!"
else
    log_error "Error al hacer push. Puede que necesites permisos de escritura."
    log_info "Los archivos siguen en: $TEMP_DIR"
    log_info "Puedes intentar manualmente: cd $TEMP_DIR && git push"
    exit 1
fi

echo

# ── 9. Verificar ────────────────────────────────────────────────────────────
log_info "Últimos commits:"
git log --oneline -5
echo

# ── 10. Limpiar temporal ────────────────────────────────────────────────────
read -rp "¿Eliminar directorio temporal? (y/n): " CLEANUP
if [[ "$CLEANUP" == "y" || "$CLEANUP" == "Y" ]]; then
    rm -rf "$TEMP_DIR"
    log_ok "Directorio temporal eliminado."
else
    log_info "Directorio temporal conservado en: $TEMP_DIR"
fi

echo
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ¡Sincronización completada!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
