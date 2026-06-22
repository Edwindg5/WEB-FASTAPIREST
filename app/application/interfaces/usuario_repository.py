"""Interfaz para el Repositorio de Usuario."""
from abc import abstractmethod
from typing import Optional
from app.application.interfaces.repository import IRepository
from app.domain.entities.usuario import Usuario


class IUsuarioRepository(IRepository):
    """Interfaz para el repositorio de Usuario.
    
    Extiende IRepository con métodos específicos de Usuario.
    """

    @abstractmethod
    async def get_by_correo(self, correo: str) -> Optional[Usuario]:
        """Obtiene un usuario por su correo."""
        pass

    @abstractmethod
    async def usuario_exists(self, correo: str) -> bool:
        """Verifica si un usuario existe por correo."""
        pass

    @abstractmethod
    async def get_count(self) -> int:
        """Obtiene el total de usuarios."""
        pass
