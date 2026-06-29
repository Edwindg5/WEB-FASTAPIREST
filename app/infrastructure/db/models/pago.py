"""Modelo SQLAlchemy para Pagos."""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, JSON, ForeignKey
from datetime import datetime
from app.infrastructure.db.models.usuario import Base


class PagoModel(Base):
    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    plan = Column(String(50), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    moneda = Column(String(3), default="MXN")
    estado = Column(String(20), default="pendiente")
    mp_preference_id = Column(String(255), nullable=True)
    mp_payment_id = Column(String(255), nullable=True)
    detalle_pago = Column(JSON, nullable=True)
    fecha_pago = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<PagoModel(id={self.id}, plan={self.plan}, estado={self.estado})>"
