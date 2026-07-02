"""Entidad de Dominio: Lote de Café."""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from enum import Enum


class EstadoLote(str, Enum):
    """Estados posibles de un lote."""
    EN_PROCESO = "en_proceso"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"


@dataclass
class LoteCafe:
    """Entidad de Lote de Café en proceso de secado."""
    
    id: Optional[int] = None
    codigo_qr: Optional[str] = None
    nombre: str = ""
    estado: EstadoLote = EstadoLote.EN_PROCESO
    fecha_inicio: Optional[date] = None
    fecha_fin_estimada: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    temperatura_objetivo: Optional[float] = None
    humedad_objetivo: Optional[float] = None
    created_by: Optional[int] = None  # ID del usuario que creó
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def esta_activo(self) -> bool:
        """Verifica si el lote está activo (en progreso)."""
        return self.estado == EstadoLote.EN_PROCESO

    def esta_completado(self) -> bool:
        """Verifica si el lote está completado."""
        return self.estado == EstadoLote.FINALIZADO
