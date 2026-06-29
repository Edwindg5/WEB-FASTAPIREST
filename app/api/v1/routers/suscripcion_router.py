"""Router de suscripciones. Requiere JWT."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
from datetime import datetime, timezone

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.suscripcion import SuscripcionModel
from app.core.security import get_current_user
from app.api.v1.schemas.suscripcion import PlanInfo, SuscripcionResponse

router = APIRouter(prefix="/suscripciones", tags=["Suscripciones"])

PLANES: List[PlanInfo] = [
    PlanInfo(
        plan="basico",
        precio=99.00,
        moneda="MXN",
        descripcion="Hasta 3 lotes activos",
        lotes_max=3,
    ),
    PlanInfo(
        plan="profesional",
        precio=249.00,
        moneda="MXN",
        descripcion="Hasta 10 lotes activos",
        lotes_max=10,
    ),
    PlanInfo(
        plan="empresarial",
        precio=499.00,
        moneda="MXN",
        descripcion="Lotes ilimitados",
        lotes_max=-1,
    ),
]

PLAN_MAP = {p.plan: p for p in PLANES}


@router.get("/planes", response_model=List[PlanInfo], summary="Listar planes disponibles")
async def listar_planes():
    return PLANES


@router.get(
    "/mi-suscripcion",
    response_model=SuscripcionResponse,
    summary="Suscripción actual del usuario",
)
async def mi_suscripcion(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    usuario_id = int(current_user.get("sub"))
    result = await db.execute(
        select(SuscripcionModel).where(SuscripcionModel.id_usuario == usuario_id)
    )
    suscripcion = result.scalar_one_or_none()

    if not suscripcion:
        return SuscripcionResponse(plan="prueba", estado="prueba", lotes_max=1)

    return SuscripcionResponse(
        id=suscripcion.id,
        plan=suscripcion.plan,
        estado=suscripcion.estado,
        fecha_inicio=suscripcion.fecha_inicio,
        fecha_fin=suscripcion.fecha_fin,
        lotes_max=suscripcion.lotes_max,
    )


async def verificar_suscripcion_lote(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Dependency: verifica que el usuario pueda crear más lotes según su plan."""
    from fastapi import HTTPException
    from sqlalchemy import func
    from app.infrastructure.db.models.lote_cafe import LoteCafeModel

    usuario_id = int(current_user.get("sub"))

    result = await db.execute(
        select(SuscripcionModel).where(SuscripcionModel.id_usuario == usuario_id)
    )
    suscripcion = result.scalar_one_or_none()

    if suscripcion is None:
        lotes_max = 1
        activa = False
    else:
        activa = (
            suscripcion.estado == "activa"
            and (suscripcion.fecha_fin is None or suscripcion.fecha_fin > datetime.now(timezone.utc))
        )
        lotes_max = suscripcion.lotes_max

    if lotes_max == -1:
        return current_user

    lotes_activos = (
        await db.execute(
            select(func.count()).where(
                LoteCafeModel.created_by == usuario_id,
                LoteCafeModel.estado == "en_progreso",
            )
        )
    ).scalar_one()

    if lotes_activos >= lotes_max:
        raise HTTPException(
            status_code=402,
            detail="Tu plan actual no permite más lotes. Actualiza tu suscripción.",
        )

    return current_user
