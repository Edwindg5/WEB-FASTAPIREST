"""Manejador centralizado de excepciones."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from app.core.logging import logger


def setup_exception_handlers(app: FastAPI):
    """Configura los handlers de excepciones para la app."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Maneja errores de validación de Pydantic."""
        logger.warning(f"Error de validación en {request.url.path}: {exc}")
        
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"][1:]),
                "message": error["msg"],
                "type": error["type"],
            })

        return JSONResponse(
            status_code=422,
            content={
                "detail": "Error de validación",
                "errors": errors,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Maneja excepciones HTTP."""
        logger.warning(f"HTTPException en {request.url.path}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Maneja excepciones genéricas no anticipadas."""
        logger.error(f"Error no manejado en {request.url.path}: {str(exc)}", exc_info=True)
        
        # No exponer detalles internos en producción
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"},
        )
