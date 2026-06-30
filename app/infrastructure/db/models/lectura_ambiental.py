"""Modelo SQLAlchemy para Lecturas Ambientales — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, Boolean, DateTime, Numeric, ForeignKey
from app.infrastructure.db.models.usuario import Base


class LecturaAmbientalModel(Base):
    __tablename__ = "lecturas_ambientales"

    id_lectura = Column(Integer, primary_key=True, index=True)
    id_sensor = Column(Integer, ForeignKey("sensores.id_sensor"), nullable=True)
    temperatura = Column(Numeric(5, 2), nullable=True)
    humedad = Column(Numeric(5, 2), nullable=True)
    presion = Column(Numeric(7, 2), nullable=True)
    luz = Column(Numeric(10, 2), nullable=True)
    lluvia = Column(Boolean, default=False)
    viento = Column(Numeric(5, 2), nullable=True)
    timestamp = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<LecturaAmbientalModel(id_lectura={self.id_lectura}, sensor={self.id_sensor})>"
