"""Configuración pytest - fixtures compartidas."""
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.db.database import get_db_sync
from app.infrastructure.db.models.usuario import Base
from app.core.security import hash_password

# Base de datos para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """Crea una BD nueva para cada test."""
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_sync] = override_get_db

    yield TestingSessionLocal()

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db) -> TestClient:
    """Cliente HTTP para tests."""
    return TestClient(app)


@pytest.fixture
def usuario_admin_db(db: Session):
    """Fixture que crea un usuario admin en la BD."""
    from app.infrastructure.db.models.usuario import UsuarioModel

    usuario = UsuarioModel(
        correo="admin@test.local",
        nombre_completo="Admin Test",
        rol="admin",
        estado="activo",
        contrasena_hash=hash_password("AdminPassword123"),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture
def usuario_supervisor_db(db: Session):
    """Fixture que crea un usuario supervisor en la BD."""
    from app.infrastructure.db.models.usuario import UsuarioModel

    usuario = UsuarioModel(
        correo="supervisor@test.local",
        nombre_completo="Supervisor Test",
        rol="supervisor",
        estado="activo",
        contrasena_hash=hash_password("SuperPassword123"),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
