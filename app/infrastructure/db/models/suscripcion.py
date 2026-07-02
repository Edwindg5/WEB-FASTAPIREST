"""Modelo SQLAlchemy para Suscripciones — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from app.infrastructure.db.models.usuario import Base

EstadoSuscripcionEnum = SAEnum("activa", "cancelada", "vencida", "prueba", name="estado_suscripcion", create_type=False)


class SuscripcionModel(Base):
    __tablename__ = "suscripciones"

    id_suscripcion = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    plan = Column(String(50), nullable=False, default="prueba")
    estado = Column(EstadoSuscripcionEnum, default="prueba")
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    lotes_max = Column(Integer, default=1)

    def __repr__(self) -> str:
        return f"<SuscripcionModel(id_suscripcion={self.id_suscripcion}, plan={self.plan})>"
