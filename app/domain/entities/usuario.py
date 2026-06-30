"""Entidad de Dominio: Usuario."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class RolUsuario(str, Enum):
    ADMINISTRADOR = "administrador"
    SUPERVISOR = "supervisor"
    PRODUCTOR = "productor"


class EstadoUsuario(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"


@dataclass
class Usuario:
    id_usuario: Optional[int] = None
    email: str = ""
    nombre: str = ""
    rol: RolUsuario = RolUsuario.PRODUCTOR
    estado: EstadoUsuario = EstadoUsuario.ACTIVO
    password_hash: str = ""
    telefono: Optional[str] = None
    fecha_registro: Optional[datetime] = None

    def is_admin(self) -> bool:
        return self.rol == RolUsuario.ADMINISTRADOR

    def is_activo(self) -> bool:
        return self.estado == EstadoUsuario.ACTIVO

    def puede_leer_lotes(self) -> bool:
        return self.is_activo()

    def puede_modificar_lotes(self) -> bool:
        return self.is_activo() and self.rol in (RolUsuario.ADMINISTRADOR, RolUsuario.SUPERVISOR)
