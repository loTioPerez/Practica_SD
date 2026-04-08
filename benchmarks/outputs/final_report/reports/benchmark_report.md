# Benchmark Comparison Report

> Generado: 2026-04-08 21:21:54 UTC

## Executive Summary

### Key Findings

- **Direct architecture** achieves up to **1.6x** higher throughput than indirect.
- **2** benchmark scenarios evaluated.
- **Direct** scales from 1 to 8 workers with **1.0x** speedup.
- **Indirect** scales from 1 to 8 workers with **4.8x** speedup.
- **Direct** shows **43.2%** throughput degradation under high contention.
- **Indirect** shows **10.4%** throughput degradation under high contention.

### Recommendations

- Use **direct architecture** for lowest latency and highest throughput.
- Consider **indirect architecture** for decoupling and fault tolerance.
## Methodology

### Test Setup

- **System**: Concert Ticketing System (20,000 tickets default)
- **Architectures**: Direct (REST + NGINX) and Indirect (RabbitMQ + Workers)
- **Persistence**: Redis
- **Benchmark Tool**: Custom async HTTP benchmark runner (httpx)

### Workloads

| Workload | Description | Operations |
|----------|-------------|------------|
| Unnumbered | General admission tickets | 20,000 |
| Numbered | Specific seat purchases | 60,000 |
| Hotspot | High contention (80% to 5% of seats) | Variable |

### Configuration

- **Concurrency**: Configurable per benchmark execution
- **Timeout**: Configurable per benchmark execution
- **Workers tested**: Configurable; scalability experiments typically vary the number of workers
- **Note**: Refer to the raw summary files for the exact parameters used in each execution set

## Summary Table

| Benchmark | Architecture | Throughput (ops/s) | Latency Mean (ms) | P95 (ms) | P99 (ms) | Success Rate | Error Rate |
|-----------|-------------|-------------------|-------------------|----------|----------|-------------|------------|
| benchmark_unnumbered_20000 | direct | 97.05 | 101.48 | 106.65 | 298.08 | 100% | 0% |
| benchmark_unnumbered_20000 | indirect | 62.22 | 160.37 | 384.51 | 638.56 | 100% | 0% |
| benchmark_numbered_60000 | direct | 94.44 | 103.13 | 226.18 | 445.85 | 76.93% | 0% |
| benchmark_numbered_60000 | indirect | 59.18 | 168.64 | 382.37 | 1,116.41 | 76.93% | 0% |

## Direct Architecture Results

### benchmark_unnumbered_20000

| Metric | Value |
|--------|-------|
| Throughput | 97.05 ops/s |
| Latency (mean) | 101.48 ms |
| LATENCY P50 | 42.29 ms |
| LATENCY P95 | 106.65 ms |
| LATENCY P99 | 298.08 ms |
| Accepted | 20,000 |
| Rejected | 0 |
| Success Rate | 100% |

### benchmark_numbered_60000

| Metric | Value |
|--------|-------|
| Throughput | 94.44 ops/s |
| Latency (mean) | 103.13 ms |
| LATENCY P50 | 75.70 ms |
| LATENCY P95 | 226.18 ms |
| LATENCY P99 | 445.85 ms |
| Accepted | 20,000 |
| Rejected | 5,997 |
| Success Rate | 76.93% |

## Indirect Architecture Results

### benchmark_unnumbered_20000

| Metric | Value |
|--------|-------|
| Throughput | 62.22 ops/s |
| Latency (mean) | 160.37 ms |
| LATENCY P50 | 123.83 ms |
| LATENCY P95 | 384.51 ms |
| LATENCY P99 | 638.56 ms |
| Accepted | 20,000 |
| Rejected | 0 |
| Success Rate | 100% |

### benchmark_numbered_60000

| Metric | Value |
|--------|-------|
| Throughput | 59.18 ops/s |
| Latency (mean) | 168.64 ms |
| LATENCY P50 | 121.26 ms |
| LATENCY P95 | 382.37 ms |
| LATENCY P99 | 1,116.41 ms |
| Accepted | 20,000 |
| Rejected | 5,997 |
| Success Rate | 76.93% |

## Comparative Analysis

### Direct vs Indirect

| Benchmark | Direct Throughput | Indirect Throughput | Ratio | Direct Latency | Indirect Latency |
|-----------|------------------|--------------------|---------|-----------------|--------------------|
| benchmark_unnumbered_20000 | 97.05 | 62.22 | 1.5598 | 101.48ms | 160.37ms |
| benchmark_numbered_60000 | 94.44 | 59.18 | 1.5957 | 103.13ms | 168.64ms |

## Scalability Analysis

### Direct Scalability

| Workers | Throughput (ops/s) | Latency Mean (ms) | Success Rate |
|---------|-------------------|-------------------|-------------|
| 1 | 102.73 | 476.31 | 100% |
| 2 | 118.53 | 83.49 | 100% |
| 4 | 100.92 | 98.08 | 100% |
| 8 | 99.05 | 99.99 | 100% |

### Indirect Scalability

| Workers | Throughput (ops/s) | Latency Mean (ms) | Success Rate |
|---------|-------------------|-------------------|-------------|
| 1 | 20.78 | 2,401.52 | 100% |
| 2 | 65.79 | 151.73 | 100% |
| 4 | 91.92 | 108.53 | 100% |
| 8 | 98.87 | 100.89 | 100% |

## Contention Analysis

### Normal vs High Contention

| Architecture | Scenario | Throughput (ops/s) | Latency Mean (ms) | Degradation |
|-------------|----------|-------------------|-------------------|-------------|
| Direct | Normal | 184.24 | 52.97 | - |
| Direct | Hotspot | 104.70 | 94.26 | - |
| **Direct** | **Degradation** | - | - | **43.2%** |
| Indirect | Normal | 87.84 | 113.60 | - |
| Indirect | Hotspot | 78.67 | 126.90 | - |
| **Indirect** | **Degradation** | - | - | **10.4%** |

## Plots

### Throughput Comparison

![Throughput Comparison](plots\throughput_comparison.png)

### Latency Distribution

![Latency Distribution](plots\latency_distribution.png)

### Scalability

![Scalability](plots\scalability.png)

### Ticket Type Comparison

![Ticket Type Comparison](plots\ticket_type_comparison.png)

### Contention Impact

![Contention Impact](plots\contention_impact.png)

### Success Failure Breakdown

![Success Failure Breakdown](plots\success_failure_breakdown.png)

## Conclusions

### Tradeoffs

- **Direct Architecture**: Lower latency, simpler deployment, but tightly coupled.
- **Indirect Architecture**: Better fault tolerance, decoupled components, but higher latency.

### Best Use Cases

- **Direct**: Low-latency requirements, simple deployments, small to medium scale.
- **Indirect**: Large scale, need for fault tolerance, asynchronous processing requirements.

### Recommendations

1. Direct architecture outperforms indirect in 2/2 scenarios.
2. Consider indirect architecture for production workloads requiring fault tolerance.
3. Scale workers based on expected load using the scalability analysis.
4. Monitor contention patterns in production to detect hotspot scenarios.