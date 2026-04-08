# Benchmark Comparison Report

> Generado: 2026-04-08 17:54:58 UTC

## Executive Summary

### Key Findings

- **Direct architecture** achieves up to **2.7x** higher throughput than indirect.
- **2** benchmark scenarios evaluated.

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

- **Concurrency**: 50 concurrent requests (configurable)
- **Timeout**: 60 seconds per request
- **Workers tested**: 1, 2, 4, 8

## Summary Table

| Benchmark | Architecture | Throughput (ops/s) | Latency Mean (ms) | P95 (ms) | P99 (ms) | Success Rate | Error Rate |
|-----------|-------------|-------------------|-------------------|----------|----------|-------------|------------|
| benchmark_unnumbered_20000 | direct | 123.16 | 79.74 | 81.60 | 178.37 | 100% | 0% |
| benchmark_unnumbered_20000 | indirect | 98.75 | 100.63 | 264.79 | 382.90 | 100% | 0% |
| benchmark_numbered_60000 | direct | 171.40 | 56.51 | 121.36 | 203.07 | 76.93% | 0% |
| benchmark_numbered_60000 | indirect | 64.00 | 155.72 | 434.26 | 743.87 | 76.93% | 0% |

## Direct Architecture Results

### benchmark_unnumbered_20000

| Metric | Value |
|--------|-------|
| Throughput | 123.16 ops/s |
| Latency (mean) | 79.74 ms |
| LATENCY P50 | 32.94 ms |
| LATENCY P95 | 81.60 ms |
| LATENCY P99 | 178.37 ms |
| Accepted | 20,000 |
| Rejected | 0 |
| Success Rate | 100% |

### benchmark_numbered_60000

| Metric | Value |
|--------|-------|
| Throughput | 171.40 ops/s |
| Latency (mean) | 56.51 ms |
| LATENCY P50 | 46.09 ms |
| LATENCY P95 | 121.36 ms |
| LATENCY P99 | 203.07 ms |
| Accepted | 20,000 |
| Rejected | 5,997 |
| Success Rate | 76.93% |

## Indirect Architecture Results

### benchmark_unnumbered_20000

| Metric | Value |
|--------|-------|
| Throughput | 98.75 ops/s |
| Latency (mean) | 100.63 ms |
| LATENCY P50 | 81.00 ms |
| LATENCY P95 | 264.79 ms |
| LATENCY P99 | 382.90 ms |
| Accepted | 20,000 |
| Rejected | 0 |
| Success Rate | 100% |

### benchmark_numbered_60000

| Metric | Value |
|--------|-------|
| Throughput | 64.00 ops/s |
| Latency (mean) | 155.72 ms |
| LATENCY P50 | 104.57 ms |
| LATENCY P95 | 434.26 ms |
| LATENCY P99 | 743.87 ms |
| Accepted | 20,000 |
| Rejected | 5,997 |
| Success Rate | 76.93% |

## Comparative Analysis

### Direct vs Indirect

| Benchmark | Direct Throughput | Indirect Throughput | Ratio | Direct Latency | Indirect Latency |
|-----------|------------------|--------------------|---------|-----------------|--------------------|
| benchmark_unnumbered_20000 | 123.16 | 98.75 | 1.2473 | 79.74ms | 100.63ms |
| benchmark_numbered_60000 | 171.40 | 64.00 | 2.6782 | 56.51ms | 155.72ms |

## Plots

### Throughput Comparison

![Throughput Comparison](plots\throughput_comparison.png)

### Latency Distribution

![Latency Distribution](plots\latency_distribution.png)

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

1. Direct architecture outperforms indirect in 2/2 scenarios.
2. Consider indirect architecture for production workloads requiring fault tolerance.
3. Scale workers based on expected load using the scalability analysis.
4. Monitor contention patterns in production to detect hotspot scenarios.