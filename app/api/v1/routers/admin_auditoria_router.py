"""Router admin — auditoría. Requiere rol=admin."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, Optional
from datetime import datetime

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.audit_log import AuditLogModel
from app.core.security import get_current_admin_user

router = APIRouter(prefix="/admin/auditoria", tags=["Admin — Auditoría"])


@router.get("", summary="Consultar logs de auditoría")
async def listar_auditoria(
    id_usuario: Optional[int] = Query(None),
    accion: Optional[str] = Query(None),
    desde: Optional[str] = Query(None, description="YYYY-MM-DD"),
    hasta: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    query = select(AuditLogModel)

    if id_usuario:
        query = query.where(AuditLogModel.usuario_id == id_usuario)
    if accion:
        query = query.where(AuditLogModel.accion.ilike(f"%{accion}%"))
    if desde:
        desde_dt = datetime.strptime(desde, "%Y-%m-%d")
        query = query.where(AuditLogModel.created_at >= desde_dt)
    if hasta:
        hasta_dt = datetime.strptime(hasta, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.where(AuditLogModel.created_at <= hasta_dt)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    offset = (page - 1) * limit
    result = await db.execute(
        query.order_by(AuditLogModel.created_at.desc()).offset(offset).limit(limit)
    )
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": log.id,
                "usuario_id": log.usuario_id,
                "accion": log.accion,
                "entidad_tipo": log.entidad_tipo,
                "entidad_id": log.entidad_id,
                "valores_anteriores": log.valores_anteriores,
                "valores_nuevos": log.valores_nuevos,
                "ip_cliente": log.ip_cliente,
                "fecha_hora": log.created_at,
            }
            for log in logs
        ],
    }
