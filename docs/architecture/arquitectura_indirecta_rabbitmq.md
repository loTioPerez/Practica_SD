# Arquitectura Indirecta RabbitMQ

Aqui se documentara la version basada en colas, productores y workers
asincronos coordinados mediante RabbitMQ.

Responsabilidad prevista:

- `indirect_gateway/` sera el punto unico de entrada de esta arquitectura.
- Su trabajo sera recibir solicitudes y publicarlas en RabbitMQ.
- `worker/` sera quien procese realmente la compra usando el core compartido.
- `benchmark_runner/` solo reproducira cargas de prueba; no sustituye al
  gateway ni contiene logica de negocio.
