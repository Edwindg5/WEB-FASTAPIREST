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


class AdminSensorAltaDirecta(BaseModel):
    """Body para POST /admin/sensores/alta-directa.

    Da de alta un ESP32 identificado por `identificador` (el id que el
    propio dispositivo usa como MAC/ID de cola MQTT, ej. 'kajve-D8463591' —
    no tiene que tener formato de MAC address AA:BB:CC:DD:EE:FF) y lo
    asigna de una vez a un usuario real, sin pasar por el flujo de
    "sin vincular" + reclamar por QR desde la app.
    """
    identificador: str = Field(..., min_length=3, max_length=50, description="ID del ESP32, ej. kajve-D8463591")
    id_usuario: int = Field(..., description="Usuario real al que se asigna el sensor de inmediato")
    tipo: str = Field(default="ambos", description="ambos | temperatura | humedad")
    modelo: Optional[str] = Field(default=None, description="Modelo del dispositivo")
    mide_viento: bool = False
    mide_radiacion: bool = False
    mide_humedad_grano: bool = True
    nombre_lote: Optional[str] = Field(default=None, max_length=255)
    variedad: Optional[str] = Field(default="arabica", max_length=100)
    tipo_proceso: Optional[str] = Field(default="natural", max_length=50)
    ubicacion: Optional[str] = Field(default=None, max_length=255)


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


class AdminSensorAltaDirectaResponse(BaseModel):
    sensor: AdminSensorResponse
    id_lote: int
    codigo_qr: Optional[str]
    nombre_lote: Optional[str]
    estado_lote: str


class AdminSensorListResponse(BaseModel):
    total: int
    items: List[AdminSensorResponse]


class AdminSensorDetalle(AdminSensorResponse):
    historial_lotes: List[dict] = []


class QRResponse(BaseModel):
    qr_base64: str
