# Troubleshooting

Guia corta para diagnosticar los problemas mas comunes al arrancar y validar el
sistema.

## Comprobacion rapida

```bash
bash scripts/verify_system.sh
```

Si este script falla, revisa primero infraestructura, despues servicios Python y
por ultimo NGINX.

## Redis o RabbitMQ no levantan

```bash
docker compose -f tools/local_dev/docker-compose.yml ps
docker compose -f tools/local_dev/docker-compose.yml up -d
```

Si RabbitMQ tarda en quedar sano, espera unos segundos antes de arrancar el
gateway o los workers.

## Las APIs directas no responden

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

Si alguna no responde, revisa:

- `logs/direct_api_0.log`
- `logs/direct_api_1.log`

## El gateway indirecto no responde

```bash
curl http://localhost:8080/health
```

Si falla, revisa:

- `logs/indirect_gateway.log`
- conectividad con Redis
- conectividad con RabbitMQ

## Los workers no consumen mensajes

Revisa los logs de workers activos:

- `logs/worker_0.log`
- `logs/worker_1.log`
- `logs/worker_2.log`

Lo mas habitual es que RabbitMQ aun no estuviera listo o que se hayan arrancado
con variables de entorno incorrectas.

## Estado incoherente tras varias pruebas

```bash
bash scripts/reset_state.sh
```

Si necesitas limpieza mas agresiva:

```bash
bash scripts/reset_system.sh
```

## Ultimo recurso

```bash
bash scripts/stop_all.sh
bash scripts/start_all.sh
bash scripts/verify_system.sh
```
