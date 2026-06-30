"""Router de usuarios — CRUD."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.api.v1.schemas.usuario import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse,
    UsuarioListResponse, UsuarioChangePassword,
)
from app.application.use_cases.auth_use_case import AuthUseCase, UsuarioUseCase
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.usuario_repository import UsuarioRepository
from app.core.security import get_current_user, get_current_admin_user
from app.core.logging import logger

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


async def get_usuario_use_case(db: AsyncSession = Depends(get_db)) -> UsuarioUseCase:
    return UsuarioUseCase(UsuarioRepository(db))


async def get_auth_use_case(db: AsyncSession = Depends(get_db)) -> AuthUseCase:
    return AuthUseCase(UsuarioRepository(db))


def _to_response(usuario) -> UsuarioResponse:
    from app.domain.entities.usuario import RolUsuario, EstadoUsuario
    rol = usuario.rol.value if hasattr(usuario.rol, "value") else str(usuario.rol)
    estado = usuario.estado.value if hasattr(usuario.estado, "value") else str(usuario.estado)
    return UsuarioResponse(
        id_usuario=usuario.id_usuario,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=RolUsuario(rol),
        estado=EstadoUsuario(estado),
        telefono=usuario.telefono,
        fecha_registro=usuario.fecha_registro,
    )


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    usuario_create: UsuarioCreate,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    try:
        usuario = await auth_use_case.registrar_usuario(
            email=usuario_create.email.lower(),
            nombre=usuario_create.nombre,
            password=usuario_create.password,
            rol=usuario_create.rol.value,
            telefono=usuario_create.telefono,
        )
        logger.info(f"Usuario creado: {usuario.email}")
        return _to_response(usuario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/", response_model=UsuarioListResponse)
async def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    usuario_use_case: UsuarioUseCase = Depends(get_usuario_use_case),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    usuarios, total = await usuario_use_case.listar_usuarios(skip, limit)
    return UsuarioListResponse(
        total=total, skip=skip, limit=limit,
        items=[_to_response(u) for u in usuarios],
    )


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: int,
    usuario_use_case: UsuarioUseCase = Depends(get_usuario_use_case),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    if (
        int(current_user.get("sub")) != usuario_id
        and current_user.get("role") != "administrador"
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos")

    usuario = await usuario_use_case.obtener_usuario(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return _to_response(usuario)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    usuario_use_case: UsuarioUseCase = Depends(get_usuario_use_case),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    usuario = await usuario_use_case.actualizar_usuario(
        id_usuario=usuario_id,
        nombre=usuario_update.nombre,
        rol=usuario_update.rol.value if usuario_update.rol else None,
        estado=usuario_update.estado.value if usuario_update.estado else None,
    )
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return _to_response(usuario)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    usuario_id: int,
    usuario_use_case: UsuarioUseCase = Depends(get_usuario_use_case),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    exito = await usuario_use_case.eliminar_usuario(usuario_id)
    if not exito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")


@router.post("/{usuario_id}/cambiar-password", status_code=status.HTTP_200_OK)
async def cambiar_password(
    usuario_id: int,
    cambio: UsuarioChangePassword,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    if int(current_user.get("sub")) != usuario_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puede cambiar su propia contraseña")
    try:
        await auth_use_case.cambiar_password(
            id_usuario=usuario_id,
            password_actual=cambio.password_actual,
            password_nuevo=cambio.password_nuevo,
        )
        return {"message": "Contraseña cambiada exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
