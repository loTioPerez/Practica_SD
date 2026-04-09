# Benchmarks

Este directorio agrupa los benchmarks de entrada, el generador del escenario
hotspot y los resultados finales usados en la entrega.

## Estructura

```text
benchmarks/
|-- input/
|   |-- benchmark_unnumbered_20000.txt
|   `-- benchmark_numbered_60000.txt
|-- generated/
|   |-- generate_hotspot.py
|   `-- hotspot_benchmark.txt
`-- outputs/
    |-- direct/
    |-- indirect/
    |-- scalability/latest/
    |-- contention/latest/normal/
    |-- contention/latest/hotspot/
    |-- dynamic_scaling/latest/
    |-- plots/
    `-- reports/
```

## Nota sobre `benchmark_numbered_60000.txt`

El nombre historico del fichero se mantiene, pero el benchmark numerado usado
realmente contiene `25 997` operaciones validas:

- `20 000` aceptadas
- `5 997` rechazadas por `seat_already_sold`

## Escenarios cubiertos

- **Direct vs indirect**: `outputs/direct/` y `outputs/indirect/`
- **Escalabilidad**: `outputs/scalability/latest/`
- **Contencion normal**: `outputs/contention/latest/normal/`
- **Hotspot**: `outputs/contention/latest/hotspot/`
- **Dynamic scaling**: `outputs/dynamic_scaling/latest/`

## Reporte final

El reporte agregado y los graficos de la entrega estan en:

- `outputs/reports/benchmark_report.html`
- `outputs/reports/benchmark_report.md`
- `outputs/reports/summary_table.json`
- `outputs/plots/`

## Regeneracion del reporte

Desde la raiz del proyecto:

```bash
bash scripts/generate_report.sh benchmarks/outputs
```
