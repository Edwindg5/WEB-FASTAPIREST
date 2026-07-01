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
    CrearPreferenciaRequest, PreferenciaResponse, PagoResponse, PagoListResponse,
)
from app.api.v1.routers.suscripcion_router import PLAN_MAP

router = APIRouter(prefix="/pagos", tags=["Pagos"])


def _get_mp_sdk():
    import mercadopago
    token = os.getenv("MP_ACCESS_TOKEN", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MercadoPago no configurado. Definir MP_ACCESS_TOKEN en .env",
        )
    return mercadopago.SDK(token)


@router.post("/crear-preferencia", response_model=PreferenciaResponse)
async def crear_preferencia(
    body: CrearPreferenciaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    if body.plan not in PLAN_MAP:
        raise HTTPException(status_code=400, detail=f"Plan inválido: {body.plan}")

    plan_info = PLAN_MAP[body.plan]
    id_usuario = int(current_user.get("sub"))
    monto = plan_info.precio

    sdk = _get_mp_sdk()
    preference_data = {
        "items": [{
            "title": f"Suscripción {plan_info.plan.title()} — Monitoreo Café",
            "quantity": 1,
            "unit_price": monto,
            "currency_id": "MXN",
        }],
        "metadata": {"id_usuario": id_usuario, "plan": body.plan},
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

    # Crear o actualizar suscripción en estado pendiente
    sus_r = await db.execute(select(SuscripcionModel).where(SuscripcionModel.id_usuario == id_usuario))
    sus = sus_r.scalar_one_or_none()
    if not sus:
        sus = SuscripcionModel(
            id_usuario=id_usuario, plan=body.plan, estado="pendiente",
            fecha_inicio=datetime.now(timezone.utc), lotes_max=1,
        )
        db.add(sus)
        await db.flush()

    pago = PagoModel(
        id_usuario=id_usuario,
        id_suscripcion=sus.id_suscripcion,
        monto=monto,
        moneda="MXN",
        estado="pendiente",
        mp_preference_id=preference_id,
        fecha_pago=datetime.now(timezone.utc),
    )
    db.add(pago)
    await db.commit()

    return PreferenciaResponse(init_point=init_point, preference_id=preference_id)


@router.post("/webhook", summary="Webhook de Mercado Pago (sin JWT)")
async def webhook_mercadopago(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body_bytes = await request.body()
        if not body_bytes:
            return {"status": "ignored", "reason": "empty body"}
    except Exception as e:
        from app.core.logging import logger
        logger.warning(f"Webhook recibido con body inválido o desconexión: {e}")
        return {"status": "ignored", "reason": "invalid or empty body"}

    secret = os.getenv("MP_WEBHOOK_SECRET", "")
    if secret:
        mp_signature = request.headers.get("x-signature", "")
        expected = hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
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
    id_usuario = metadata.get("id_usuario")
    plan = metadata.get("plan")

    # Buscar pago por preference_id si no hay metadata
    if not id_usuario or not plan:
        pref_id = payment_data.get("preference_id")
        if pref_id:
            p_r = await db.execute(select(PagoModel).where(PagoModel.mp_preference_id == pref_id))
            existing = p_r.scalar_one_or_none()
            if existing:
                id_usuario = existing.id_usuario
                plan = PLAN_MAP.get(existing.id_suscripcion, None)

    if mp_status == "approved" and id_usuario:
        pref_id = payment_data.get("preference_id")
        pago_r = await db.execute(select(PagoModel).where(PagoModel.mp_preference_id == pref_id))
        pago = pago_r.scalar_one_or_none()

        if pago:
            pago.estado = "aprobado"
            pago.mp_payment_id = payment_id
        else:
            pago = PagoModel(
                id_usuario=int(id_usuario), monto=0, moneda="MXN",
                estado="aprobado", mp_payment_id=payment_id,
                fecha_pago=datetime.now(timezone.utc),
            )
            db.add(pago)
        await db.flush()

        sus_r = await db.execute(
            select(SuscripcionModel).where(SuscripcionModel.id_usuario == int(id_usuario))
        )
        sus = sus_r.scalar_one_or_none()
        plan_info = PLAN_MAP.get(plan or "basico")
        lotes_max = plan_info.lotes_max if plan_info else 1

        if sus:
            sus.plan = plan or sus.plan
            sus.estado = "activa"
            sus.fecha_fin = datetime.now(timezone.utc) + timedelta(days=30)
            sus.lotes_max = lotes_max
        else:
            sus = SuscripcionModel(
                id_usuario=int(id_usuario), plan=plan or "basico", estado="activa",
                fecha_inicio=datetime.now(timezone.utc),
                fecha_fin=datetime.now(timezone.utc) + timedelta(days=30),
                lotes_max=lotes_max,
            )
            db.add(sus)

        audit = AuditLogModel(
            id_usuario=int(id_usuario), accion="pago_aprobado", entidad="pagos",
            id_entidad=pago.id_pago, ip_address="mercadopago-webhook",
            detalles={"plan": plan, "mp_payment_id": payment_id},
            fecha_hora=datetime.utcnow(),
        )
        db.add(audit)
        await db.commit()

    elif mp_status in ("rejected", "cancelled"):
        pref_id = payment_data.get("preference_id")
        p_r = await db.execute(select(PagoModel).where(PagoModel.mp_preference_id == pref_id))
        pago = p_r.scalar_one_or_none()
        if pago:
            pago.estado = "rechazado"
            pago.mp_payment_id = payment_id
            await db.commit()

    return {"status": "ok"}


@router.get("/historial", response_model=PagoListResponse)
async def historial_pagos(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    id_usuario = int(current_user.get("sub"))
    result = await db.execute(
        select(PagoModel).where(PagoModel.id_usuario == id_usuario).order_by(PagoModel.fecha_pago.desc())
    )
    pagos = result.scalars().all()

    return PagoListResponse(
        total=len(pagos),
        items=[
            PagoResponse(
                id_pago=p.id_pago,
                id_suscripcion=p.id_suscripcion,
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
