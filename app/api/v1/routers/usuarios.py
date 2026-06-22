"""Router de usuarios - CRUD de usuarios (RF-01)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.api.v1.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListResponse,
    UsuarioChangePassword,
)
from app.application.use_cases.auth_use_case import AuthUseCase, UsuarioUseCase
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.usuario_repository import UsuarioRepository
from app.core.security import get_current_user, get_current_admin_user
from app.core.logging import logger

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


async def get_usuario_use_case(db: AsyncSession = Depends(get_db)) -> UsuarioUseCase:
    """Inyecta el caso de uso de usuario."""
    usuario_repo = UsuarioRepository(db)
    return UsuarioUseCase(usuario_repo)


async def get_auth_use_case(db: AsyncSession = Depends(get_db)) -> AuthUseCase:
    """Inyecta el caso de uso de autenticación."""
    usuario_repo = UsuarioRepository(db)
    return AuthUseCase(usuario_repo)


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo usuario",
    dependencies=[Depends(get_current_admin_user)],
)
async def crear_usuario(
    usuario_create: UsuarioCreate,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Crea un nuevo usuario en el sistema.
    
    Solo administradores pueden crear usuarios.
    
    Args:
        usuario_create: Datos del usuario a crear.
        
    Returns:
        UsuarioResponse con los datos del usuario creado.
        
    Raises:
        HTTPException 400: Si el correo ya existe.
        HTTPException 403: Si no es administrador.
    """
    try:
        usuario = await auth_use_case.registrar_usuario(
            correo=usuario_create.correo.lower(),
            nombre_completo=usuario_create.nombre_completo,
            contrasena=usuario_create.contrasena,
            rol=usuario_create.rol.value,
        )

        logger.info(f"Usuario creado: {usuario.correo} por admin: {current_user.get('correo')}")

        return UsuarioResponse.model_validate(usuario)
    except ValueError as e:
        logger.warning(f"Error al crear usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get(
    "/",
    response_model=UsuarioListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar usuarios",
    dependencies=[Depends(get_current_admin_user)],
)
async def listar_usuarios(
    skip: int = Query(0, ge=0, description="Cantidad a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Límite por página"),
    usuario_use_case: UsuarioUseCase = Depends(get_usuario_use_case),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Lista todos los usuarios con paginación.
    
    Solo administradores pueden listar usuarios.
    
    Args:
        skip: Registros a saltar (paginación).
        limit: Límite de registros por página.
        
    Returns:
        UsuarioListResponse con lista de usuarios.
    """
    usuarios, total = await usuario_use_case.listar_usuarios(skip, limit)

    return UsuarioListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[UsuarioResponse.model_validate(u) for u in usuarios],
    )


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalles de usuario",
)
async def obtener_usuario(
    usuario_id: int,
    usuario_use_case: UsuarioUseCase = Depends(get_usuario_use_case),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Obtiene los detalles de un usuario.
    
    Los usuarios pueden ver sus propios datos.
    Los administradores pueden ver cualquier usuario.
    
    Args:
        usuario_id: ID del usuario a obtener.
        
    Returns:
        UsuarioResponse con los datos del usuario.
        
    Raises:
        HTTPException 404: Si el usuario no existe.
        HTTPException 403: Si no tiene permisos.
    """
    # Verificar permisos
    if (
        int(current_user.get("sub")) != usuario_id
        and current_user.get("role") != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver este usuario",
        )

    usuario = await usuario_use_case.obtener_usuario(usuario_id)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return UsuarioResponse.model_validate(usuario)


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar usuario",
)
async def actualizar_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    usuario_use_case: UsuarioUseCase = Depends(get_usuario_use_case),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Actualiza los datos de un usuario.
    
    Solo administradores pueden actualizar usuarios.
    
    Args:
        usuario_id: ID del usuario a actualizar.
        usuario_update: Datos a actualizar (parcial).
        
    Returns:
        UsuarioResponse con los datos actualizados.
        
    Raises:
        HTTPException 404: Si el usuario no existe.
        HTTPException 403: Si no es administrador.
    """
    usuario = await usuario_use_case.actualizar_usuario(
        usuario_id=usuario_id,
        nombre_completo=usuario_update.nombre_completo,
        rol=usuario_update.rol.value if usuario_update.rol else None,
        estado=usuario_update.estado.value if usuario_update.estado else None,
    )

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    logger.info(f"Usuario actualizado: {usuario.correo} por admin: {current_user.get('correo')}")

    return UsuarioResponse.model_validate(usuario)


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    dependencies=[Depends(get_current_admin_user)],
)
async def eliminar_usuario(
    usuario_id: int,
    usuario_use_case: UsuarioUseCase = Depends(get_usuario_use_case),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Elimina un usuario del sistema.
    
    Solo administradores pueden eliminar usuarios.
    
    Args:
        usuario_id: ID del usuario a eliminar.
        
    Raises:
        HTTPException 404: Si el usuario no existe.
        HTTPException 403: Si no es administrador.
    """
    exito = await usuario_use_case.eliminar_usuario(usuario_id)

    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    logger.info(f"Usuario eliminado: ID {usuario_id} por admin: {current_user.get('correo')}")


@router.post(
    "/{usuario_id}/cambiar-contrasena",
    status_code=status.HTTP_200_OK,
    summary="Cambiar contraseña",
)
async def cambiar_contrasena(
    usuario_id: int,
    cambio: UsuarioChangePassword,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Cambia la contraseña de un usuario.
    
    Los usuarios solo pueden cambiar su propia contraseña.
    
    Args:
        usuario_id: ID del usuario.
        cambio: Datos con contraseña actual y nueva.
        
    Raises:
        HTTPException 403: Si intenta cambiar contraseña de otro usuario.
        HTTPException 400: Si la contraseña actual es incorrecta.
    """
    # Verificar que solo pueda cambiar la suya
    if int(current_user.get("sub")) != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puede cambiar su propia contraseña",
        )

    try:
        await auth_use_case.cambiar_contrasena(
            usuario_id=usuario_id,
            contrasena_actual=cambio.contrasena_actual,
            contrasena_nueva=cambio.contrasena_nueva,
        )

        logger.info(f"Contraseña cambiada para usuario: {usuario_id}")

        return {"message": "Contraseña cambiada exitosamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
