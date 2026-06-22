"""Router de autenticación - Login, logout, refresh token."""
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
    """Inyecta el caso de uso de autenticación."""
    usuario_repo = UsuarioRepository(db)
    return AuthUseCase(usuario_repo)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login de usuario",
    responses={
        200: {"description": "Login exitoso"},
        401: {"description": "Credenciales inválidas"},
    }
)
async def login(
    request: LoginRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_use_case),
):
    """Autentica un usuario y retorna JWT tokens.
    
    Genera un access token (corta duración) y refresh token (larga duración)
    para la autenticación de endpoints posteriores.
    
    Args:
        request: Contiene correo y contraseña del usuario.
        
    Returns:
        LoginResponse con tokens y datos del usuario.
        
    Raises:
        HTTPException 401: Si credenciales son inválidas o usuario no está activo.
    """
    try:
        access_token, refresh_token, usuario = await auth_use_case.login(
            correo=request.correo.lower(),
            contrasena=request.contrasena,
        )

        logger.info(f"Login exitoso para usuario: {usuario.correo}")

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            usuario_id=usuario.id,
            correo=usuario.correo,
            nombre_completo=usuario.nombre_completo,
            rol=usuario.rol.value,
        )
    except ValueError as e:
        logger.warning(f"Intento de login fallido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        ) from e


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Renovar access token",
)
async def refresh_token(
    request: RefreshTokenRequest,
):
    """Renueva el access token usando un refresh token válido.
    
    Args:
        request: Contiene el refresh token válido.
        
    Returns:
        TokenResponse con nuevo access token.
        
    Raises:
        HTTPException 401: Si el refresh token es inválido.
    """
    try:
        payload = decode_token(request.refresh_token)
        
        # Verificar que sea un refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )

        # Generar nuevo access token
        user_id = payload.get("sub")
        new_access_token = create_access_token(
            data={"sub": user_id}
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=request.refresh_token,
            token_type="bearer",
        )
    except Exception as e:
        logger.error(f"Error en refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        ) from e


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout de usuario",
    responses={
        200: {"description": "Logout exitoso"},
    }
)
async def logout():
    """Realiza logout del usuario.
    
    Nota: En una arquitectura JWT sin sesiones en servidor,
    el logout es principalmente para notificar al cliente.
    El cliente debe descartar el token.
    
    En caso de requerir revocación de tokens, se necesaría
    una lista negra (blacklist) o almacenar sesiones activas.
    """
    logger.info("Usuario realizó logout")
    return {"message": "Logout exitoso"}
