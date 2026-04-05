# Benchmarks - Concert Ticketing System

## Descripcion

Este directorio contiene todo lo necesario para ejecutar, analizar y
reportar benchmarks comparativos del sistema de venta de entradas.

## Estructura

```
benchmarks/
├── input/                          # Ficheros de carga benchmark
│   ├── benchmark_unnumbered_20000.txt
│   └── benchmark_numbered_60000.txt
├── generated/                      # Benchmarks generados (hotspot)
│   └── generate_hotspot.py
├── outputs/                        # Resultados de benchmarks
│   ├── direct/                     # Resultados arquitectura directa
│   ├── indirect/                   # Resultados arquitectura indirecta
│   ├── comparative/                # Benchmarks comparativos
│   ├── scalability/                # Tests de escalabilidad
│   ├── contention/                 # Tests de contencion
│   ├── plots/                      # Graficos generados
│   └── reports/                    # Reportes (MD + HTML)
└── summaries/                      # Resumenes de ejecuciones
```

## Como ejecutar benchmarks

### Prerequisitos

1. Docker y Docker Compose instalados
2. Dependencias Python instaladas: `pip install -e .`
3. Infraestructura levantada (Redis, RabbitMQ)

### 1. Benchmarks individuales

```bash
# Arquitectura directa
./scripts/run_direct_benchmark.sh

# Arquitectura indirecta
./scripts/run_indirect_benchmark.sh
```

### 2. Benchmarks comparativos

Ejecuta benchmarks en ambas arquitecturas con multiples configuraciones:

```bash
./scripts/run_comparative_benchmarks.sh
```

Variables de entorno configurables:
- `DIRECT_BASE_URL` - URL base directa (default: http://localhost)
- `INDIRECT_BASE_URL` - URL base indirecta (default: http://localhost:8080)
- `BENCHMARK_CONCURRENCY` - Concurrencia (default: 50)
- `WORKERS_LIST` - Workers a probar (default: "1 2 4 8")

### 3. Test de escalabilidad

Mide throughput vs numero de workers:

```bash
./scripts/run_scalability_test.sh
```

### 4. Test de contencion

Compara rendimiento normal vs alta contencion:

```bash
./scripts/run_contention_test.sh
```

### 5. Pipeline completo

Ejecuta todo el pipeline: benchmarks + analisis + graficos + reporte:

```bash
./scripts/run_full_analysis.sh
```

## Como generar reportes

Si ya tienes resultados de benchmarks:

```bash
./scripts/generate_report.sh [directorio_outputs]
```

Genera:
- `outputs/reports/benchmark_report.md` - Reporte en Markdown
- `outputs/reports/benchmark_report.html` - Reporte en HTML
- `outputs/reports/summary_table.json` - Tabla resumen en JSON
- `outputs/plots/*.png` - Graficos PNG

## Graficos generados

| Grafico | Descripcion |
|---------|-------------|
| `throughput_comparison.png` | Barras comparando throughput Direct vs Indirect |
| `latency_distribution.png` | Histogramas de distribucion de latencias |
| `scalability.png` | Lineas de throughput vs numero de workers |
| `ticket_type_comparison.png` | Comparacion unnumbered vs numbered |
| `contention_impact.png` | Impacto de contencion en rendimiento |
| `success_failure_breakdown.png` | Desglose de operaciones por resultado |

## Metricas medidas

- **Throughput**: Operaciones por segundo
- **Latencia**: Media, P50, P95, P99
- **Tiempo total**: Duracion total de ejecucion
- **Tasa de exito**: Porcentaje de operaciones aceptadas
- **Tasa de error**: Porcentaje de errores de transporte
- **Duplicados**: Operaciones detectadas como duplicadas (idempotencia)

## Interpretacion de resultados

### Throughput
- **> 5000 ops/s**: Excelente
- **2000-5000 ops/s**: Bueno
- **500-2000 ops/s**: Aceptable
- **< 500 ops/s**: Bajo rendimiento

### Latencia P99
- **< 50ms**: Excelente
- **50-100ms**: Bueno
- **100-500ms**: Aceptable
- **> 500ms**: Alto

### Escalabilidad
- Escalado lineal ideal: throughput se multiplica proporcionalmente
- La eficiencia de escalado se calcula como: speedup_real / speedup_ideal

## Troubleshooting

### "Connection refused"
- Verificar que los servicios estan levantados
- Comprobar URLs base en variables de entorno

### Throughput bajo
- Aumentar concurrencia
- Verificar recursos del sistema (CPU, memoria)
- Comprobar que Redis no es el cuello de botella

### Graficos vacios
- Verificar que existen ficheros *_summary.json y *_results.jsonl
- Comprobar permisos de escritura en directorio de outputs

### Error de dependencias
```bash
pip install matplotlib numpy pandas
```
