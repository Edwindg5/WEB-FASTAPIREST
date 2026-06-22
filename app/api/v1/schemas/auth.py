"""Schemas Pydantic para autenticación."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request para login de usuario."""
    correo: EmailStr = Field(..., description="Email del usuario")
    contrasena: str = Field(..., min_length=1, description="Contraseña")


class TokenResponse(BaseModel):
    """Response con tokens JWT."""
    access_token: str = Field(..., description="Access token (Bearer)")
    refresh_token: str = Field(..., description="Refresh token para renovar")
    token_type: str = Field(default="bearer", description="Tipo de token")


class LoginResponse(BaseModel):
    """Response completa del login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario_id: int
    correo: str
    nombre_completo: str
    rol: str


class RefreshTokenRequest(BaseModel):
    """Request para renovar access token."""
    refresh_token: str = Field(..., description="Refresh token válido")
