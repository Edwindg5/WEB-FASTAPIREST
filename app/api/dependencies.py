"""Dependencias para inyección de dependencias en FastAPI."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.usuario_repository import UsuarioRepository
from app.application.use_cases.auth_use_case import AuthUseCase, UsuarioUseCase


async def get_auth_use_case(db: AsyncSession = Depends(get_db)) -> AuthUseCase:
    """Inyecta el caso de uso de autenticación."""
    usuario_repo = UsuarioRepository(db)
    return AuthUseCase(usuario_repo)


async def get_usuario_use_case(db: AsyncSession = Depends(get_db)) -> UsuarioUseCase:
    """Inyecta el caso de uso de usuario."""
    usuario_repo = UsuarioRepository(db)
    return UsuarioUseCase(usuario_repo)
