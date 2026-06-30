"""Modelo SQLAlchemy para Predicciones — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from app.infrastructure.db.models.usuario import Base


class PrediccionModel(Base):
    __tablename__ = "predicciones"

    id_prediccion = Column(Integer, primary_key=True, index=True)
    id_lote = Column(Integer, ForeignKey("lotes_cafe.id_lote"), nullable=True)
    id_modelo = Column(Integer, ForeignKey("modelos_ml.id_modelo"), nullable=True)
    tiempo_estimado_horas = Column(Numeric(10, 2), nullable=True)
    calidad_estimada = Column(String(50), nullable=True)
    confianza = Column(Numeric(5, 4), nullable=True)
    fecha_prediccion = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<PrediccionModel(id_prediccion={self.id_prediccion})>"
