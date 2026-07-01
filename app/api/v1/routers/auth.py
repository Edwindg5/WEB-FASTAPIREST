"""Router de autenticación — Login, logout, refresh token."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import LoginRequest, LoginResponse, RefreshTokenRequest, TokenResponse
from app.application.use_cases.auth_use_case import AuthUseCase
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.usuario_repository import UsuarioRepository
from app.core.security import decode_token, create_access_token
from app.core.logging import logger

router = APIRouter(prefix="/auth", tags=["Autenticación"])


async def get_auth_use_case(db: AsyncSession = Depends(get_db)) -> AuthUseCase:
    return AuthUseCase(UsuarioRepository(db))


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
):
    try:
        access_token, refresh_token, usuario = await auth_use_case.login(
            email=request.email.lower(),
            password=request.password,
        )
        logger.info(f"Login exitoso: {usuario.email}")
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            id_usuario=usuario.id_usuario,
            email=usuario.email,
            nombre=usuario.nombre,
            rol=usuario.rol.value if hasattr(usuario.rol, "value") else str(usuario.rol),
        )
    except ValueError as e:
        logger.warning(f"Login fallido: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas") from e


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado") from e

    usuario = await UsuarioRepository(db).get_by_id(int(payload.get("sub")))
    if not usuario or not usuario.is_activo():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")

    rol_value = usuario.rol.value if hasattr(usuario.rol, "value") else str(usuario.rol)
    new_access_token = create_access_token(
        data={"sub": str(usuario.id_usuario), "email": usuario.email, "role": rol_value}
    )
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=request.refresh_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    return {"message": "Logout exitoso"}
