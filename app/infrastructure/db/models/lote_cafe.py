"""Modelo SQLAlchemy para Lote de Café — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum as SAEnum
from app.infrastructure.db.models.usuario import Base

EstadoLoteEnum = SAEnum("en_proceso", "finalizado", "cancelado", name="estado_lote", create_type=False)


class LoteCafeModel(Base):
    __tablename__ = "lotes_cafe"

    id_lote = Column(Integer, primary_key=True, index=True)
    nombre_lote = Column(String(255), nullable=True)
    variedad = Column(String(100), nullable=True)
    tipo_proceso = Column(String(50), nullable=True)
    peso_kg = Column(Numeric(10, 2), nullable=True)
    ubicacion = Column(String(255), nullable=True)
    codigo_qr = Column(String(255), unique=True, nullable=True)
    estado = Column(EstadoLoteEnum, default="en_proceso")
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    id_sensor = Column(Integer, ForeignKey("sensores.id_sensor"), nullable=True)
    fecha_inicio_secado = Column(DateTime, nullable=True)
    fecha_fin_secado = Column(DateTime, nullable=True)
    linked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<LoteCafeModel(id_lote={self.id_lote}, nombre={self.nombre_lote})>"
