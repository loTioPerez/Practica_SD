# Sistema Escalable de Adquisicion de Entradas

Implementacion de la practica de sistemas distribuidos con dos arquitecturas:

- **Directa**: cliente -> NGINX -> API REST -> Redis
- **Indirecta**: cliente -> gateway -> RabbitMQ -> workers -> Redis

El sistema soporta entradas no numeradas y numeradas, mantiene idempotencia por
`request_id` y compara rendimiento, contencion y escalabilidad bajo carga.

## Estructura util del repositorio

- `src/concert_ticketing/`: codigo de aplicacion, adaptadores y puntos de entrada
- `scripts/`: arranque, parada, benchmarks, reseteo y generacion de reportes
- `tools/local_dev/`: Docker Compose y `seed_state.py` para Redis y RabbitMQ
- `deploy/nginx/`: configuracion del balanceador REST
- `deploy/rabbitmq/`: artefactos auxiliares de RabbitMQ
- `benchmarks/input/`: benchmarks base entregados
- `benchmarks/generated/`: generacion del benchmark hotspot
- `benchmarks/outputs/`: resultados finales, graficos y reportes
- `docs/`: troubleshooting puntual

## Resultados finales

Los artefactos canonicos de la entrega estan en:

- `benchmarks/outputs/direct/`
- `benchmarks/outputs/indirect/`
- `benchmarks/outputs/scalability/latest/`
- `benchmarks/outputs/contention/latest/normal/`
- `benchmarks/outputs/contention/latest/hotspot/`
- `benchmarks/outputs/dynamic_scaling/latest/`
- `benchmarks/outputs/plots/`
- `benchmarks/outputs/reports/`

El reporte final generado queda en:

- `benchmarks/outputs/reports/benchmark_report.html`
- `benchmarks/outputs/reports/benchmark_report.md`
- `benchmarks/outputs/reports/summary_table.json`

## Ejecucion rapida

Desde la raiz del proyecto:

```bash
bash scripts/start_all.sh
bash scripts/verify_system.sh
bash scripts/stop_all.sh
```

Para regenerar el reporte a partir de los resultados de `benchmarks/outputs/`:

```bash
bash scripts/generate_report.sh benchmarks/outputs
```

## Notas

- Redis es el backend de consistencia del sistema.
- RabbitMQ se usa exclusivamente en la arquitectura indirecta.
- La practica se valido tanto en local como en un despliegue distribuido en LAN.
