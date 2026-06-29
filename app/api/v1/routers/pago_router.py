"""Router de pagos con Mercado Pago. Requiere JWT (excepto webhook)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.pago import PagoModel
from app.infrastructure.db.models.suscripcion import SuscripcionModel
from app.infrastructure.db.models.audit_log import AuditLogModel
from app.core.security import get_current_user
from app.api.v1.schemas.pago import (
    CrearPreferenciaRequest,
    PreferenciaResponse,
    PagoResponse,
    PagoListResponse,
    WebhookPayload,
)
from app.api.v1.routers.suscripcion_router import PLAN_MAP

router = APIRouter(prefix="/pagos", tags=["Pagos"])

PRECIOS = {"basico": 99.00, "profesional": 249.00, "empresarial": 499.00}


def _get_mp_sdk():
    import mercadopago
    token = os.getenv("MP_ACCESS_TOKEN", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MercadoPago no configurado. Definir MP_ACCESS_TOKEN en .env",
        )
    return mercadopago.SDK(token)


@router.post(
    "/crear-preferencia",
    response_model=PreferenciaResponse,
    summary="Crear preferencia de pago en Mercado Pago",
)
async def crear_preferencia(
    body: CrearPreferenciaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    if body.plan not in PLAN_MAP:
        raise HTTPException(status_code=400, detail=f"Plan inválido: {body.plan}")

    plan_info = PLAN_MAP[body.plan]
    usuario_id = int(current_user.get("sub"))
    monto = plan_info.precio

    sdk = _get_mp_sdk()

    preference_data = {
        "items": [
            {
                "title": f"Suscripción {plan_info.plan.title()} — Sistema Monitoreo Café",
                "quantity": 1,
                "unit_price": monto,
                "currency_id": "MXN",
            }
        ],
        "metadata": {"usuario_id": usuario_id, "plan": body.plan},
        "back_urls": {
            "success": f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/v1/pagos/webhook",
            "failure": f"{os.getenv('FRONTEND_URL', 'http://localhost:4200')}/pago/error",
            "pending": f"{os.getenv('FRONTEND_URL', 'http://localhost:4200')}/pago/pendiente",
        },
        "auto_return": "approved",
    }

    mp_response = sdk.preference().create(preference_data)
    response_data = mp_response.get("response", {})
    preference_id = response_data.get("id", "")
    init_point = response_data.get("init_point", "")

    if not preference_id:
        raise HTTPException(status_code=502, detail="Error al crear preferencia en MercadoPago")

    pago = PagoModel(
        id_usuario=usuario_id,
        plan=body.plan,
        monto=monto,
        moneda="MXN",
        estado="pendiente",
        mp_preference_id=preference_id,
    )
    db.add(pago)
    await db.commit()

    return PreferenciaResponse(init_point=init_point, preference_id=preference_id)


@router.post("/webhook", summary="Webhook de Mercado Pago (sin JWT)")
async def webhook_mercadopago(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body_bytes = await request.body()

    secret = os.getenv("MP_WEBHOOK_SECRET", "")
    if secret:
        mp_signature = request.headers.get("x-signature", "")
        expected = hmac.new(
            secret.encode(), body_bytes, hashlib.sha256
        ).hexdigest()
        if mp_signature and not hmac.compare_digest(expected, mp_signature):
            raise HTTPException(status_code=401, detail="Firma inválida")

    import json
    try:
        payload = json.loads(body_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido")

    payment_id = None
    if "data" in payload and "id" in payload.get("data", {}):
        payment_id = str(payload["data"]["id"])
    elif "id" in payload:
        payment_id = str(payload["id"])

    if not payment_id:
        return {"status": "ignored"}

    sdk = _get_mp_sdk()
    mp_payment = sdk.payment().get(payment_id)
    payment_data = mp_payment.get("response", {})
    mp_status = payment_data.get("status", "")
    metadata = payment_data.get("metadata", {})
    usuario_id = metadata.get("usuario_id")
    plan = metadata.get("plan")

    if not usuario_id or not plan:
        preference_id = payment_data.get("preference_id")
        if preference_id:
            pago_r = await db.execute(
                select(PagoModel).where(PagoModel.mp_preference_id == preference_id)
            )
            existing = pago_r.scalar_one_or_none()
            if existing:
                usuario_id = existing.id_usuario
                plan = existing.plan

    if mp_status == "approved" and usuario_id and plan:
        pago_r = await db.execute(
            select(PagoModel).where(PagoModel.mp_preference_id == payment_data.get("preference_id"))
        )
        pago = pago_r.scalar_one_or_none()

        if pago:
            pago.estado = "aprobado"
            pago.mp_payment_id = payment_id
        else:
            plan_info = PLAN_MAP.get(plan)
            monto = plan_info.precio if plan_info else 0
            pago = PagoModel(
                id_usuario=int(usuario_id),
                plan=plan,
                monto=monto,
                moneda="MXN",
                estado="aprobado",
                mp_payment_id=payment_id,
            )
            db.add(pago)

        await db.flush()

        sus_r = await db.execute(
            select(SuscripcionModel).where(SuscripcionModel.id_usuario == int(usuario_id))
        )
        suscripcion = sus_r.scalar_one_or_none()
        plan_info = PLAN_MAP.get(plan)
        lotes_max = plan_info.lotes_max if plan_info else 1

        if suscripcion:
            suscripcion.plan = plan
            suscripcion.estado = "activa"
            suscripcion.fecha_fin = datetime.now(timezone.utc) + timedelta(days=30)
            suscripcion.lotes_max = lotes_max
            suscripcion.id_pago = pago.id
            suscripcion.updated_at = datetime.now(timezone.utc)
        else:
            suscripcion = SuscripcionModel(
                id_usuario=int(usuario_id),
                plan=plan,
                estado="activa",
                fecha_fin=datetime.now(timezone.utc) + timedelta(days=30),
                lotes_max=lotes_max,
                id_pago=pago.id,
            )
            db.add(suscripcion)

        audit = AuditLogModel(
            usuario_id=int(usuario_id),
            accion="pago_aprobado",
            entidad_tipo="pagos",
            entidad_id=pago.id,
            ip_cliente="mercadopago-webhook",
            valores_nuevos={"plan": plan, "mp_payment_id": payment_id},
        )
        db.add(audit)
        await db.commit()

    elif mp_status in ("rejected", "cancelled"):
        pago_r = await db.execute(
            select(PagoModel).where(PagoModel.mp_preference_id == payment_data.get("preference_id"))
        )
        pago = pago_r.scalar_one_or_none()
        if pago:
            pago.estado = "rechazado"
            pago.mp_payment_id = payment_id
            await db.commit()

    return {"status": "ok"}


@router.get(
    "/historial",
    response_model=PagoListResponse,
    summary="Historial de pagos del usuario",
)
async def historial_pagos(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    usuario_id = int(current_user.get("sub"))
    result = await db.execute(
        select(PagoModel)
        .where(PagoModel.id_usuario == usuario_id)
        .order_by(PagoModel.fecha_pago.desc())
    )
    pagos = result.scalars().all()

    return PagoListResponse(
        total=len(pagos),
        items=[
            PagoResponse(
                id=p.id,
                plan=p.plan,
                monto=float(p.monto),
                moneda=p.moneda,
                estado=p.estado,
                mp_preference_id=p.mp_preference_id,
                mp_payment_id=p.mp_payment_id,
                fecha_pago=p.fecha_pago,
            )
            for p in pagos
        ],
    )
