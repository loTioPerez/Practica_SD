# Benchmark Comparison Report

> Generado: 2026-04-06 19:40:29 UTC

## Executive Summary

### Key Findings

- **Indirect architecture** achieves up to **3.8x** higher throughput than direct.
- **2** benchmark scenarios evaluated.
- **Direct** scales from 1 to 8 workers with **0.9x** speedup.
- **Indirect** scales from 1 to 8 workers with **0.6x** speedup.

### Recommendations

- **Indirect architecture** provides better throughput in tested scenarios.
- **Direct architecture** may still be preferred for simplicity.
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

- **Concurrency**: 50 concurrent requests (configurable)
- **Timeout**: 60 seconds per request
- **Workers tested**: 1, 2, 4, 8

## Summary Table

| Benchmark | Architecture | Throughput (ops/s) | Latency Mean (ms) | P95 (ms) | P99 (ms) | Success Rate | Error Rate |
|-----------|-------------|-------------------|-------------------|----------|----------|-------------|------------|
| benchmark_unnumbered_20000 | direct | 3,815.58 | 489.16 | 1,431.77 | 2,206.01 | 100% | 0% |
| benchmark_unnumbered_20000 | indirect | 14,421.85 | 801.00 | 820.57 | 828.74 | 100% | 0% |
| benchmark_numbered_60000 | direct | 3,201.82 | 476.98 | 1,430.02 | 2,282.81 | 76.93% | 0% |
| benchmark_numbered_60000 | indirect | 19,185.47 | 800.68 | 819.92 | 827.72 | 76.93% | 0% |

## Direct Architecture Results

### benchmark_unnumbered_20000

| Metric | Value |
|--------|-------|
| Throughput | 3,815.58 ops/s |
| Latency (mean) | 489.16 ms |
| LATENCY P50 | 334.06 ms |
| LATENCY P95 | 1,431.77 ms |
| LATENCY P99 | 2,206.01 ms |
| Accepted | 20,000 |
| Rejected | 0 |
| Success Rate | 100% |

### benchmark_numbered_60000

| Metric | Value |
|--------|-------|
| Throughput | 3,201.82 ops/s |
| Latency (mean) | 476.98 ms |
| LATENCY P50 | 309.20 ms |
| LATENCY P95 | 1,430.02 ms |
| LATENCY P99 | 2,282.81 ms |
| Accepted | 20,000 |
| Rejected | 5,997 |
| Success Rate | 76.93% |

## Indirect Architecture Results

### benchmark_unnumbered_20000

| Metric | Value |
|--------|-------|
| Throughput | 14,421.85 ops/s |
| Latency (mean) | 801.00 ms |
| LATENCY P50 | 805.47 ms |
| LATENCY P95 | 820.57 ms |
| LATENCY P99 | 828.74 ms |
| Accepted | 20,000 |
| Rejected | 0 |
| Success Rate | 100% |

### benchmark_numbered_60000

| Metric | Value |
|--------|-------|
| Throughput | 19,185.47 ops/s |
| Latency (mean) | 800.68 ms |
| LATENCY P50 | 809.53 ms |
| LATENCY P95 | 819.92 ms |
| LATENCY P99 | 827.72 ms |
| Accepted | 20,000 |
| Rejected | 5,997 |
| Success Rate | 76.93% |

## Comparative Analysis

### Direct vs Indirect

| Benchmark | Direct Throughput | Indirect Throughput | Ratio | Direct Latency | Indirect Latency |
|-----------|------------------|--------------------|---------|-----------------|--------------------|
| benchmark_unnumbered_20000 | 3,815.58 | 14,421.85 | 0.2646 | 489.16ms | 801.00ms |
| benchmark_numbered_60000 | 3,201.82 | 19,185.47 | 0.1669 | 476.98ms | 800.68ms |

## Scalability Analysis

### Direct Scalability

| Workers | Throughput (ops/s) | Latency Mean (ms) | Success Rate |
|---------|-------------------|-------------------|-------------|
| 1 | 4,001.27 | 476.31 | 100% |
| 2 | 4,398.48 | 469.37 | 100% |
| 4 | 4,735.81 | 477.94 | 100% |
| 8 | 3,691.91 | 477.80 | 100% |

### Indirect Scalability

| Workers | Throughput (ops/s) | Latency Mean (ms) | Success Rate |
|---------|-------------------|-------------------|-------------|
| 1 | 6,750.19 | 2,401.52 | 100% |
| 2 | 11,143.02 | 1,202.57 | 100% |
| 4 | 17,455.11 | 599.97 | 100% |
| 8 | 3,902.39 | 512.73 | 100% |

## Plots

### Throughput Comparison

![Throughput Comparison](plots\throughput_comparison.png)

### Latency Distribution

![Latency Distribution](plots\latency_distribution.png)

### Scalability

![Scalability](plots\scalability.png)

### Ticket Type Comparison

![Ticket Type Comparison](plots\ticket_type_comparison.png)

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

1. Indirect architecture outperforms direct in 2/2 scenarios.
2. Consider direct architecture for simplicity in small deployments.
3. Scale workers based on expected load using the scalability analysis.
4. Monitor contention patterns in production to detect hotspot scenarios.