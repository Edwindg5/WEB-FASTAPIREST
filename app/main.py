"""Punto de entrada de la aplicación FastAPI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import logger
from app.api.middleware.audit import AuditMiddleware
from app.api.middleware.encryption_middleware import EncryptionMiddleware
from app.api.middleware.exception_handlers import setup_exception_handlers
from app.api.v1.routers import auth, usuarios
from app.api.v1.routers import (
    admin_usuarios_router,
    admin_sensores_router,
    admin_dashboard_router,
    admin_reportes_router,
    admin_auditoria_router,
    suscripcion_router,
    pago_router,
    seguridad_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando API Web - Sistema Monitoreo Café")
    yield
    logger.info("Cerrando aplicación")


app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(EncryptionMiddleware)
app.add_middleware(AuditMiddleware)

setup_exception_handlers(app)

# Routers existentes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")

# Admin — Parte 1
app.include_router(admin_usuarios_router.router, prefix="/api/v1")
app.include_router(admin_sensores_router.router, prefix="/api/v1")

# Admin — Parte 2
app.include_router(admin_dashboard_router.router, prefix="/api/v1")
app.include_router(admin_reportes_router.router, prefix="/api/v1")
app.include_router(admin_auditoria_router.router, prefix="/api/v1")

# Pagos y suscripciones — Parte 3
app.include_router(suscripcion_router.router, prefix="/api/v1")
app.include_router(pago_router.router, prefix="/api/v1")

# Seguridad / cifrado — Parte 4
app.include_router(seguridad_router.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "titulo": settings.app_title,
        "descripcion": settings.app_description,
        "version": settings.app_version,
        "documentacion": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
