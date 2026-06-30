"""Modelo SQLAlchemy para Inferencias ML — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, JSON, ForeignKey
from app.infrastructure.db.models.usuario import Base


class InferenciaMLModel(Base):
    __tablename__ = "inferencias_ml"

    id_inferencia = Column(Integer, primary_key=True, index=True)
    id_modelo = Column(Integer, ForeignKey("modelos_ml.id_modelo"), nullable=True)
    datos_entrada = Column(JSON, nullable=True)
    resultado = Column(JSON, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    etiqueta = Column(String(50), nullable=True)
    confianza = Column(Numeric(5, 4), nullable=True)
    fecha_inferencia = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<InferenciaMLModel(id_inferencia={self.id_inferencia})>"
