"""Punto de entrada de la aplicación FastAPI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import logger
from app.api.middleware.audit import AuditMiddleware
from app.api.middleware.exception_handlers import setup_exception_handlers
from app.api.v1.routers import auth, usuarios

# Simulación de inicialización
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja inicio y cierre de la aplicación."""
    # Startup
    logger.info("🚀 Iniciando API Web - Sistema Monitoreo Café")
    yield
    # Shutdown
    logger.info("🛑 Cerrando aplicación")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configurar CORS - Solo desde el frontend Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de auditoría
app.add_middleware(AuditMiddleware)

# Configurar exception handlers
setup_exception_handlers(app)

# Incluir routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")

# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint para verificar que la API está corriendo."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
    }


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información de la API."""
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
