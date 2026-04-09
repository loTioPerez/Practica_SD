# RabbitMQ

Artefactos auxiliares para la arquitectura indirecta basada en colas.

## Ficheros relevantes

- `definitions.json`: definiciones exportables de RabbitMQ usadas como referencia

RabbitMQ es el middleware obligatorio de la arquitectura indirecta: el gateway
publica solicitudes de compra y los workers las consumen de forma asincrona.
