"""Router admin — auditoría. Requiere rol=administrador."""
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
        query = query.where(AuditLogModel.id_usuario == id_usuario)
    if accion:
        query = query.where(AuditLogModel.accion.ilike(f"%{accion}%"))
    if desde:
        query = query.where(AuditLogModel.fecha_hora >= datetime.strptime(desde, "%Y-%m-%d"))
    if hasta:
        hasta_dt = datetime.strptime(hasta, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.where(AuditLogModel.fecha_hora <= hasta_dt)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(AuditLogModel.fecha_hora.desc()).offset(offset).limit(limit))
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id_log": log.id_log,
                "id_usuario": log.id_usuario,
                "accion": log.accion,
                "entidad": log.entidad,
                "id_entidad": log.id_entidad,
                "detalles": log.detalles,
                "ip_address": log.ip_address,
                "fecha_hora": log.fecha_hora,
            }
            for log in logs
        ],
    }
