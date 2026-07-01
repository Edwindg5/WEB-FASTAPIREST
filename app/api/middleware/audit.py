"""Middleware de auditoría - registra eventos importantes."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime
import json
from app.core.logging import logger


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware que registra acciones críticas en auditoría."""

    # Endpoints que requieren auditoría
    AUDIT_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/usuarios",
        "/api/v1/lotes",
        "/api/v1/sensores",
        "/api/v1/reportes",
    ]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Intercepta la request, ejecuta el endpoint y registra auditoría."""

        should_audit = self._should_audit(request.url.path)

        # Registrar entrada (solo si la ruta requiere auditoría)
        request_body = await self._get_body(request) if should_audit else ""

        # Ejecutar endpoint
        response = await call_next(request)

        # Registrar auditoría si aplica
        if should_audit:
            await self._log_audit(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                client_ip=self._get_client_ip(request),
                body=request_body,
            )

        return response

    async def _get_body(self, request: Request) -> str:
        """Obtiene el cuerpo de la request."""
        try:
            body = await request.body()
            return body.decode("utf-8") if body else ""
        except Exception as e:
            logger.error(f"Error leyendo body: {e}")
            return ""

    def _should_audit(self, path: str) -> bool:
        """Determina si la ruta debe ser auditada."""
        return any(audit_path in path for audit_path in self.AUDIT_PATHS)

    def _get_client_ip(self, request: Request) -> str:
        """Obtiene la IP del cliente."""
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0]
        return request.client.host if request.client else "unknown"

    async def _log_audit(
        self, method: str, path: str, status_code: int, client_ip: str, body: str
    ):
        """Registra evento de auditoría."""
        audit_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "client_ip": client_ip,
            "body": body[:500],  # Limitar tamaño
        }
        
        logger.info(f"AUDIT: {json.dumps(audit_log)}")
        
        # TODO: Guardar en tabla audit_log de BD
        # await audit_repository.create(audit_log)
