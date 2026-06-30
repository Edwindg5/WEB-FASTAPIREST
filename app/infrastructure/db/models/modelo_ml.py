"""Modelo SQLAlchemy para Modelos ML — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, Numeric
from app.infrastructure.db.models.usuario import Base


class ModeloMLModel(Base):
    __tablename__ = "modelos_ml"

    id_modelo = Column(Integer, primary_key=True, index=True)
    nombre_modelo = Column(String(255), nullable=True)
    version = Column(String(50), nullable=True)
    tipo = Column(String(100), nullable=True)
    ruta_archivo = Column(String(500), nullable=True)
    precision_score = Column(Numeric(5, 4), nullable=True)
    estado = Column(String(20), default="activo")
    fecha_entrenamiento = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<ModeloMLModel(id_modelo={self.id_modelo}, nombre={self.nombre_modelo})>"
