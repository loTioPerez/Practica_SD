#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Levantando Redis y RabbitMQ para desarrollo local..."
docker compose -f "$ROOT_DIR/tools/local_dev/docker-compose.yml" up -d redis rabbitmq

echo "Inicializando estado base en Redis..."
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
python3 "$ROOT_DIR/tools/local_dev/seed_state.py" --ticket-type all

echo "Servicios base levantados."
echo "Para arrancar la API directa:"
echo "  PYTHONPATH=\"$ROOT_DIR/src\" python3 -m concert_ticketing.apps.direct_api.main"
echo "Para usar NGINX, aplica la configuracion de deploy/nginx/nginx.conf y upstream.conf"
