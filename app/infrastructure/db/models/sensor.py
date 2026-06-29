"""Modelo SQLAlchemy para Sensor ESP32."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.infrastructure.db.models.usuario import Base


class SensorModel(Base):
    __tablename__ = "sensores"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=True, index=True)
    nombre = Column(String(255), nullable=True)
    mac_address = Column(String(17), unique=True, nullable=True, index=True)
    tipo = Column(String(20), default="ambos")
    tipo_sensor = Column(String(50), nullable=True)
    modelo = Column(String(100), nullable=True)
    ubicacion = Column(String(255), nullable=True)
    estado = Column(String(50), default="activo")
    id_cola_mqtt = Column(String(255), nullable=True)
    provisioning_token = Column(String(36), unique=True, nullable=True)
    token_usado = Column(Boolean, default=False)
    lote_id = Column(Integer, ForeignKey("lotes_cafe.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SensorModel(id={self.id}, mac={self.mac_address}, estado={self.estado})>"
