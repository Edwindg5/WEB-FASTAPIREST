"""Schemas Pydantic para endpoints de admin — sensores."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class AdminSensorCreate(BaseModel):
    mac_address: str = Field(..., description="MAC address del ESP32 (AA:BB:CC:DD:EE:FF)")
    tipo: str = Field(default="ambos", description="ambos | temperatura | humedad")
    modelo: str = Field(default="ESP32-WROOM-32", description="Modelo del dispositivo")


class AdminSensorUpdate(BaseModel):
    estado: Optional[str] = Field(None, description="activo | inactivo | mantenimiento")
    modelo: Optional[str] = None


class AdminSensorResponse(BaseModel):
    id: int
    mac_address: Optional[str]
    tipo: Optional[str]
    modelo: Optional[str]
    estado: str
    id_cola_mqtt: Optional[str]
    provisioning_token: Optional[str]
    token_usado: bool
    lote_nombre: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminSensorListResponse(BaseModel):
    total: int
    items: List[AdminSensorResponse]


class AdminSensorDetalle(AdminSensorResponse):
    historial_lotes: List[dict] = []


class QRResponse(BaseModel):
    qr_base64: str
