"""Modelo SQLAlchemy para Reportes."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.infrastructure.db.models.usuario import Base


class ReporteModel(Base):
    __tablename__ = "reportes"

    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey("lotes_cafe.id"), nullable=False)
    tipo = Column(String(50), nullable=False)
    formato = Column(String(10), nullable=False)
    archivo_url = Column(String(500), nullable=True)
    generado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ReporteModel(id={self.id}, tipo={self.tipo}, formato={self.formato})>"
