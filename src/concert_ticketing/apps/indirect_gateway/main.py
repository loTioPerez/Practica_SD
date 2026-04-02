"""Punto de entrada del servicio de acceso a la arquitectura indirecta.

Este proceso recibe solicitudes y las publica en RabbitMQ. No ejecuta la
logica de compra; esa responsabilidad pertenece a los workers.
"""
