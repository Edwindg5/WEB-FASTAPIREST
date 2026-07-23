"""Router admin — gestión de usuarios. Requiere rol=administrador."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional, Dict, Any
from datetime import datetime

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.usuario import UsuarioModel, RolUsuarioEnum, EstadoUsuarioEnum
from app.infrastructure.db.models.lote_cafe import LoteCafeModel
from app.infrastructure.db.models.audit_log import AuditLogModel
from app.core.security import get_current_admin_user, hash_password
from app.api.v1.schemas.admin_usuario import (
    AdminUsuarioItem, AdminUsuarioDetalle, AdminUsuarioListResponse, AdminUsuarioEstadoUpdate,
    AdminUsuarioUpdate,
)

router = APIRouter(prefix="/admin/usuarios", tags=["Admin — Usuarios"])


async def _audit(db, id_usuario, accion, entidad, id_entidad, ip, detalles=None):
    from datetime import datetime
    log = AuditLogModel(
        id_usuario=id_usuario,
        accion=accion,
        entidad_afectada=entidad,
        id_entidad_afectada=id_entidad,
        ip_origen=ip,
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
    if rol and rol not in RolUsuarioEnum.enums:
        raise HTTPException(
            status_code=400,
            detail=f"rol inválido: '{rol}'. Valores permitidos: {', '.join(RolUsuarioEnum.enums)}",
        )
    if estado and estado not in EstadoUsuarioEnum.enums:
        raise HTTPException(
            status_code=400,
            detail=f"estado inválido: '{estado}'. Valores permitidos: {', '.join(EstadoUsuarioEnum.enums)}",
        )

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


@router.put("/{id}", response_model=AdminUsuarioDetalle)
async def actualizar_usuario(
    id: int,
    body: AdminUsuarioUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Edita los datos de un usuario (nombre, email, rol, telefono, password).

    Antes solo existía PUT /{id}/estado (activar/desactivar); el frontend
    llama a PUT /admin/usuarios/{id} para "guardar cambios" del formulario
    de edición y no había ninguna ruta que respondiera a eso, por lo que
    siempre fallaba con 404/405. Esta ruta cubre esa edición completa.
    """
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id_usuario == id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if body.rol is not None and body.rol not in RolUsuarioEnum.enums:
        raise HTTPException(
            status_code=400,
            detail=f"rol inválido: '{body.rol}'. Valores permitidos: {', '.join(RolUsuarioEnum.enums)}",
        )

    cambios: Dict[str, Any] = {}

    if body.email is not None:
        email_normalizado = body.email.strip().lower()
        if not email_normalizado:
            raise HTTPException(status_code=400, detail="El correo no puede estar vacío")
        existente = await db.execute(
            select(UsuarioModel).where(
                UsuarioModel.email == email_normalizado,
                UsuarioModel.id_usuario != id,
            )
        )
        if existente.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya existe otro usuario con ese correo")
        if usuario.email != email_normalizado:
            cambios["email"] = {"antes": usuario.email, "despues": email_normalizado}
        usuario.email = email_normalizado

    if body.nombre is not None:
        nombre_limpio = body.nombre.strip()
        if not nombre_limpio:
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")
        if usuario.nombre != nombre_limpio:
            cambios["nombre"] = {"antes": usuario.nombre, "despues": nombre_limpio}
        usuario.nombre = nombre_limpio

    if body.rol is not None and usuario.rol != body.rol:
        cambios["rol"] = {"antes": usuario.rol, "despues": body.rol}
        usuario.rol = body.rol

    if body.telefono is not None:
        usuario.telefono = body.telefono.strip() or None

    if body.password:
        usuario.password_hash = hash_password(body.password)
        cambios["password"] = "actualizada"

    await db.commit()
    await db.refresh(usuario)

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _audit(db, int(current_user.get("sub")), "actualizar_usuario", "usuarios", id, ip, cambios or None)

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
    """Elimina FÍSICAMENTE al usuario (borrado duro, no borrado lógico).

    Antes este endpoint solo hacía `usuario.estado = "inactivo"`, así que
    "eliminar" y "desactivar" (PUT /{id}/estado) terminaban haciendo lo
    mismo. Desactivar sigue siendo el borrado lógico (vía /{id}/estado);
    este endpoint ahora sí borra el registro de la tabla `usuarios`.

    La BD no tiene ON DELETE CASCADE en las FKs hacia usuarios, así que
    hay que limpiar a mano — en orden — todo lo que depende del usuario
    (y de sus lotes) antes del DELETE final, o Postgres rechaza el borrado
    por violación de llave foránea. Los registros que sí tienen valor
    histórico para otras personas (órdenes de compra, catálogo de
    productos) no se borran: solo se les quita la referencia al usuario o
    al lote (columnas nullable), para no perder ese historial.
    """
    result = await db.execute(select(UsuarioModel).where(UsuarioModel.id_usuario == id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if int(current_user.get("sub")) == id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")

    try:
        lotes_r = await db.execute(select(LoteCafeModel.id_lote).where(LoteCafeModel.id_usuario == id))
        lote_ids = [row[0] for row in lotes_r.all()]

        if lote_ids:
            await db.execute(text("DELETE FROM alertas WHERE id_lote = ANY(:ids)"), {"ids": lote_ids})
            await db.execute(text("DELETE FROM historial_eventos WHERE id_lote = ANY(:ids)"), {"ids": lote_ids})
            await db.execute(text("DELETE FROM lecturas_ambientales WHERE id_lote = ANY(:ids)"), {"ids": lote_ids})
            await db.execute(text("DELETE FROM predicciones WHERE id_lote = ANY(:ids)"), {"ids": lote_ids})
            await db.execute(text("DELETE FROM recomendaciones WHERE id_lote = ANY(:ids)"), {"ids": lote_ids})
            await db.execute(text("UPDATE catalogo_productos SET id_lote = NULL WHERE id_lote = ANY(:ids)"), {"ids": lote_ids})
            await db.execute(text("UPDATE ordenes SET id_lote = NULL WHERE id_lote = ANY(:ids)"), {"ids": lote_ids})
            await db.execute(text("DELETE FROM reportes WHERE id_lote = ANY(:ids)"), {"ids": lote_ids})

        await db.execute(text("DELETE FROM historial_eventos WHERE id_usuario = :uid"), {"uid": id})
        await db.execute(text("DELETE FROM reportes WHERE id_usuario = :uid"), {"uid": id})
        await db.execute(text("DELETE FROM pagos WHERE id_usuario = :uid"), {"uid": id})
        await db.execute(text("DELETE FROM suscripciones WHERE id_usuario = :uid"), {"uid": id})
        await db.execute(text("UPDATE ordenes SET id_usuario = NULL WHERE id_usuario = :uid"), {"uid": id})
        await db.execute(text("DELETE FROM audit_log WHERE id_usuario = :uid"), {"uid": id})

        if lote_ids:
            await db.execute(text("DELETE FROM lotes_cafe WHERE id_usuario = :uid"), {"uid": id})

        await db.execute(text("DELETE FROM usuarios WHERE id_usuario = :uid"), {"uid": id})
        await db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo eliminar el usuario: tiene datos relacionados que lo impiden.",
        ) from exc

    # El audit log de esta acción se registra DESPUÉS del commit y con el id
    # del admin que la ejecuta (no el del usuario, que ya no existe — la FK
    # de audit_log.id_usuario lo rechazaría).
    await _audit(
        db, int(current_user.get("sub")), "eliminar_usuario_fisico",
        "usuarios", id, ip, {"id_usuario_eliminado": id, "email": usuario.email},
    )
    return {"message": "Usuario eliminado permanentemente", "id_usuario": id}
