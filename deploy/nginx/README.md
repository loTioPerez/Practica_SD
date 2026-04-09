# NGINX

Configuracion del balanceador de carga para la arquitectura REST.

## Ficheros relevantes

- `nginx.conf`: configuracion principal del servidor
- `upstream.conf`: definicion del upstream con las APIs directas
- `mime.types`: tipos MIME usados por NGINX
- `runtime/`: directorio de trabajo local para logs y PID cuando se arranca NGINX

## Rol en la practica

NGINX actua como punto unico de entrada de la arquitectura directa y reparte
peticiones entre las instancias REST publicadas en `:8000` y `:8001`.
