#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Levantando Redis y RabbitMQ ==="
docker compose -f "$ROOT_DIR/tools/local_dev/docker-compose.yml" up -d redis rabbitmq

echo "Esperando a que Redis y RabbitMQ esten listos..."
sleep 5

echo "=== Inicializando estado base en Redis ==="
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
python3 "$ROOT_DIR/tools/local_dev/seed_state.py" --ticket-type all

echo ""
echo "=== Servicios base levantados ==="
echo ""
echo "Para arrancar workers (en terminales separadas):"
echo "  PYTHONPATH=\"$ROOT_DIR/src\" python3 -m concert_ticketing.apps.worker.main"
echo ""
echo "Para arrancar el gateway indirecto:"
echo "  PYTHONPATH=\"$ROOT_DIR/src\" python3 -m concert_ticketing.apps.indirect_gateway.main"
echo ""
echo "El gateway indirecto escucha en http://localhost:8080"
