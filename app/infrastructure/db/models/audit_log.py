"""Modelo SQLAlchemy para Audit Log — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from app.infrastructure.db.models.usuario import Base


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id_log = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)
    accion = Column(String(255), nullable=False)
    entidad = Column(String(100), nullable=True)
    id_entidad = Column(Integer, nullable=True)
    detalles = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    fecha_hora = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLogModel(id_log={self.id_log}, accion={self.accion})>"
