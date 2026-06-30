"""Repositorio SQLAlchemy para Usuario — usa columnas reales de PostgreSQL."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.application.interfaces.usuario_repository import IUsuarioRepository
from app.domain.entities.usuario import Usuario, RolUsuario, EstadoUsuario
from app.infrastructure.db.models.usuario import UsuarioModel


class UsuarioRepository(IUsuarioRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, usuario: Usuario, **kwargs) -> Usuario:
        db_usuario = UsuarioModel(
            nombre=usuario.nombre,
            email=usuario.email,
            password_hash=usuario.password_hash,
            rol=usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol,
            estado=usuario.estado.value if hasattr(usuario.estado, "value") else usuario.estado,
            telefono=usuario.telefono,
        )
        self.db.add(db_usuario)
        await self.db.flush()
        usuario.id_usuario = db_usuario.id_usuario
        return usuario

    async def get_by_id(self, id: int) -> Optional[Usuario]:
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id_usuario == id)
        )
        db_u = result.scalar_one_or_none()
        return self._map_to_domain(db_u) if db_u else None

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.email == email)
        )
        db_u = result.scalar_one_or_none()
        return self._map_to_domain(db_u) if db_u else None

    async def get_all(self, skip: int = 0, limit: int = 10) -> List[Usuario]:
        result = await self.db.execute(
            select(UsuarioModel).offset(skip).limit(limit)
        )
        return [self._map_to_domain(u) for u in result.scalars().all()]

    async def update(self, id: int, usuario: Usuario) -> Optional[Usuario]:
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id_usuario == id)
        )
        db_u = result.scalar_one_or_none()
        if not db_u:
            return None

        if usuario.nombre:
            db_u.nombre = usuario.nombre
        if usuario.rol:
            db_u.rol = usuario.rol.value if hasattr(usuario.rol, "value") else usuario.rol
        if usuario.estado:
            db_u.estado = usuario.estado.value if hasattr(usuario.estado, "value") else usuario.estado
        if usuario.password_hash:
            db_u.password_hash = usuario.password_hash

        await self.db.flush()
        return self._map_to_domain(db_u)

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id_usuario == id)
        )
        db_u = result.scalar_one_or_none()
        if not db_u:
            return False
        await self.db.delete(db_u)
        return True

    async def usuario_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(UsuarioModel).where(UsuarioModel.email == email)
        )
        return (result.scalar() or 0) > 0

    async def get_count(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(UsuarioModel)
        )
        return result.scalar() or 0

    @staticmethod
    def _map_to_domain(db_u: UsuarioModel) -> Usuario:
        if not db_u:
            return None
        return Usuario(
            id_usuario=db_u.id_usuario,
            email=db_u.email,
            nombre=db_u.nombre,
            rol=db_u.rol,
            estado=db_u.estado,
            password_hash=db_u.password_hash,
            telefono=db_u.telefono,
            fecha_registro=db_u.fecha_registro,
        )
