"""Schemas Pydantic para Pagos."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CrearPreferenciaRequest(BaseModel):
    plan: str = Field(..., description="basico | profesional | empresarial")


class PreferenciaResponse(BaseModel):
    init_point: str
    preference_id: str


class PagoResponse(BaseModel):
    id: int
    plan: str
    monto: float
    moneda: str
    estado: str
    mp_preference_id: Optional[str]
    mp_payment_id: Optional[str]
    fecha_pago: datetime

    class Config:
        from_attributes = True


class PagoListResponse(BaseModel):
    total: int
    items: List[PagoResponse]


class WebhookPayload(BaseModel):
    type: Optional[str] = None
    data: Optional[dict] = None
    id: Optional[str] = None
