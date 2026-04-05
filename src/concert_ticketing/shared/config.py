"""Configuracion centralizada cargada desde YAML y entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


def _find_config_dir() -> Path:
    """Busca el directorio config del proyecto."""
    env_path = os.getenv("CONFIG_DIR")
    if env_path:
        return Path(env_path)
    # Subimos desde src/concert_ticketing/shared/ hasta la raiz del proyecto
    candidate = Path(__file__).resolve().parents[3] / "config"
    if candidate.is_dir():
        return candidate
    return Path("config")


def _load_yaml(name: str) -> dict:
    path = _find_config_dir() / name
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return {}


@dataclass(frozen=True)
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True


@dataclass(frozen=True)
class RabbitMQConfig:
    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"
    vhost: str = "/"
    management_port: int = 15672


@dataclass(frozen=True)
class AppConfig:
    app_name: str = "concert-ticketing-system"
    log_level: str = "INFO"
    total_tickets: int = 20_000
    host: str = "0.0.0.0"
    redis: RedisConfig = field(default_factory=RedisConfig)
    rabbitmq: RabbitMQConfig = field(default_factory=RabbitMQConfig)

    @staticmethod
    def from_env() -> AppConfig:
        """Carga configuracion combinando YAML y variables de entorno."""
        common = _load_yaml("common.yaml")
        redis_yaml = _load_yaml("redis.yaml")
        rabbitmq_yaml = _load_yaml("rabbitmq.yaml")

        app_section = common.get("app", {})
        network_section = common.get("network", {})
        redis_section = redis_yaml.get("redis", {})
        rabbitmq_section = rabbitmq_yaml.get("rabbitmq", {})

        redis_cfg = RedisConfig(
            host=os.getenv("REDIS_HOST", redis_section.get("host", "localhost")),
            port=int(os.getenv("REDIS_PORT", redis_section.get("port", 6379))),
            db=int(os.getenv("REDIS_DB", redis_section.get("db", 0))),
            password=os.getenv("REDIS_PASSWORD", redis_section.get("password", None)),
            decode_responses=redis_section.get("decode_responses", True),
            socket_timeout=float(redis_section.get("socket_timeout", 5.0)),
            socket_connect_timeout=float(redis_section.get("socket_connect_timeout", 5.0)),
            retry_on_timeout=redis_section.get("retry_on_timeout", True),
        )

        rabbitmq_cfg = RabbitMQConfig(
            host=os.getenv("RABBITMQ_HOST", rabbitmq_section.get("host", "localhost")),
            port=int(os.getenv("RABBITMQ_PORT", rabbitmq_section.get("port", 5672))),
            user=os.getenv("RABBITMQ_USER", rabbitmq_section.get("user", "guest")),
            password=os.getenv("RABBITMQ_PASSWORD", rabbitmq_section.get("password", "guest")),
            vhost=os.getenv("RABBITMQ_VHOST", rabbitmq_section.get("vhost", "/")),
            management_port=int(rabbitmq_section.get("management_port", 15672)),
        )

        return AppConfig(
            app_name=app_section.get("name", "concert-ticketing-system"),
            log_level=os.getenv("LOG_LEVEL", app_section.get("log_level", "INFO")),
            total_tickets=int(app_section.get("total_tickets", 20_000)),
            host=network_section.get("host", "0.0.0.0"),
            redis=redis_cfg,
            rabbitmq=rabbitmq_cfg,
        )
