"""Entidad de Dominio: Usuario.

Entidad pura sin dependencias de frameworks.
Contiene solo la lógica de negocio relacionada a usuarios.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class RolUsuario(str, Enum):
    """Roles de usuario disponibles."""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    TECNICO = "tecnico"


class EstadoUsuario(str, Enum):
    """Estados posibles de un usuario."""
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    BLOQUEADO = "bloqueado"


@dataclass
class Usuario:
    """Entidad de Usuario.
    
    Representa un usuario del sistema con sus datos básicos.
    Nota: Esta es una entidad de DOMINIO, no vinculada a frameworks.
    """
    
    id: Optional[int] = None
    correo: str = ""
    nombre_completo: str = ""
    rol: RolUsuario = RolUsuario.SUPERVISOR
    estado: EstadoUsuario = EstadoUsuario.ACTIVO
    contrasena_hash: str = ""  # No almacenar texto plano
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    ultimo_login: Optional[datetime] = None
    
    def is_admin(self) -> bool:
        """Verifica si el usuario es administrador."""
        return self.rol == RolUsuario.ADMIN
    
    def is_activo(self) -> bool:
        """Verifica si el usuario está activo."""
        return self.estado == EstadoUsuario.ACTIVO
    
    def puede_leer_lotes(self) -> bool:
        """Verifica si puede leer lotes."""
        return self.is_activo() and self.rol in [RolUsuario.ADMIN, RolUsuario.SUPERVISOR]
    
    def puede_modificar_lotes(self) -> bool:
        """Verifica si puede modificar lotes (solo admins)."""
        return self.is_activo() and self.is_admin()
