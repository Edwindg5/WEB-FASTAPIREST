"""Casos de uso para autenticación y gestión de usuarios."""
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.usuario import Usuario, EstadoUsuario
from app.application.interfaces.usuario_repository import IUsuarioRepository
from app.infrastructure.db.repositories.usuario_repository import UsuarioRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)


class AuthUseCase:
    """Caso de uso para autenticación (login, registro, etc)."""

    def __init__(self, usuario_repo: IUsuarioRepository):
        """Inicializa con el repositorio de usuario."""
        self.usuario_repo = usuario_repo

    async def registrar_usuario(
        self, correo: str, nombre_completo: str, contrasena: str, rol: str = "supervisor"
    ) -> Usuario:
        """Registra un nuevo usuario en el sistema.
        
        Args:
            correo: Email del usuario.
            nombre_completo: Nombre completo.
            contrasena: Contraseña en texto plano (se hará hash).
            rol: Rol del usuario (default: supervisor).
            
        Returns:
            Usuario creado.
            
        Raises:
            ValueError: Si el correo ya existe.
        """
        # Verificar que no exista
        if await self.usuario_repo.usuario_exists(correo):
            raise ValueError(f"El usuario con correo '{correo}' ya existe")

        # Crear entidad de dominio
        usuario = Usuario(
            correo=correo,
            nombre_completo=nombre_completo,
            rol=rol,
            estado=EstadoUsuario.ACTIVO,
            contrasena_hash=hash_password(contrasena),
        )

        # Persistir en BD
        usuario_creado = await self.usuario_repo.create(usuario)
        return usuario_creado

    async def login(self, correo: str, contrasena: str) -> Tuple[str, str, Usuario]:
        """Autentica un usuario y genera tokens JWT.
        
        Args:
            correo: Email del usuario.
            contrasena: Contraseña en texto plano.
            
        Returns:
            Tupla (access_token, refresh_token, usuario).
            
        Raises:
            ValueError: Si credenciales inválidas o usuario no activo.
        """
        # Buscar usuario
        usuario = await self.usuario_repo.get_by_correo(correo)
        if not usuario:
            raise ValueError("Credenciales inválidas")

        # Verificar contraseña
        if not verify_password(contrasena, usuario.contrasena_hash):
            raise ValueError("Credenciales inválidas")

        # Verificar estado
        if not usuario.is_activo():
            raise ValueError(f"Usuario {usuario.estado.value}")

        # Generar tokens
        access_token = create_access_token(
            data={"sub": str(usuario.id), "correo": usuario.correo, "role": usuario.rol.value}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(usuario.id)}
        )

        return access_token, refresh_token, usuario

    async def cambiar_contrasena(
        self, usuario_id: int, contrasena_actual: str, contrasena_nueva: str
    ) -> bool:
        """Cambia la contraseña de un usuario.
        
        Args:
            usuario_id: ID del usuario.
            contrasena_actual: Contraseña actual (verificación).
            contrasena_nueva: Nueva contraseña.
            
        Returns:
            True si se cambió correctamente.
            
        Raises:
            ValueError: Si contraseña actual es incorrecta.
        """
        usuario = await self.usuario_repo.get_by_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario no encontrado")

        # Verificar contraseña actual
        if not verify_password(contrasena_actual, usuario.contrasena_hash):
            raise ValueError("Contraseña actual incorrecta")

        # Actualizar contraseña
        usuario.contrasena_hash = hash_password(contrasena_nueva)
        updated = await self.usuario_repo.update(usuario_id, usuario)

        return updated is not None


class UsuarioUseCase:
    """Caso de uso para gestión de usuarios (CRUD)."""

    def __init__(self, usuario_repo: IUsuarioRepository):
        """Inicializa con el repositorio de usuario."""
        self.usuario_repo = usuario_repo

    async def obtener_usuario(self, usuario_id: int) -> Optional[Usuario]:
        """Obtiene los datos de un usuario por ID."""
        return await self.usuario_repo.get_by_id(usuario_id)

    async def listar_usuarios(self, skip: int = 0, limit: int = 10) -> Tuple[List[Usuario], int]:
        """Lista todos los usuarios con paginación.
        
        Returns:
            Tupla (lista de usuarios, total de usuarios).
        """
        usuarios = await self.usuario_repo.get_all(skip, limit)
        total = await self.usuario_repo.get_count()
        return usuarios, total

    async def actualizar_usuario(
        self, usuario_id: int, nombre_completo: Optional[str] = None,
        rol: Optional[str] = None, estado: Optional[str] = None
    ) -> Optional[Usuario]:
        """Actualiza los datos de un usuario."""
        usuario = await self.usuario_repo.get_by_id(usuario_id)
        if not usuario:
            return None

        if nombre_completo:
            usuario.nombre_completo = nombre_completo
        if rol:
            usuario.rol = rol
        if estado:
            usuario.estado = estado

        return await self.usuario_repo.update(usuario_id, usuario)

    async def eliminar_usuario(self, usuario_id: int) -> bool:
        """Elimina un usuario del sistema."""
        return await self.usuario_repo.delete(usuario_id)
