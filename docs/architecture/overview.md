# Vision General

Este documento resumira la arquitectura global del sistema y la relacion entre
el nucleo compartido, la arquitectura directa y la arquitectura indirecta.

La version actual del esqueleto prioriza simplicidad:

- Redis es el backend previsto inicialmente para consistencia.
- RabbitMQ se usa solo en la arquitectura indirecta.
- El core no conoce detalles de HTTP, Redis ni RabbitMQ.
- Se ha evitado introducir componentes experimentales que no sean necesarios
  para cumplir el enunciado.
