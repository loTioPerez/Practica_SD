# Diseno de Consistencia

Este documento recogera las decisiones de consistencia, atomicidad,
idempotencia y tratamiento de contencion.

Decision actual del esqueleto:

- Redis sera la primera opcion de implementacion.
- La idempotencia se apoyara en `request_id`.
- No se mantiene por ahora una segunda implementacion de persistencia para no
  dispersar esfuerzo antes de validar la correcta.
