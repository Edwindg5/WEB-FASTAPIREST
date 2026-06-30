"""Casos de uso para autenticación y gestión de usuarios."""
from typing import Tuple, Optional, Dict, Any, List
from app.domain.entities.usuario import Usuario, EstadoUsuario
from app.application.interfaces.usuario_repository import IUsuarioRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token


class AuthUseCase:

    def __init__(self, usuario_repo: IUsuarioRepository):
        self.usuario_repo = usuario_repo

    async def registrar_usuario(
        self,
        email: str,
        nombre: str,
        password: str,
        rol: str = "productor",
        telefono: Optional[str] = None,
    ) -> Usuario:
        if await self.usuario_repo.usuario_exists(email):
            raise ValueError(f"El usuario con email '{email}' ya existe")

        usuario = Usuario(
            email=email,
            nombre=nombre,
            rol=rol,
            estado=EstadoUsuario.ACTIVO,
            password_hash=hash_password(password),
            telefono=telefono,
        )
        return await self.usuario_repo.create(usuario)

    async def login(self, email: str, password: str) -> Tuple[str, str, Usuario]:
        usuario = await self.usuario_repo.get_by_email(email)
        if not usuario:
            raise ValueError("Credenciales inválidas")

        if not verify_password(password, usuario.password_hash):
            raise ValueError("Credenciales inválidas")

        if not usuario.is_activo():
            raise ValueError(f"Usuario {usuario.estado}")

        rol_value = usuario.rol.value if hasattr(usuario.rol, "value") else str(usuario.rol)
        access_token = create_access_token(
            data={"sub": str(usuario.id_usuario), "email": usuario.email, "role": rol_value}
        )
        refresh_token = create_refresh_token(data={"sub": str(usuario.id_usuario)})
        return access_token, refresh_token, usuario

    async def cambiar_password(
        self, id_usuario: int, password_actual: str, password_nuevo: str
    ) -> bool:
        usuario = await self.usuario_repo.get_by_id(id_usuario)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        if not verify_password(password_actual, usuario.password_hash):
            raise ValueError("Contraseña actual incorrecta")
        usuario.password_hash = hash_password(password_nuevo)
        updated = await self.usuario_repo.update(id_usuario, usuario)
        return updated is not None


class UsuarioUseCase:

    def __init__(self, usuario_repo: IUsuarioRepository):
        self.usuario_repo = usuario_repo

    async def obtener_usuario(self, id_usuario: int) -> Optional[Usuario]:
        return await self.usuario_repo.get_by_id(id_usuario)

    async def listar_usuarios(self, skip: int = 0, limit: int = 10) -> Tuple[List[Usuario], int]:
        usuarios = await self.usuario_repo.get_all(skip, limit)
        total = await self.usuario_repo.get_count()
        return usuarios, total

    async def actualizar_usuario(
        self,
        id_usuario: int,
        nombre: Optional[str] = None,
        rol: Optional[str] = None,
        estado: Optional[str] = None,
    ) -> Optional[Usuario]:
        usuario = await self.usuario_repo.get_by_id(id_usuario)
        if not usuario:
            return None
        if nombre:
            usuario.nombre = nombre
        if rol:
            usuario.rol = rol
        if estado:
            usuario.estado = estado
        return await self.usuario_repo.update(id_usuario, usuario)

    async def eliminar_usuario(self, id_usuario: int) -> bool:
        return await self.usuario_repo.delete(id_usuario)
