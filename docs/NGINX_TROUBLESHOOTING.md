# NGINX Troubleshooting

NGINX es el balanceador de la arquitectura directa y el punto unico de entrada
esperado para la entrega REST.

## Comprobacion minima

```bash
curl http://localhost/health
```

Si responde `200 OK`, NGINX esta encaminando bien hacia las APIs directas.

## Las APIs responden pero NGINX no

Primero comprueba backend:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

Si ambas responden y `http://localhost/health` no, el problema esta en la capa
de NGINX.

## Problemas habituales

### Puerto 80 ocupado

Otro proceso ya esta usando el puerto `80`.

### Error de permisos al arrancar

En algunos entornos NGINX necesita privilegios elevados para escuchar en el
puerto `80`.

### Upstream mal configurado

Revisa:

- `deploy/nginx/nginx.conf`
- `deploy/nginx/upstream.conf`

Los backends esperados son `127.0.0.1:8000` y `127.0.0.1:8001`.

## Logs y runtime

Los artefactos temporales de NGINX se guardan en:

- `deploy/nginx/runtime/logs/`

Si el sistema esta parado, ese directorio puede quedar vacio.

## Modo de diagnostico

Si necesitas aislar el problema, puedes arrancar la parte directa sin pasar por
NGINX y verificar primero las APIs. Una vez respondan bien, vuelve a validar el
acceso por `http://localhost/`.
