"""Router admin — gestión de sensores ESP32. Requiere rol=admin."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import json
import io
import base64
import qrcode

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.sensor import SensorModel
from app.infrastructure.db.models.lote_cafe import LoteCafeModel
from app.infrastructure.db.models.audit_log import AuditLogModel
from app.core.security import get_current_admin_user
from app.api.v1.schemas.admin_sensor import (
    AdminSensorCreate,
    AdminSensorUpdate,
    AdminSensorResponse,
    AdminSensorListResponse,
    AdminSensorDetalle,
    QRResponse,
)

router = APIRouter(prefix="/admin/sensores", tags=["Admin — Sensores"])


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


async def _get_lote_nombre(db: AsyncSession, lote_id: Optional[int]) -> Optional[str]:
    if not lote_id:
        return None
    r = await db.execute(select(LoteCafeModel.nombre).where(LoteCafeModel.id == lote_id))
    return r.scalar_one_or_none()


def _sensor_to_response(sensor: SensorModel, lote_nombre: Optional[str] = None) -> AdminSensorResponse:
    return AdminSensorResponse(
        id=sensor.id,
        mac_address=sensor.mac_address,
        tipo=sensor.tipo,
        modelo=sensor.modelo,
        estado=sensor.estado or "activo",
        id_cola_mqtt=sensor.id_cola_mqtt,
        provisioning_token=sensor.provisioning_token,
        token_usado=sensor.token_usado or False,
        lote_nombre=lote_nombre,
        created_at=sensor.created_at,
    )


@router.post(
    "",
    response_model=AdminSensorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo sensor ESP32",
)
async def crear_sensor(
    body: AdminSensorCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    existing = await db.execute(
        select(SensorModel).where(SensorModel.mac_address == body.mac_address)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un sensor con esa MAC address",
        )

    id_cola_mqtt = f"sensors/{body.mac_address}/data"
    provisioning_token = str(uuid.uuid4())

    sensor = SensorModel(
        mac_address=body.mac_address,
        tipo=body.tipo,
        modelo=body.modelo,
        estado="activo",
        id_cola_mqtt=id_cola_mqtt,
        provisioning_token=provisioning_token,
        token_usado=False,
        codigo=body.mac_address.replace(":", ""),
        nombre=f"ESP32-{body.mac_address[-5:].replace(':', '')}",
        tipo_sensor=body.tipo,
    )
    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _registrar_auditoria(
        db=db,
        usuario_id=int(current_user.get("sub")),
        accion="crear_sensor",
        entidad_tipo="sensores",
        entidad_id=sensor.id,
        ip_cliente=ip,
        valores_nuevos={"mac_address": body.mac_address, "tipo": body.tipo, "modelo": body.modelo},
    )

    return _sensor_to_response(sensor)


@router.get(
    "",
    response_model=AdminSensorListResponse,
    summary="Listar todos los sensores",
)
async def listar_sensores(
    estado: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    query = select(SensorModel)
    if estado:
        query = query.where(SensorModel.estado == estado)

    result = await db.execute(query)
    sensores = result.scalars().all()

    items = []
    for s in sensores:
        lote_nombre = await _get_lote_nombre(db, s.lote_id)
        items.append(_sensor_to_response(s, lote_nombre))

    return AdminSensorListResponse(total=len(items), items=items)


@router.get(
    "/{id}",
    response_model=AdminSensorDetalle,
    summary="Detalle de un sensor",
)
async def detalle_sensor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel).where(SensorModel.id == id))
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor no encontrado")

    lote_nombre = await _get_lote_nombre(db, sensor.lote_id)

    # Historial: lotes donde el sensor ha tenido lecturas (distinct por lecturas_ambientales)
    from sqlalchemy import text
    historial_r = await db.execute(
        text(
            "SELECT DISTINCT l.id, l.nombre, l.estado "
            "FROM lotes_cafe l "
            "JOIN lecturas_ambientales la ON la.lote_id = l.id "
            "WHERE la.sensor_id = :sid "
            "ORDER BY l.id DESC"
        ),
        {"sid": id},
    )
    historial = [
        {"id_lote": r.id, "nombre": r.nombre, "estado": r.estado}
        for r in historial_r.all()
    ]

    base = _sensor_to_response(sensor, lote_nombre)
    return AdminSensorDetalle(**base.model_dump(), historial_lotes=historial)


@router.put(
    "/{id}",
    response_model=AdminSensorResponse,
    summary="Actualizar sensor",
)
async def actualizar_sensor(
    id: int,
    body: AdminSensorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel).where(SensorModel.id == id))
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor no encontrado")

    if body.estado is not None:
        sensor.estado = body.estado
    if body.modelo is not None:
        sensor.modelo = body.modelo
    sensor.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(sensor)

    lote_nombre = await _get_lote_nombre(db, sensor.lote_id)
    return _sensor_to_response(sensor, lote_nombre)


@router.get(
    "/{id}/qr",
    response_model=QRResponse,
    summary="Generar imagen QR del sensor",
)
async def generar_qr_sensor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel).where(SensorModel.id == id))
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor no encontrado")

    if not sensor.mac_address or not sensor.provisioning_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El sensor no tiene MAC address o token de provisioning",
        )

    qr_data = json.dumps({"esp32_id": sensor.mac_address, "token": sensor.provisioning_token})
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return QRResponse(qr_base64=f"data:image/png;base64,{b64}")
