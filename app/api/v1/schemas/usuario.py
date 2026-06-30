"""Schemas Pydantic para Usuario."""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.domain.entities.usuario import RolUsuario, EstadoUsuario


class UsuarioBase(BaseModel):
    email: EmailStr = Field(..., description="Email único del usuario")
    nombre: str = Field(..., min_length=1, max_length=255)
    rol: RolUsuario = Field(default=RolUsuario.PRODUCTOR)


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    rol: Optional[RolUsuario] = None
    estado: Optional[EstadoUsuario] = None


class UsuarioChangePassword(BaseModel):
    password_actual: str = Field(..., description="Contraseña actual")
    password_nuevo: str = Field(..., min_length=8, max_length=255)


class UsuarioResponse(UsuarioBase):
    id_usuario: int
    estado: EstadoUsuario
    telefono: Optional[str] = None
    fecha_registro: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsuarioListResponse(BaseModel):
    total: int
    skip: int = 0
    limit: int = 10
    items: list[UsuarioResponse] = []
