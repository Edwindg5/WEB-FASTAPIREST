"""Schemas Pydantic para endpoints de admin — lotes de café."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AdminLoteCreate(BaseModel):
    nombre_lote: str = Field(..., description="Nombre del lote")
    variedad: Optional[str] = Field(None, description="Variedad del café")
    tipo_proceso: Optional[str] = Field(None, description="Tipo de proceso de secado")
    peso_kg: Optional[float] = Field(None, description="Peso en kilogramos")
    ubicacion: Optional[str] = Field(None, description="Ubicación del lote")
    id_sensor: int = Field(..., description="ID del sensor asignado al lote")


class AdminLoteResponse(BaseModel):
    id_lote: int
    id_usuario: Optional[int]
    id_sensor: Optional[int]
    nombre_lote: Optional[str]
    variedad: Optional[str]
    tipo_proceso: Optional[str]
    peso_kg: Optional[float]
    ubicacion: Optional[str]
    codigo_qr: Optional[str]
    estado: str
    fecha_inicio_secado: Optional[datetime]
    fecha_fin_secado: Optional[datetime]
    linked_at: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
