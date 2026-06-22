"""Entidad de Dominio: Sensor."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class TipoSensor(str, Enum):
    """Tipos de sensores disponibles."""
    TEMPERATURA = "temperatura"
    HUMEDAD = "humedad"
    CO2 = "co2"
    PRESION = "presion"
    RADIACION = "radiacion"


class EstadoSensor(str, Enum):
    """Estados posibles de un sensor."""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    DAÑADO = "dañado"


@dataclass
class Sensor:
    """Entidad de Sensor IoT."""
    
    id: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    tipo_sensor: TipoSensor = TipoSensor.TEMPERATURA
    ubicacion: Optional[str] = None
    estado: EstadoSensor = EstadoSensor.ACTIVO
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def esta_operativo(self) -> bool:
        """Verifica si el sensor está operativo."""
        return self.estado == EstadoSensor.ACTIVO
