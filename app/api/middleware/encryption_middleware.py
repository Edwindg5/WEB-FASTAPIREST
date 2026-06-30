"""Middleware de anonimización (Patrón: Interceptor/Pipe).

Intercepta responses GET y anonimiza campos sensibles para usuarios no-admin.
"""
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.metadata_mapping import SENSITIVE_FIELDS
from app.core.encryption import encryption_service


class EncryptionMiddleware(BaseHTTPMiddleware):
    """Anonimiza campos sensibles en responses para usuarios no-admin."""

    PROTECTED_PREFIXES = ["/api/v1/admin/usuarios", "/api/v1/admin/sensores"]

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if request.method != "GET":
            return response

        if not any(request.url.path.startswith(p) for p in self.PROTECTED_PREFIXES):
            return response

        role = self._extract_role(request)
        if role == "administrador":
            return response

        return await self._anonymize_response(response)

    def _extract_role(self, request: Request) -> str:
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return ""
        try:
            from app.core.security import decode_token
            payload = decode_token(auth[7:])
            return payload.get("role", "")  # "administrador" | "supervisor" | "productor"
        except Exception:
            return ""

    async def _anonymize_response(self, response: Response) -> Response:
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            data = json.loads(body)
            data = self._apply_anonymization(data)
            return JSONResponse(content=data, status_code=response.status_code, headers=dict(response.headers))
        except Exception:
            return response

    def _apply_anonymization(self, data):
        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                if k in ("email", "correo") and isinstance(v, str):
                    result[k] = encryption_service.anonymize_email(v)
                elif k == "telefono" and isinstance(v, str):
                    result[k] = encryption_service.anonymize_phone(v)
                elif k == "provisioning_token" and isinstance(v, str):
                    result[k] = "***"
                elif k == "mp_payment_id" and isinstance(v, str):
                    result[k] = "***"
                else:
                    result[k] = self._apply_anonymization(v)
            return result
        elif isinstance(data, list):
            return [self._apply_anonymization(item) for item in data]
        return data
