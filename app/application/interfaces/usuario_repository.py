"""Interfaz para el Repositorio de Usuario."""
from abc import abstractmethod
from typing import Optional
from app.application.interfaces.repository import IRepository
from app.domain.entities.usuario import Usuario


class IUsuarioRepository(IRepository):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Usuario]:
        pass

    @abstractmethod
    async def usuario_exists(self, email: str) -> bool:
        pass

    @abstractmethod
    async def get_count(self) -> int:
        pass
