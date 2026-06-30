"""Schemas Pydantic para autenticación."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=1, description="Contraseña")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    id_usuario: int
    email: str
    nombre: str
    rol: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token válido")
