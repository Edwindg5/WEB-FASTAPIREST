"""Modelo SQLAlchemy para Pagos — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum as SAEnum
from app.infrastructure.db.models.usuario import Base

EstadoPagoEnum = SAEnum("pendiente", "aprobado", "rechazado", "reembolsado", name="estado_pago", create_type=False)


class PagoModel(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_suscripcion = Column(Integer, ForeignKey("suscripciones.id_suscripcion"), nullable=True)
    monto = Column(Numeric(10, 2), nullable=False)
    moneda = Column(String(3), default="MXN")
    estado = Column(EstadoPagoEnum, default="pendiente")
    mp_preference_id = Column(String(255), nullable=True)
    mp_payment_id = Column(String(255), nullable=True)
    fecha_pago = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<PagoModel(id_pago={self.id_pago}, estado={self.estado})>"
