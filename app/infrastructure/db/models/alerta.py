"""Modelo SQLAlchemy para Alertas — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from app.infrastructure.db.models.usuario import Base


class AlertaModel(Base):
    __tablename__ = "alertas"

    id_alerta = Column(Integer, primary_key=True, index=True)
    id_lote = Column(Integer, ForeignKey("lotes_cafe.id_lote"), nullable=True)
    tipo_alerta = Column(String(100), nullable=True)
    mensaje = Column(Text, nullable=True)
    nivel_severidad = Column(String(50), default="normal")
    atendida = Column(Boolean, default=False)
    fecha_generada = Column(DateTime, nullable=True)
    fecha_atencion = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AlertaModel(id_alerta={self.id_alerta}, nivel={self.nivel_severidad})>"
