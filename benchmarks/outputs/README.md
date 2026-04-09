# Outputs de Benchmarks

Este directorio contiene los resultados finales consolidados de la practica.

## Estructura canonica

- `direct/`: benchmark base de la arquitectura directa
- `indirect/`: benchmark base de la arquitectura indirecta
- `scalability/latest/`: throughput frente a `1`, `2`, `4` y `8` workers
- `contention/latest/normal/`: escenario numerado normal
- `contention/latest/hotspot/`: escenario hotspot `80/5`
- `dynamic_scaling/latest/`: ejecucion con escalado en caliente
- `plots/`: graficos finales
- `reports/`: reporte HTML, Markdown y tabla resumen

Los resultados antiguos y experimentales se han eliminado para que este arbol
sea la unica fuente de verdad de la entrega.

Tambien se han retirado los logs de ejecucion para dejar aqui solo artefactos
finales de benchmark, graficos y reportes.
