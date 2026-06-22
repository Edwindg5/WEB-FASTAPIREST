"""Interfaces/Puertos abstractas para repositorios.

Define el contrato que deben cumplir los repositorios.
La implementación concreta está en infrastructure/db/repositories/.
"""
from abc import ABC, abstractmethod
from typing import Optional, List


class IRepository(ABC):
    """Interfaz base para todos los repositorios.
    
    Patrón Repository genérico para acceso a datos.
    """

    @abstractmethod
    async def create(self, obj: object) -> object:
        """Crea un nuevo registro."""
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[object]:
        """Obtiene un registro por ID."""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 10) -> List[object]:
        """Obtiene todos los registros con paginación."""
        pass

    @abstractmethod
    async def update(self, id: int, obj: object) -> Optional[object]:
        """Actualiza un registro existente."""
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Elimina un registro."""
        pass
