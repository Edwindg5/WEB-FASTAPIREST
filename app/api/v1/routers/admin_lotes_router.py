"""Router admin — creación de lotes de café. Requiere rol=administrador."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import io
import qrcode

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.lote_cafe import LoteCafeModel
from app.infrastructure.db.models.sensor import SensorModel
from app.infrastructure.db.models.usuario import UsuarioModel
from app.infrastructure.db.models.audit_log import AuditLogModel
from app.core.config import settings
from app.core.security import get_current_admin_user, hash_password
from app.api.v1.schemas.admin_lote import AdminLoteCreate, AdminLoteResponse

router = APIRouter(prefix="/admin/lotes", tags=["Admin — Lotes"])

# Cache en memoria del id_usuario placeholder, para no consultarlo en cada request.
_placeholder_usuario_id: Optional[int] = None


async def _audit(db, id_usuario, accion, id_entidad, ip, detalles=None):
    log = AuditLogModel(
        id_usuario=id_usuario,
        accion=accion,
        entidad_afectada="lotes_cafe",
        id_entidad_afectada=id_entidad,
        ip_origen=ip,
        detalles=detalles,
        fecha_hora=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()


async def _get_placeholder_usuario_id(db: AsyncSession) -> int:
    """Obtiene el id_usuario reservado para lotes sin reclamar, creándolo si no existe."""
    global _placeholder_usuario_id
    if _placeholder_usuario_id is not None:
        return _placeholder_usuario_id

    result = await db.execute(select(UsuarioModel).where(UsuarioModel.email == settings.placeholder_lote_email))
    usuario = result.scalar_one_or_none()

    if usuario is None:
        usuario = UsuarioModel(
            nombre="Lote sin asignar",
            email=settings.placeholder_lote_email,
            password_hash=hash_password(str(uuid.uuid4())),
            rol="productor",
            estado="activo",
            fecha_registro=datetime.utcnow(),
        )
        db.add(usuario)
        try:
            await db.commit()
            await db.refresh(usuario)
        except IntegrityError:
            # Otra request lo creó primero (email es unique) — recuperamos el existente.
            await db.rollback()
            result = await db.execute(select(UsuarioModel).where(UsuarioModel.email == settings.placeholder_lote_email))
            usuario = result.scalar_one_or_none()

    _placeholder_usuario_id = usuario.id_usuario
    return _placeholder_usuario_id


def _to_response(lote: LoteCafeModel) -> AdminLoteResponse:
    return AdminLoteResponse(
        id_lote=lote.id_lote,
        id_usuario=lote.id_usuario,
        id_sensor=lote.id_sensor,
        nombre_lote=lote.nombre_lote,
        variedad=lote.variedad,
        tipo_proceso=lote.tipo_proceso,
        peso_kg=float(lote.peso_kg) if lote.peso_kg is not None else None,
        ubicacion=lote.ubicacion,
        codigo_qr=lote.codigo_qr,
        estado=lote.estado,
        fecha_inicio_secado=lote.fecha_inicio_secado,
        fecha_fin_secado=lote.fecha_fin_secado,
        linked_at=lote.linked_at,
        created_at=lote.created_at,
    )


@router.post("", response_model=AdminLoteResponse, status_code=status.HTTP_201_CREATED)
async def crear_lote(
    body: AdminLoteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    sensor_r = await db.execute(select(SensorModel).where(SensorModel.id_sensor == body.id_sensor))
    if sensor_r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Sensor con id {body.id_sensor} no encontrado")

    id_usuario_placeholder = await _get_placeholder_usuario_id(db)

    lote = LoteCafeModel(
        nombre_lote=body.nombre_lote,
        variedad=body.variedad,
        tipo_proceso=body.tipo_proceso,
        peso_kg=body.peso_kg,
        ubicacion=body.ubicacion,
        id_sensor=body.id_sensor,
        id_usuario=id_usuario_placeholder,
        linked_at=None,
        codigo_qr=str(uuid.uuid4()),
        estado="en_proceso",
        created_at=datetime.utcnow(),
    )
    db.add(lote)
    await db.commit()
    await db.refresh(lote)

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _audit(
        db, int(current_user.get("sub")), "crear_lote", lote.id_lote, ip,
        {"nombre_lote": body.nombre_lote, "id_sensor": body.id_sensor},
    )

    return _to_response(lote)


@router.get("/{id}/qr-imagen", summary="Descargar imagen QR del lote")
async def qr_imagen_lote(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(LoteCafeModel).where(LoteCafeModel.id_lote == id))
    lote = result.scalar_one_or_none()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if not lote.codigo_qr:
        raise HTTPException(status_code=400, detail="El lote no tiene código QR asignado")

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(lote.codigo_qr)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return Response(
        content=buffer.read(),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="lote_{id}_qr.png"'},
    )
