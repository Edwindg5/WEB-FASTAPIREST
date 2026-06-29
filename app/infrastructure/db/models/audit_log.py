"""Modelo SQLAlchemy para Audit Log."""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from datetime import datetime
from app.infrastructure.db.models.usuario import Base


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    accion = Column(String(255), nullable=False)
    entidad_tipo = Column(String(50), nullable=True)
    entidad_id = Column(Integer, nullable=True)
    valores_anteriores = Column(JSON, nullable=True)
    valores_nuevos = Column(JSON, nullable=True)
    ip_cliente = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLogModel(id={self.id}, accion={self.accion})>"
