# Scripts

Scripts auxiliares para arrancar el sistema, verificarlo, ejecutar benchmarks y
generar el reporte final.

## Arranque y parada

- `_common.sh`: funciones compartidas para logs, puertos, PIDs y utilidades
- `start_all.sh`: levanta Redis, RabbitMQ, APIs directas, NGINX, gateway y workers
- `start_direct_only.sh`: levanta solo la arquitectura directa
- `start_indirect_only.sh`: levanta solo la arquitectura indirecta
- `start_without_nginx.sh`: arranca el sistema sin balanceador NGINX
- `stop_all.sh`: detiene todos los procesos gestionados por scripts
- `status.sh`: muestra estado de puertos, procesos y health checks
- `logs.sh`: consulta logs de servicios arrancados manualmente

## Estado y reseteo

- `init_state.sh`: inicializa el estado base en Redis
- `reset_state.sh`: resetea solo Redis y reinyecta el estado inicial
- `reset_system.sh`: reseteo mas completo de infraestructura y logs
- `verify_system.sh`: comprobacion operativa de servicios
- `verify_correctness.sh`: validacion de resultados de benchmark

## Benchmarks y analisis

- `run_direct_benchmark.sh`: benchmark base de la arquitectura directa
- `run_indirect_benchmark.sh`: benchmark base de la arquitectura indirecta
- `run_comparative_benchmarks.sh`: comparativa directa vs indirecta
- `run_scalability_test.sh`: pruebas de escalabilidad con distinto numero de workers
- `run_contention_test.sh`: escenario numerado normal y comparativa de contencion
- `run_hotspot_benchmark.sh`: escenario `80/5` de alta contencion
- `run_dynamic_scaling_test.sh`: benchmark con cambio de workers en caliente
- `run_full_analysis.sh`: pipeline de benchmarks y reporte
- `generate_report.sh`: genera `reports/` y `plots/` desde `benchmarks/outputs`

## Escalado manual

- `scale_workers_up.sh`: sube workers de la arquitectura indirecta
- `scale_workers_down.sh`: baja workers de la arquitectura indirecta

Estos dos scripts se conservan porque siguen siendo utiles para el escenario de
dynamic scaling, aunque en LAN tambien se haya validado el escalado manualmente.
