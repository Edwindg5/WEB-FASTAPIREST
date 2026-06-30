"""Router de suscripciones. Requiere JWT."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, List
from datetime import datetime, timezone

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.suscripcion import SuscripcionModel
from app.core.security import get_current_user
from app.api.v1.schemas.suscripcion import PlanInfo, SuscripcionResponse

router = APIRouter(prefix="/suscripciones", tags=["Suscripciones"])

PLANES: List[PlanInfo] = [
    PlanInfo(plan="basico", precio=99.00, moneda="MXN", descripcion="Hasta 3 lotes activos", lotes_max=3),
    PlanInfo(plan="profesional", precio=249.00, moneda="MXN", descripcion="Hasta 10 lotes activos", lotes_max=10),
    PlanInfo(plan="empresarial", precio=499.00, moneda="MXN", descripcion="Lotes ilimitados", lotes_max=-1),
]

PLAN_MAP = {p.plan: p for p in PLANES}


@router.get("/planes", response_model=List[PlanInfo])
async def listar_planes():
    return PLANES


@router.get("/mi-suscripcion", response_model=SuscripcionResponse)
async def mi_suscripcion(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    id_usuario = int(current_user.get("sub"))
    result = await db.execute(
        select(SuscripcionModel).where(SuscripcionModel.id_usuario == id_usuario)
    )
    sus = result.scalar_one_or_none()

    if not sus:
        return SuscripcionResponse(plan="prueba", estado="prueba", lotes_max=1)

    return SuscripcionResponse(
        id_suscripcion=sus.id_suscripcion,
        plan=sus.plan,
        estado=sus.estado,
        fecha_inicio=sus.fecha_inicio,
        fecha_fin=sus.fecha_fin,
        lotes_max=sus.lotes_max,
    )


async def verificar_suscripcion_lote(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Dependency que verifica si el usuario puede crear más lotes."""
    from app.infrastructure.db.models.lote_cafe import LoteCafeModel

    id_usuario = int(current_user.get("sub"))
    result = await db.execute(
        select(SuscripcionModel).where(SuscripcionModel.id_usuario == id_usuario)
    )
    sus = result.scalar_one_or_none()

    lotes_max = sus.lotes_max if sus else 1
    if lotes_max == -1:
        return current_user

    lotes_activos = (
        await db.execute(
            select(func.count()).where(
                LoteCafeModel.id_usuario == id_usuario,
                LoteCafeModel.estado == "en_proceso",
            )
        )
    ).scalar_one()

    if lotes_activos >= lotes_max:
        raise HTTPException(
            status_code=402,
            detail="Tu plan actual no permite más lotes. Actualiza tu suscripción.",
        )
    return current_user
