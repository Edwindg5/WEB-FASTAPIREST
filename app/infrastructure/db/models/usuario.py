"""Modelo SQLAlchemy para Usuario — columnas reales de PostgreSQL."""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

RolUsuarioEnum = SAEnum("administrador", "productor", name="rol_usuario", create_type=False)
EstadoUsuarioEnum = SAEnum("activo", "inactivo", name="estado_usuario", create_type=False)


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(RolUsuarioEnum, nullable=False, default="productor")
    estado = Column(EstadoUsuarioEnum, nullable=False, default="activo")
    telefono = Column(String(20), nullable=True)
    fecha_registro = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<UsuarioModel(id_usuario={self.id_usuario}, email={self.email}, rol={self.rol})>"
