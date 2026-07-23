"""Schemas Pydantic para endpoints de admin — usuarios."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class AdminUsuarioItem(BaseModel):
    id_usuario: int
    nombre: str
    email: str
    rol: str
    estado: str
    fecha_registro: datetime

    class Config:
        from_attributes = True


class AdminUsuarioDetalle(AdminUsuarioItem):
    total_lotes: int = 0
    lotes_activos: int = 0
    ultimo_login: Optional[datetime] = None


class AdminUsuarioListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[AdminUsuarioItem]


class AdminUsuarioEstadoUpdate(BaseModel):
    estado: str = Field(..., pattern="^(activo|inactivo)$")


class AdminUsuarioUpdate(BaseModel):
    """Body para PUT /admin/usuarios/{id}: edición completa de datos del usuario."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=150)
    email: Optional[str] = Field(None, min_length=3, max_length=150)
    rol: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=6)
