"""Modelo SQLAlchemy para Sensor ESP32 — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.infrastructure.db.models.usuario import Base


class SensorModel(Base):
    __tablename__ = "sensores"

    id_sensor = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String(17), unique=True, nullable=True, index=True)
    tipo = Column(String(50), default="ambos")
    modelo = Column(String(100), default="ESP32-WROOM-32")
    estado = Column(String(20), default="activo")
    id_cola_mqtt = Column(String(255), nullable=True)
    provisioning_token = Column(String(255), unique=True, nullable=True)
    token_usado = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<SensorModel(id_sensor={self.id_sensor}, mac={self.mac_address})>"
