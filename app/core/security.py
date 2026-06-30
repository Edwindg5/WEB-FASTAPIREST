"""Utilidades de seguridad: JWT, hashing de contraseñas, etc."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.core.config import settings

# Contexto para hashing de contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash de contraseña con bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra su hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Crea un JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decodifica y valida un JWT token.
    
    Raises:
        HTTPException: Si el token es inválido o ha expirado.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(credentials: Any = Depends(security)) -> Dict[str, Any]:
    """Obtiene el usuario actual desde el token JWT.
    
    Función de inyección de dependencias para FastAPI.
    Extrae y valida el token del header Authorization.
    
    Args:
        credentials: Las credenciales HTTP (Bearer token).
        
    Returns:
        Dict con los datos del payload del token.
        
    Raises:
        HTTPException: Si el token es inválido.
    """
    token = credentials.credentials
    payload = decode_token(token)

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Obtiene el usuario actual y valida que sea administrador.
    
    Args:
        current_user: Usuario actual obtenido de get_current_user.
        
    Returns:
        Dict con los datos del usuario si es admin.
        
    Raises:
        HTTPException: Si no es administrador.
    """
    role = current_user.get("role")
    if role != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return current_user
