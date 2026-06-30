"""Router admin — gestión de usuarios. Requiere rol=administrador."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, Any
from datetime import datetime

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.usuario import UsuarioModel
from app.infrastructure.db.models.lote_cafe import LoteCafeModel
from app.infrastructure.db.models.audit_log import AuditLogModel
from app.core.security import get_current_admin_user
from app.api.v1.schemas.admin_usuario import (
    AdminUsuarioItem, AdminUsuarioDetalle, AdminUsuarioListResponse, AdminUsuarioEstadoUpdate,
)

router = APIRouter(prefix="/admin/usuarios", tags=["Admin — Usuarios"])


async def _audit(db, id_usuario, accion, entidad, id_entidad, ip, detalles=None):
    from datetime import datetime
    log = AuditLogModel(
        id_usuario=id_usuario,
        accion=accion,
        entidad=entidad,
        id_entidad=id_entidad,
        ip_address=ip,
        detalles=detalles,
        fecha_hora=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()


def _to_item(u: UsuarioModel) -> AdminUsuarioItem:
    return AdminUsuarioItem(
        id_usuario=u.id_usuario,
        nombre=u.nombre,
        email=u.email,
        rol=u.rol,
        estado=u.estado,
        fecha_registro=u.fecha_registro or datetime.utcnow(),
    )


@router.get("", response_model=AdminUsuarioListResponse)
async def listar_usuarios(
    rol: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    query = select(UsuarioModel)
    if rol:
        query = query.where(UsuarioModel.rol == rol)
    if estado:
        query = query.where(UsuarioModel.estado == estado)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    usuarios = result.scalars().all()

    return AdminUsuarioListResponse(
        total=total, page=page, limit=limit,
        items=[_to_item(u) for u in usuarios],
    )


@router.get("/{id}", response_model=AdminUsuarioDetalle)
async def detalle_usuario(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id_usuario == id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    total_lotes = (
        await db.execute(select(func.count()).where(LoteCafeModel.id_usuario == id))
    ).scalar_one()
    lotes_activos = (
        await db.execute(
            select(func.count()).where(LoteCafeModel.id_usuario == id, LoteCafeModel.estado == "en_proceso")
        )
    ).scalar_one()

    item = _to_item(usuario)
    return AdminUsuarioDetalle(
        **item.model_dump(),
        total_lotes=total_lotes,
        lotes_activos=lotes_activos,
        ultimo_login=None,
    )


@router.put("/{id}/estado")
async def cambiar_estado_usuario(
    id: int,
    body: AdminUsuarioEstadoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id_usuario == id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    estado_anterior = usuario.estado
    usuario.estado = body.estado
    await db.commit()

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _audit(
        db, int(current_user.get("sub")), "cambio_estado_usuario",
        "usuarios", id, ip,
        {"antes": estado_anterior, "despues": body.estado},
    )
    return {"message": f"Estado actualizado a '{body.estado}'", "id_usuario": id}


@router.delete("/{id}")
async def eliminar_usuario(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id_usuario == id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.estado = "inactivo"
    await db.commit()

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _audit(
        db, int(current_user.get("sub")), "eliminar_usuario",
        "usuarios", id, ip, {"estado": "inactivo"},
    )
    return {"message": "Usuario desactivado", "id_usuario": id}
