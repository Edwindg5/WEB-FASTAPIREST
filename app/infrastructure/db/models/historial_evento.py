"""Modelo SQLAlchemy para Historial de Eventos — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.infrastructure.db.models.usuario import Base


class HistorialEventoModel(Base):
    __tablename__ = "historial_eventos"

    id_evento = Column(Integer, primary_key=True, index=True)
    id_lote = Column(Integer, ForeignKey("lotes_cafe.id_lote"), nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    tipo_evento = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)
    fecha_evento = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<HistorialEventoModel(id_evento={self.id_evento})>"
