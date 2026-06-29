"""Repositorio SQLAlchemy para Usuario."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.application.interfaces.usuario_repository import IUsuarioRepository
from app.domain.entities.usuario import Usuario, RolUsuario, EstadoUsuario
from app.infrastructure.db.models.usuario import UsuarioModel
from app.core.security import hash_password


class UsuarioRepository(IUsuarioRepository):
    """Implementación concreta del repositorio de Usuario con SQLAlchemy."""

    def __init__(self, db: AsyncSession):
        """Inicializa el repositorio con una sesión de BD.
        
        Args:
            db: Sesión SQLAlchemy asíncrona.
        """
        self.db = db

    async def create(self, usuario: Usuario, telefono_cifrado: str = None) -> Usuario:
        """Crea un nuevo usuario en la BD. telefono_cifrado ya viene encriptado."""
        db_usuario = UsuarioModel(
            correo=usuario.correo,
            nombre_completo=usuario.nombre_completo,
            rol=usuario.rol,
            estado=usuario.estado,
            contrasena_hash=usuario.contrasena_hash,
            telefono=telefono_cifrado,
        )
        self.db.add(db_usuario)
        await self.db.flush()
        usuario.id = db_usuario.id
        return usuario

    async def get_by_id(self, id: int) -> Optional[Usuario]:
        """Obtiene un usuario por ID."""
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id == id)
        )
        db_usuario = result.scalar_one_or_none()
        return self._map_to_domain(db_usuario) if db_usuario else None

    async def get_by_correo(self, correo: str) -> Optional[Usuario]:
        """Obtiene un usuario por correo."""
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.correo == correo)
        )
        db_usuario = result.scalar_one_or_none()
        return self._map_to_domain(db_usuario) if db_usuario else None

    async def get_all(self, skip: int = 0, limit: int = 10) -> List[Usuario]:
        """Obtiene todos los usuarios con paginación."""
        result = await self.db.execute(
            select(UsuarioModel)
            .offset(skip)
            .limit(limit)
        )
        db_usuarios = result.scalars().all()
        return [self._map_to_domain(u) for u in db_usuarios]

    async def update(self, id: int, usuario: Usuario) -> Optional[Usuario]:
        """Actualiza un usuario existente."""
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id == id)
        )
        db_usuario = result.scalar_one_or_none()
        
        if not db_usuario:
            return None

        # Actualizar solo los campos que vienen con valores
        if usuario.nombre_completo:
            db_usuario.nombre_completo = usuario.nombre_completo
        if usuario.rol:
            db_usuario.rol = usuario.rol
        if usuario.estado:
            db_usuario.estado = usuario.estado
        if usuario.contrasena_hash:
            db_usuario.contrasena_hash = usuario.contrasena_hash

        await self.db.flush()
        return self._map_to_domain(db_usuario)

    async def delete(self, id: int) -> bool:
        """Elimina un usuario (borrado lógico o físico)."""
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id == id)
        )
        db_usuario = result.scalar_one_or_none()
        
        if not db_usuario:
            return False

        await self.db.delete(db_usuario)
        return True

    async def usuario_exists(self, correo: str) -> bool:
        """Verifica si un usuario existe por correo."""
        result = await self.db.execute(
            select(func.count()).select_from(UsuarioModel)
            .where(UsuarioModel.correo == correo)
        )
        count = result.scalar()
        return count > 0

    async def get_count(self) -> int:
        """Obtiene el total de usuarios en la BD."""
        result = await self.db.execute(
            select(func.count()).select_from(UsuarioModel)
        )
        return result.scalar()

    @staticmethod
    def _map_to_domain(db_usuario: UsuarioModel) -> Usuario:
        """Mapea un modelo de BD a la entidad de dominio."""
        if not db_usuario:
            return None
        
        return Usuario(
            id=db_usuario.id,
            correo=db_usuario.correo,
            nombre_completo=db_usuario.nombre_completo,
            rol=db_usuario.rol,
            estado=db_usuario.estado,
            contrasena_hash=db_usuario.contrasena_hash,
            created_at=db_usuario.created_at,
            updated_at=db_usuario.updated_at,
            ultimo_login=db_usuario.ultimo_login,
        )
