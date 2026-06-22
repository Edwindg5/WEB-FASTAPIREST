"""Tests de integración para los endpoints de autenticación."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.usuario import UsuarioModel, Base
from app.core.security import hash_password


# Engine en memoria para tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Crea una base de datos en memoria para tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    AsyncSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield AsyncSessionLocal


@pytest.fixture
def override_get_db(test_db):
    """Override de la dependencia get_db."""
    async def _override():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = _override


@pytest.mark.asyncio
async def test_login_fallido(override_get_db):
    """Test: Login con credenciales inválidas debe fallar."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "correo": "noexiste@example.com",
                "contrasena": "cualquierPassword123",
            },
        )

        assert response.status_code == 401
        assert "Credenciales inválidas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_health_check():
    """Test: Health check debe retornar OK."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
