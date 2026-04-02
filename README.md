# Sistema Escalable de Adquisicion de Entradas

Esqueleto inicial del proyecto para la practica de sistemas distribuidos.

En este punto solo se ha definido la estructura base del repositorio. No hay
logica de negocio implementada todavia.

## Estructura elegida

El repositorio combina dos objetivos:

- un nucleo compartido para no duplicar la logica de venta
- una organizacion fuerte para despliegue, benchmarks, analisis y memoria

Las piezas principales son:

- `src/concert_ticketing/core/`: dominio, servicios y puertos
- `src/concert_ticketing/adapters/`: REST, RabbitMQ, persistencia y observabilidad
- `src/concert_ticketing/apps/`: puntos de entrada ejecutables
- `docs/`: arquitectura, runbooks y material de la memoria
- `deploy/`: AWS, systemd, NGINX y RabbitMQ
- `benchmarks/`: entradas originales, escenarios generados y salidas
- `metrics/` y `logs/`: artefactos de ejecucion
- `tests/`: pruebas unitarias, de integracion, smoke y stress

## Decision arquitectonica

La comparacion entre arquitectura directa e indirecta debe hacerse sobre la
misma logica de negocio. Por eso se mantiene un paquete Python comun,
`concert_ticketing`, y se separan claramente:

- `core/` para las reglas del sistema
- `ports/` para las interfaces de acceso a infraestructura
- `adapters/` para las implementaciones concretas
- `apps/` para ensamblar cada servicio ejecutable

## Simplificacion aplicada

Para que el proyecto sea mas facil de entender y mantener desde el principio,
la estructura se ha simplificado con estos criterios:

- Redis queda como backend principal de consistencia.
- PostgreSQL se elimina por ahora para no abrir una segunda linea tecnica.
- El dominio se mantiene ligero: `models.py` y `enums.py` en vez de una
  separacion mas ceremoniosa.
- La mensajeria RabbitMQ se trata como infraestructura de entrada, no como una
  abstraccion adicional dentro del core.
- La API REST construye la aplicacion mediante `app_factory.py` para evitar
  duplicidad de `main.py`.

## Estado actual

- La estructura del proyecto ya esta preparada.
- La documentacion base se ha dejado en espanol.
- Los archivos son placeholders y serviran como mapa para el desarrollo.
