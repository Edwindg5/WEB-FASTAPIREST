"""Router admin — gestión de usuarios. Requiere rol=admin."""
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
    AdminUsuarioItem,
    AdminUsuarioDetalle,
    AdminUsuarioListResponse,
    AdminUsuarioEstadoUpdate,
)

router = APIRouter(prefix="/admin/usuarios", tags=["Admin — Usuarios"])


async def _registrar_auditoria(
    db: AsyncSession,
    usuario_id: int,
    accion: str,
    entidad_tipo: str,
    entidad_id: Optional[int],
    ip_cliente: str = "api",
    valores_anteriores: Optional[dict] = None,
    valores_nuevos: Optional[dict] = None,
):
    log = AuditLogModel(
        usuario_id=usuario_id,
        accion=accion,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        ip_cliente=ip_cliente,
        valores_anteriores=valores_anteriores,
        valores_nuevos=valores_nuevos,
    )
    db.add(log)
    await db.commit()


def _usuario_to_item(u: UsuarioModel) -> AdminUsuarioItem:
    return AdminUsuarioItem(
        id_usuario=u.id,
        nombre=u.nombre_completo,
        email=u.correo,
        rol=u.rol.value if hasattr(u.rol, "value") else str(u.rol),
        estado=u.estado.value if hasattr(u.estado, "value") else str(u.estado),
        fecha_registro=u.created_at,
    )


@router.get(
    "",
    response_model=AdminUsuarioListResponse,
    summary="Listar todos los usuarios",
)
async def listar_usuarios(
    rol: Optional[str] = Query(None, description="Filtrar por rol"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
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

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    usuarios = result.scalars().all()

    return AdminUsuarioListResponse(
        total=total,
        page=page,
        limit=limit,
        items=[_usuario_to_item(u) for u in usuarios],
    )


@router.get(
    "/{id}",
    response_model=AdminUsuarioDetalle,
    summary="Detalle de un usuario",
)
async def detalle_usuario(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id == id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    total_lotes_q = select(func.count()).where(LoteCafeModel.created_by == id)
    total_lotes = (await db.execute(total_lotes_q)).scalar_one()

    lotes_activos_q = select(func.count()).where(
        LoteCafeModel.created_by == id,
        LoteCafeModel.estado == "en_progreso",
    )
    lotes_activos = (await db.execute(lotes_activos_q)).scalar_one()

    item = _usuario_to_item(usuario)
    return AdminUsuarioDetalle(
        **item.model_dump(),
        total_lotes=total_lotes,
        lotes_activos=lotes_activos,
        ultimo_login=usuario.ultimo_login,
    )


@router.put(
    "/{id}/estado",
    summary="Activar o desactivar usuario",
)
async def cambiar_estado_usuario(
    id: int,
    body: AdminUsuarioEstadoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id == id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    estado_anterior = usuario.estado.value if hasattr(usuario.estado, "value") else str(usuario.estado)
    usuario.estado = body.estado
    usuario.updated_at = datetime.utcnow()
    await db.commit()

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _registrar_auditoria(
        db=db,
        usuario_id=int(current_user.get("sub")),
        accion="cambio_estado_usuario",
        entidad_tipo="usuarios",
        entidad_id=id,
        ip_cliente=ip,
        valores_anteriores={"estado": estado_anterior},
        valores_nuevos={"estado": body.estado},
    )

    return {"message": f"Estado actualizado a '{body.estado}'", "id_usuario": id}


@router.delete(
    "/{id}",
    summary="Eliminar usuario (soft delete)",
)
async def eliminar_usuario(
    id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id == id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    usuario.estado = "inactivo"
    usuario.updated_at = datetime.utcnow()
    await db.commit()

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _registrar_auditoria(
        db=db,
        usuario_id=int(current_user.get("sub")),
        accion="eliminar_usuario",
        entidad_tipo="usuarios",
        entidad_id=id,
        ip_cliente=ip,
        valores_anteriores=None,
        valores_nuevos={"estado": "inactivo"},
    )

    return {"message": "Usuario desactivado correctamente", "id_usuario": id}
