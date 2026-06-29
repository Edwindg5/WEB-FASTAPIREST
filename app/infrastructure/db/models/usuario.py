"""Modelo SQLAlchemy para Usuario."""
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.domain.entities.usuario import RolUsuario, EstadoUsuario

Base = declarative_base()


class UsuarioModel(Base):
    """Modelo SQLAlchemy que mapea la tabla 'usuarios' en PostgreSQL."""
    
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    correo = Column(String(255), unique=True, nullable=False, index=True)
    nombre_completo = Column(String(255), nullable=False)
    telefono = Column(String(512), nullable=True)  # almacenado cifrado AES-256
    rol = Column(Enum(RolUsuario), default=RolUsuario.SUPERVISOR, nullable=False)
    estado = Column(Enum(EstadoUsuario), default=EstadoUsuario.ACTIVO, nullable=False)
    contrasena_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    ultimo_login = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<UsuarioModel(id={self.id}, correo={self.correo}, rol={self.rol})>"
