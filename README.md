# Scalable Concert Ticket Acquisition System

Python project skeleton for the distributed systems assignment.

At this stage the repository only contains the initial structure of the
project. No business logic has been implemented yet.

## Proposed Structure

```text
Practica_SD/
  benchmarks/
  deploy/
    aws/
    docker/
    nginx/
    systemd/
  docs/
    diagrams/
    results/
  scripts/
  src/
    concert_ticketing/
      adapters/
      apps/
      config/
      core/
  tests/
    integration/
    stress/
    unit/
```

## Main Design Decision

The repository is organized around one shared Python package,
`concert_ticketing`, so both architectures can reuse the same core
ticket-purchase logic.

- `core/`: domain models, application use cases, and ports/interfaces
- `adapters/`: REST, RabbitMQ, persistence, and metrics integrations
- `apps/`: runnable entry points for the direct API, indirect gateway,
  asynchronous worker, and benchmark runner
- `deploy/`: deployment artifacts for AWS VMs and local orchestration
- `tests/`: unit, integration, and stress test suites
- `docs/`: diagrams, benchmark outputs, and report material

## Notes

- The benchmark files are kept under `benchmarks/`.
- The project uses a `src/` layout so imports stay explicit and clean.
- Placeholder modules have been created to define the future code map
  without implementing behavior yet.
