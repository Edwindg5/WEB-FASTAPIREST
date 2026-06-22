"""Conexión y sesión de base de datos."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Engine síncrono (para desarrollo y pruebas simples)
sync_engine = create_engine(
    settings.database_url,
    echo=settings.sqlalchemy_echo,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
    class_=Session,
)


# Engine asíncrono (producción)
async_engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.sqlalchemy_echo,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency para inyectar sesión de base de datos en endpoints."""
    async with AsyncSessionLocal() as session:
        yield session


def get_db_sync() -> Session:
    """Dependency síncrona para sesión de base de datos."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
