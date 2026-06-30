"""Schemas Pydantic para Suscripciones."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PlanInfo(BaseModel):
    plan: str
    precio: float
    moneda: str
    descripcion: str
    lotes_max: int


class SuscripcionResponse(BaseModel):
    id_suscripcion: Optional[int] = None
    plan: str
    estado: str
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    lotes_max: int

    class Config:
        from_attributes = True
