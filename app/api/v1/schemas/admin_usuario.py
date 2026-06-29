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
