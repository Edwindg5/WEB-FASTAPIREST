"""Modelo SQLAlchemy para Suscripciones."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.infrastructure.db.models.usuario import Base


class SuscripcionModel(Base):
    __tablename__ = "suscripciones"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False, unique=True)
    plan = Column(String(50), nullable=False, default="prueba")
    estado = Column(String(20), default="prueba")
    fecha_inicio = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_fin = Column(DateTime, nullable=True)
    lotes_max = Column(Integer, default=1)
    id_pago = Column(Integer, ForeignKey("pagos.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SuscripcionModel(id={self.id}, plan={self.plan}, estado={self.estado})>"
