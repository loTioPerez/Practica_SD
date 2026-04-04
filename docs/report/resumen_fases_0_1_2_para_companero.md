# Resumen de estado de las Fases 0, 1 y 2

Este documento resume el estado real actual del repositorio tras revisar y
completar lo que faltaba para las fases 0, 1 y 2. La referencia principal ha
sido siempre el codigo existente del repo, no solo la planificacion inicial.

## Veredicto general

- Fase 0: cerrada a nivel de repositorio y setup local minimo.
- Fase 1: cerrada como base funcional actual del sistema.
- Fase 2: cerrada a nivel de implementacion local de la arquitectura directa.

Matiz importante:

- El cierre de las fases 0 y 2 significa que ya no quedan placeholders
  relevantes en setup local, API REST directa, NGINX ni benchmark runner
  directo.
- Sigue siendo recomendable hacer una validacion end-to-end completa con
  dependencias instaladas, Redis/RabbitMQ levantados y NGINX ejecutandose, pero
  eso ya no es una carencia de implementacion sino de prueba final de entorno.

## Fase 0: estado real

La Fase 0 estaba definida como setup local con `docker-compose`, dependencias,
YAMLs y `.env.example`.

Estado actual:

- `pyproject.toml` ya incluye:
  - `fastapi`
  - `uvicorn`
  - `redis`
  - `pika`
  - `httpx`
  - `PyYAML`
  - `pydantic`
- `tools/local_dev/docker-compose.yml` ya levanta:
  - `redis:7-alpine`
  - `rabbitmq:3-management-alpine`
  - puertos `6379`, `5672` y `15672`
- `.env.example` ya contiene variables comunes, Redis, RabbitMQ, API directa y
  benchmark runner.
- `config/common.yaml`, `config/redis.yaml`, `config/rabbitmq.yaml`,
  `config/direct.yaml`, `config/nginx.yaml` y `config/benchmark.yaml` ya tienen
  contenido base util.
- `tools/local_dev/seed_state.py` ya permite resetear e inicializar el estado
  local de Redis.

Conclusion:

- La Fase 0 puede darse por cerrada en el estado actual del repo.

## Fase 1: estado real

La Fase 1 queda validada como base funcional actual del proyecto.

### Dominio y servicios

Ya existen y tienen implementacion real:

- `src/concert_ticketing/core/domain/enums.py`
- `src/concert_ticketing/core/domain/models.py`
- `src/concert_ticketing/core/services/idempotency_service.py`
- `src/concert_ticketing/core/services/numbered_service.py`
- `src/concert_ticketing/core/services/unnumbered_service.py`
- `src/concert_ticketing/core/services/validation_service.py`
- `src/concert_ticketing/core/services/purchase_service.py`

`PurchaseService` orquesta ahora:

- compra no numerada
- compra numerada
- consulta por `request_id`
- consulta de inventario
- consulta de asientos
- consulta de compras por cliente
- inicializacion y reset de inventario

### Puertos del core

Ya existen:

- `src/concert_ticketing/core/ports/inventory_repository.py`
- `src/concert_ticketing/core/ports/idempotency_repository.py`
- `src/concert_ticketing/core/ports/result_repository.py`

### Persistencia Redis

Ya existe implementacion real en:

- `src/concert_ticketing/adapters/persistence/redis/connection.py`
- `src/concert_ticketing/adapters/persistence/redis/key_schema.py`
- `src/concert_ticketing/adapters/persistence/redis/repositories.py`

Importante:

- La atomicidad real actual no usa Lua.
- La estrategia implementada es `WATCH/MULTI/EXEC`.
- Esto contradice la planificacion original del PDF, pero se ha priorizado el
  estado real del repositorio.

### Shared

Ya existen y tienen contenido real:

- `src/concert_ticketing/shared/config.py`
- `src/concert_ticketing/shared/constants.py`
- `src/concert_ticketing/shared/exceptions.py`
- `src/concert_ticketing/shared/health.py`
- `src/concert_ticketing/shared/logger.py`
- `src/concert_ticketing/shared/serialization.py`

### Tests reales

El plan mencionaba `tests/test_core_logic.py`, pero esa ruta no existe en el
repo actual.

Lo que hay de verdad ahora es:

- `tests/unit/test_purchase_service.py`
- `tests/unit/test_benchmark_parser.py`
- `tests/unit/test_benchmark_reporting.py`
- varios tests unitarios e integration/smoke/stress que siguen como base futura

En este estado se han verificado correctamente 10 tests unitarios.

### Conclusion Fase 1

- La Fase 1 puede darse por buena como base funcional actual.
- Cumple su objetivo de dejar core + Redis operativo.

## Fase 2: estado real

La Fase 2 estaba dividida en:

- 2A API REST
- 2B NGINX Load Balancer
- 2C Benchmark Runner

### Fase 2A: API REST

Esta parte esta implementada.

Archivos completados:

- `src/concert_ticketing/adapters/api/rest/schemas.py`
- `src/concert_ticketing/adapters/api/rest/routes.py`
- `src/concert_ticketing/adapters/api/rest/dependencies.py`
- `src/concert_ticketing/adapters/api/rest/middleware.py`
- `src/concert_ticketing/adapters/api/rest/app_factory.py`
- `src/concert_ticketing/apps/direct_api/main.py`

Endpoints disponibles:

- `GET /health`
- `POST /buy/unnumbered`
- `POST /buy/numbered`
- `GET /requests/{request_id}`
- `GET /results/{request_id}`
- `GET /stats`
- `GET /inventory/{ticket_type}`
- `GET /seats/{seat_id}`
- `GET /clients/{client_id}/purchases`

Notas:

- El wiring REST reutiliza el core actual y los repositorios Redis actuales.
- No se ha rehecho el core ni se han cambiado nombres base del repositorio.
- El middleware es ligero: logging, tiempo por request y captura minima de
  errores.

### Fase 2B: NGINX

Esta parte ya no esta en placeholder.

Archivos completados:

- `deploy/nginx/nginx.conf`
- `deploy/nginx/upstream.conf`

Configuracion actual:

- upstream `direct_backend`
- estrategia `least_conn`
- dos backends ejemplo en `127.0.0.1:8000` y `127.0.0.1:8001`
- proxy de `/health` y del resto del trafico HTTP

Conclusion:

- La parte 2B queda cubierta a nivel de configuracion local.

### Fase 2C: Benchmark Runner

Esta parte tambien queda implementada.

Archivos completados:

- `src/concert_ticketing/apps/benchmark_runner/parser.py`
- `src/concert_ticketing/apps/benchmark_runner/main.py`
- `src/concert_ticketing/apps/benchmark_runner/reporting.py`
- `scripts/run_direct_benchmark.sh`

Capacidades actuales:

- leer benchmarks numerados y no numerados
- mapear cada operacion al endpoint REST correcto
- lanzar carga concurrente con `httpx.AsyncClient`
- recoger tiempos y respuestas HTTP
- calcular resumen con throughput, latencia media, aceptadas, rechazadas,
  duplicadas y errores de transporte
- exportar resumen en JSON y resultados en JSON Lines

### Scripts operativos asociados

Tambien se ha completado:

- `scripts/start_direct_stack.sh`

Este script:

- levanta Redis y RabbitMQ con `docker compose`
- inicializa el estado base de Redis
- deja indicada la forma de arrancar la API directa

### Conclusion Fase 2

- La Fase 2 puede darse por cerrada a nivel de implementacion local.
- La arquitectura directa ya no depende de placeholders relevantes.

## Resumen final

Mi visto bueno actual es este:

- Fase 0: cerrada
- Fase 1: cerrada
- Fase 2: cerrada

## Pendiente real a partir de aqui

Lo siguiente ya no pertenece al cierre de 0, 1 y 2, sino a fases posteriores:

- Fase 3 RabbitMQ
- Fase 4 benchmarks comparativos y analisis completo
- Fase 5 requisitos adicionales
- Fase 6 despliegue AWS
- Fase 7 memoria final

## Recomendacion inmediata

Antes de pasar a Fase 3, conviene hacer una validacion local corta de la
arquitectura directa completa:

- levantar `docker-compose`
- inicializar Redis
- arrancar una o dos instancias de API directa
- poner NGINX delante
- lanzar un benchmark pequeño

Eso no cambia el estado de implementacion, pero ayuda a detectar fallos de
integracion antes de abrir RabbitMQ.
