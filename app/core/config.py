"""Configuración centralizada de la aplicación."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno."""

    # Aplicación
    app_title: str = "API Web - Sistema Monitoreo Secado Café"
    app_version: str = "1.0.0"
    app_description: str = "Microservicio para monitoreo inteligente del secado de café"
    debug: bool = False

    # Base de Datos
    database_url: str = "postgresql://user:password@localhost:5432/cafe_monitoring_db"
    sqlalchemy_echo: bool = False

    # JWT
    secret_key: str = "cambiar-esta-clave-secreta-en-produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    frontend_url: str = "http://localhost:4200"
    backend_url: str = "http://localhost:8000"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60

    # MQTT
    mqtt_broker_url: Optional[str] = None
    mqtt_broker_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    # Email
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
