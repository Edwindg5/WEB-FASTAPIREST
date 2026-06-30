"""Modelo SQLAlchemy para Recomendaciones — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.infrastructure.db.models.usuario import Base


class RecomendacionModel(Base):
    __tablename__ = "recomendaciones"

    id_recomendacion = Column(Integer, primary_key=True, index=True)
    id_lote = Column(Integer, ForeignKey("lotes_cafe.id_lote"), nullable=True)
    texto = Column(Text, nullable=True)
    origen = Column(String(50), default="ml")
    fecha_generada = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<RecomendacionModel(id_recomendacion={self.id_recomendacion})>"
