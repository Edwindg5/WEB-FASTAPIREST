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
    id_pago: int
    id_suscripcion: Optional[int] = None
    monto: float
    moneda: str
    estado: str
    mp_preference_id: Optional[str] = None
    mp_payment_id: Optional[str] = None
    fecha_pago: Optional[datetime] = None

    class Config:
        from_attributes = True


class PagoListResponse(BaseModel):
    total: int
    items: List[PagoResponse]


class WebhookPayload(BaseModel):
    type: Optional[str] = None
    data: Optional[dict] = None
    id: Optional[str] = None
