"""Modelo SQLAlchemy para Reportes — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from app.infrastructure.db.models.usuario import Base

FormatoReporteEnum = SAEnum("pdf", "excel", name="formato_reporte", create_type=False)


class ReporteModel(Base):
    __tablename__ = "reportes"

    id_reporte = Column(Integer, primary_key=True, index=True)
    id_lote = Column(Integer, ForeignKey("lotes_cafe.id_lote"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    tipo_reporte = Column(String(100), nullable=True)
    formato = Column(FormatoReporteEnum, default="pdf")
    url_archivo = Column(String(500), nullable=True)
    fecha_generacion = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<ReporteModel(id_reporte={self.id_reporte}, tipo={self.tipo_reporte})>"
