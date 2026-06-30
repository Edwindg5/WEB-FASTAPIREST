"""Modelo SQLAlchemy para Usuario — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False, default="productor")
    estado = Column(String(50), nullable=False, default="activo")
    telefono = Column(String(20), nullable=True)
    fecha_registro = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<UsuarioModel(id_usuario={self.id_usuario}, email={self.email}, rol={self.rol})>"
