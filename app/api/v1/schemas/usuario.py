"""Schemas Pydantic para Usuario - DTOs de entrada y salida."""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.domain.entities.usuario import RolUsuario, EstadoUsuario


class UsuarioBase(BaseModel):
    """Schema base con los campos comunes de Usuario."""
    correo: EmailStr = Field(..., description="Email único del usuario")
    nombre_completo: str = Field(..., min_length=1, max_length=255, description="Nombre completo")
    rol: RolUsuario = Field(default=RolUsuario.SUPERVISOR, description="Rol del usuario")


class UsuarioCreate(UsuarioBase):
    """Schema para crear un usuario."""
    contrasena: str = Field(..., min_length=8, max_length=255, description="Contraseña (mín. 8 caracteres)")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono (se cifra con AES-256)")


class UsuarioUpdate(BaseModel):
    """Schema para actualizar un usuario (parcial)."""
    nombre_completo: Optional[str] = Field(None, min_length=1, max_length=255)
    rol: Optional[RolUsuario] = None
    estado: Optional[EstadoUsuario] = None


class UsuarioChangePassword(BaseModel):
    """Schema para cambiar contraseña."""
    contrasena_actual: str = Field(..., description="Contraseña actual")
    contrasena_nueva: str = Field(..., min_length=8, max_length=255, description="Nueva contraseña")


class UsuarioResponse(UsuarioBase):
    """Schema de respuesta - datos públicos del usuario."""
    id: int
    estado: EstadoUsuario
    created_at: datetime
    updated_at: datetime
    ultimo_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsuarioDetailResponse(UsuarioResponse):
    """Schema detallado del usuario (con más información)."""
    pass


class UsuarioListResponse(BaseModel):
    """Response para listar usuarios."""
    total: int = Field(..., description="Total de usuarios")
    skip: int = Field(0, description="Registros saltados")
    limit: int = Field(10, description="Límite por página")
    items: list[UsuarioResponse] = Field(default_factory=list, description="Lista de usuarios")
