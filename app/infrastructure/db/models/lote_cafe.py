"""Modelo SQLAlchemy para Lote de Café."""
from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey
from datetime import datetime
from app.infrastructure.db.models.usuario import Base


class LoteCafeModel(Base):
    __tablename__ = "lotes_cafe"

    id = Column(Integer, primary_key=True, index=True)
    codigo_qr = Column(String(255), unique=True, nullable=True)
    nombre = Column(String(255), nullable=False)
    estado = Column(String(50), default="en_progreso")
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin_estimada = Column(Date, nullable=True)
    fecha_fin_real = Column(Date, nullable=True)
    temperatura_objetivo = Column(Numeric(5, 2), nullable=True)
    humedad_objetivo = Column(Numeric(5, 2), nullable=True)
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<LoteCafeModel(id={self.id}, nombre={self.nombre}, estado={self.estado})>"
