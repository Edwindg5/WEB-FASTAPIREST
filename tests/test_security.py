"""Tests unitarios básicos."""
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from app.domain.entities.usuario import Usuario, RolUsuario, EstadoUsuario


class TestSeguridad:
    """Tests para funciones de seguridad."""

    def test_hash_y_verify_password(self):
        """Verifica que el hash de contraseña funciona correctamente."""
        password = "MiContraseña123"
        hashed = hash_password(password)

        # El hash no debe ser igual al password
        assert hashed != password

        # Verificar contraseña correcta
        assert verify_password(password, hashed)

        # Verificar contraseña incorrecta
        assert not verify_password("OtraContraseña", hashed)

    def test_create_y_decode_token(self):
        """Verifica que la creación y decodificación de tokens funciona."""
        data = {"sub": "123", "correo": "test@example.com", "role": "admin"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

        # Decodificar y verificar
        decoded = decode_token(token)
        assert decoded["sub"] == "123"
        assert decoded["correo"] == "test@example.com"
        assert decoded["role"] == "admin"


class TestEntidadUsuario:
    """Tests para la entidad Usuario."""

    def test_crear_usuario(self):
        """Verifica creación de usuario."""
        usuario = Usuario(
            id=1,
            correo="test@example.com",
            nombre_completo="Juan Pérez",
            rol=RolUsuario.SUPERVISOR,
            estado=EstadoUsuario.ACTIVO,
            contrasena_hash="hash_seguro",
        )

        assert usuario.id == 1
        assert usuario.correo == "test@example.com"
        assert usuario.is_activo()
        assert not usuario.is_admin()

    def test_permisos_usuario(self):
        """Verifica permisos según rol."""
        admin = Usuario(
            correo="admin@example.com",
            nombre_completo="Admin",
            rol=RolUsuario.ADMIN,
            estado=EstadoUsuario.ACTIVO,
            contrasena_hash="hash",
        )

        supervisor = Usuario(
            correo="supervisor@example.com",
            nombre_completo="Supervisor",
            rol=RolUsuario.SUPERVISOR,
            estado=EstadoUsuario.ACTIVO,
            contrasena_hash="hash",
        )

        # Verificar permisos
        assert admin.is_admin()
        assert admin.puede_leer_lotes()
        assert admin.puede_modificar_lotes()

        assert not supervisor.is_admin()
        assert supervisor.puede_leer_lotes()
        assert not supervisor.puede_modificar_lotes()

    def test_usuario_inactivo_sin_permisos(self):
        """Verifica que usuario inactivo no tiene permisos."""
        usuario_inactivo = Usuario(
            correo="inactivo@example.com",
            nombre_completo="Inactivo",
            rol=RolUsuario.ADMIN,
            estado=EstadoUsuario.INACTIVO,
            contrasena_hash="hash",
        )

        assert not usuario_inactivo.is_activo()
        assert not usuario_inactivo.puede_leer_lotes()
        assert not usuario_inactivo.puede_modificar_lotes()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
