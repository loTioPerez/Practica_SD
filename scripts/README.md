# 📜 Scripts Auxiliares — Concert Ticketing System

## Resumen de Scripts Disponibles

### 🔧 Librería Compartida

| Script | Descripción |
|--------|-------------|
| `_common.sh` | Funciones comunes: logging con colores, gestión de PIDs, esperas de puertos, Docker helpers |

### 🚀 Scripts de Arranque

| Script | Descripción |
|--------|-------------|
| `start_all.sh` | Levanta **TODO**: Redis + RabbitMQ + API Directa (×2) + NGINX + Gateway Indirecto + Workers (×3) |
| `start_direct_only.sh` | Solo arquitectura **directa**: Redis + API Directa (×2) + NGINX |
| `start_indirect_only.sh [N]` | Solo arquitectura **indirecta**: Redis + RabbitMQ + Gateway + N Workers (default: 3) |
| `start_direct_stack.sh` | Levanta solo Docker (Redis/RabbitMQ) + seed — útil para desarrollo |
| `start_indirect_stack.sh` | Levanta Docker + seed para la arquitectura indirecta |

### 🛑 Scripts de Parada y Reset

| Script | Descripción |
|--------|-------------|
| `stop_all.sh` | Para **todos** los servicios (Python, NGINX, Docker) y limpia PIDs |
| `reset_system.sh` | Reset completo: para todo → FLUSHALL Redis → reset RabbitMQ → re-seed → limpia logs |

### 📊 Estado y Monitorización

| Script | Descripción |
|--------|-------------|
| `status.sh` | Muestra estado de todo: Docker, puertos, procesos, health checks |
| `logs.sh [filtro]` | `tail -f` de logs. Filtros: `all`, `direct`, `indirect`, `worker`, `gateway` |

### 🏋️ Benchmarks

| Script | Descripción |
|--------|-------------|
| `run_direct_benchmark.sh` | Ejecuta benchmark contra API directa |
| `run_indirect_benchmark.sh` | Ejecuta benchmark contra gateway indirecto |
| `run_comparative_benchmarks.sh` | Benchmarks comparativos directa vs indirecta |
| `run_scalability_test.sh` | Test de escalabilidad (1, 2, 4, 8 workers) |
| `run_contention_test.sh` | Test de contención (normal vs hotspot) |
| `run_full_analysis.sh` | Pipeline completo: benchmarks + análisis + report |
| `generate_report.sh` | Genera informes Markdown/HTML con gráficos |

---

## Instalación

### Desde el archivo comprimido

```bash
# 1. Copiar el archivo a tu proyecto
cp scripts_auxiliares.tar.gz /home/gaizka/Almacen/3r/SD/Practica_SD/

# 2. Descomprimir (sobreescribe scripts/ existente)
cd /home/gaizka/Almacen/3r/SD/Practica_SD/
tar -xzf scripts_auxiliares.tar.gz

# 3. Verificar permisos de ejecución
chmod +x scripts/*.sh

# 4. Limpiar el archivo comprimido
rm scripts_auxiliares.tar.gz
```

### Desde copia directa

```bash
# Copiar toda la carpeta scripts/
cp -r /ruta/origen/scripts/ /home/gaizka/Almacen/3r/SD/Practica_SD/scripts/
chmod +x /home/gaizka/Almacen/3r/SD/Practica_SD/scripts/*.sh
```

---

## Uso Rápido

```bash
cd /home/gaizka/Almacen/3r/SD/Practica_SD

# Levantar todo el sistema
./scripts/start_all.sh

# Ver estado
./scripts/status.sh

# Ver logs en tiempo real
./scripts/logs.sh

# Solo logs de workers
./scripts/logs.sh worker

# Parar todo
./scripts/stop_all.sh

# Reset completo (limpia Redis, RabbitMQ, logs)
./scripts/reset_system.sh

# Solo arquitectura directa
./scripts/start_direct_only.sh

# Solo arquitectura indirecta con 5 workers
./scripts/start_indirect_only.sh 5
```

---

## Requisitos

- **Docker** (con `docker compose`)
- **Python 3.10+** (con dependencias del proyecto instaladas)
- **NGINX** (opcional, para balanceo de carga)
- **curl** (para health checks)

---

## Estructura de Directorios Generados

```
Practica_SD/
├── logs/              ← Logs de servicios (creado automáticamente)
│   ├── direct_api_0.log
│   ├── direct_api_1.log
│   ├── indirect_gateway.log
│   └── worker_0.log, worker_1.log, ...
├── .pids/             ← PIDs de procesos (creado automáticamente)
│   ├── direct_api_0.pid
│   └── ...
└── scripts/           ← Todos los scripts auxiliares
    ├── _common.sh
    ├── start_all.sh
    ├── ...
```
