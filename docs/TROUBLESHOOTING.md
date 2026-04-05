# Troubleshooting — Concert Ticketing System

Guía para resolver problemas comunes al ejecutar el sistema en local.

---

## 🔍 Diagnóstico rápido

Ejecuta el script de verificación para ver el estado de todos los servicios:

```bash
./scripts/verify_system.sh
```

---

## Problemas comunes

### 1. Las APIs Directas no responden al health check

**Síntoma:** `curl http://localhost:8000/health` no responde o da error.

**Posibles causas:**
- La API no ha terminado de arrancar (dale 10-15 segundos)
- Redis no está corriendo
- Error en el código de la aplicación

**Solución:**
```bash
# Verificar que Redis corre
docker ps | grep redis

# Ver logs de la API
cat logs/direct_api_0.log

# Reiniciar
./scripts/stop_all.sh
./scripts/start_all.sh
```

### 2. No se puede arrancar segunda instancia de API Directa

**Síntoma:** Solo una instancia arranca, la otra falla con "Address already in use".

**Causa:** El puerto estaba hardcodeado. Ya está arreglado — ahora se usa la variable `DIRECT_API_PORT`.

**Verificar:**
```bash
# Las dos instancias deben estar en puertos diferentes
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### 3. NGINX no arranca

**Síntoma:** Error al arrancar NGINX o puerto 80 no responde.

**Causa:** NGINX no instalado, conflicto de puertos, o config incorrecta.

**Solución:**
```bash
# Instalar NGINX
sudo apt install nginx    # Ubuntu/Debian
brew install nginx        # macOS

# NGINX es opcional — las APIs funcionan sin él
# Accede directamente a:
curl http://localhost:8000/health  # API Directa #0
curl http://localhost:8001/health  # API Directa #1
```

Ver también: [docs/NGINX_TROUBLESHOOTING.md](NGINX_TROUBLESHOOTING.md)

### 4. Gateway Indirecto no arranca / crashea

**Síntoma:** Puerto 8080 no responde. Error en logs sobre conexión a RabbitMQ.

**Causa anterior:** El gateway no tenía retry logic y crasheaba si RabbitMQ no estaba listo.

**Solución (ya implementada):**
- El gateway ahora reintenta conectar a RabbitMQ hasta 10 veces con back-off exponencial
- Si RabbitMQ tarda en arrancar, el gateway espera automáticamente

**Si persiste:**
```bash
# Verificar RabbitMQ
docker ps | grep rabbitmq
curl http://localhost:15672  # Management UI (guest/guest)

# Ver log del gateway
cat logs/indirect_gateway.log

# Reiniciar solo la parte indirecta
./scripts/stop_all.sh
./scripts/start_all.sh
```

### 5. Workers no procesan mensajes

**Síntoma:** Las peticiones al gateway indirecto dan timeout (504).

**Causa:** Workers no conectados a RabbitMQ, o RabbitMQ caído.

**Solución:**
```bash
# Verificar workers corriendo
ps aux | grep "concert_ticketing.apps.worker"

# Ver logs
cat logs/worker_0.log

# Verificar RabbitMQ
docker compose -f tools/local_dev/docker-compose.yml ps
```

### 6. Redis no conecta

**Síntoma:** Error "Connection refused" al puerto 6379.

**Solución:**
```bash
# Levantar Redis
docker compose -f tools/local_dev/docker-compose.yml up -d redis

# Verificar
docker ps | grep redis
redis-cli ping   # debería devolver PONG
```

### 7. RabbitMQ no conecta

**Síntoma:** Error de conexión al puerto 5672.

**Solución:**
```bash
# Levantar RabbitMQ
docker compose -f tools/local_dev/docker-compose.yml up -d rabbitmq

# RabbitMQ tarda ~15-30s en arrancar completamente
# Verificar
docker ps | grep rabbitmq
curl -s http://localhost:15672  # Management UI
```

---

## Ejecución sin NGINX

NGINX es **opcional**. El sistema funciona perfectamente sin él:

| Con NGINX | Sin NGINX |
|-----------|-----------|
| `http://localhost/health` | `http://localhost:8000/health` |
| `http://localhost/buy/unnumbered` | `http://localhost:8000/buy/unnumbered` |
| Load balancing automático | Elige manualmente :8000 o :8001 |

Para benchmarks sin NGINX, usa la URL directa:
```bash
./scripts/run_direct_benchmark.sh benchmarks/input/unnumbered.txt http://localhost:8000
```

---

## Verificar que todo funciona

### Health checks manuales
```bash
# API Directa
curl -s http://localhost:8000/health | python3 -m json.tool
curl -s http://localhost:8001/health | python3 -m json.tool

# Gateway Indirecto
curl -s http://localhost:8080/health | python3 -m json.tool
```

### Compra de prueba
```bash
# Compra directa (unnumbered)
curl -s -X POST http://localhost:8000/buy/unnumbered \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test-001", "request_id": "req-test-001"}' | python3 -m json.tool

# Compra indirecta (unnumbered)
curl -s -X POST http://localhost:8080/buy/unnumbered \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test-002", "request_id": "req-test-002"}' | python3 -m json.tool
```

### Script automático
```bash
./scripts/verify_system.sh
```

---

## Reset completo

Si nada funciona, reset completo:
```bash
./scripts/stop_all.sh
./scripts/reset_system.sh
./scripts/start_all.sh
./scripts/verify_system.sh
```
