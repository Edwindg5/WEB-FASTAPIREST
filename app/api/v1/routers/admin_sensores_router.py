"""Router admin — gestión de sensores ESP32. Requiere rol=administrador."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import json
import io
import base64
import qrcode

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.sensor import SensorModel, EstadoSensorEnum
from app.infrastructure.db.models.lote_cafe import LoteCafeModel
from app.infrastructure.db.models.usuario import UsuarioModel
from app.infrastructure.db.models.audit_log import AuditLogModel
from app.core.security import get_current_admin_user
from app.api.v1.schemas.admin_sensor import (
    AdminSensorCreate, AdminSensorUpdate, AdminSensorResponse,
    AdminSensorListResponse, AdminSensorDetalle, QRResponse,
    AdminSensorAltaDirecta, AdminSensorAltaDirectaResponse,
)
from app.api.v1.schemas.admin_lote import AdminLoteActualResponse

router = APIRouter(prefix="/admin/sensores", tags=["Admin — Sensores"])

# id_usuario "placeholder" que usa trg_sensor_crea_lote_placeholder para el
# lote temporal "Sin vincular - <id>" que se crea al insertar cualquier
# sensor nuevo. Coincide con el usuario placeholder real de la BD (ver
# alta_esp32_kajve-D8463591.sql). Si en algún momento cambia, ajustar aquí.
ID_USUARIO_PLACEHOLDER = 10


async def _audit(db, id_usuario, accion, id_entidad, ip, detalles=None):
    log = AuditLogModel(
        id_usuario=id_usuario,
        accion=accion,
        entidad_afectada="sensores",
        id_entidad_afectada=id_entidad,
        ip_origen=ip,
        detalles=detalles,
        fecha_hora=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()


async def _lote_nombre(db: AsyncSession, id_sensor: int) -> Optional[str]:
    r = await db.execute(
        select(LoteCafeModel.nombre_lote).where(LoteCafeModel.id_sensor == id_sensor)
    )
    return r.scalar_one_or_none()


def _to_response(s: SensorModel, lote_nombre: Optional[str] = None) -> AdminSensorResponse:
    return AdminSensorResponse(
        id=s.id_sensor,
        mac_address=s.mac_address,
        tipo=s.tipo,
        modelo=s.modelo,
        estado=s.estado or "activo",
        id_cola_mqtt=s.id_cola_mqtt,
        provisioning_token=s.provisioning_token,
        token_usado=s.token_usado or False,
        lote_nombre=lote_nombre,
        created_at=s.fecha_registro or datetime.utcnow(),
    )


@router.post("", response_model=AdminSensorResponse, status_code=status.HTTP_201_CREATED)
async def crear_sensor(
    body: AdminSensorCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    existing = await db.execute(select(SensorModel).where(SensorModel.mac_address == body.mac_address))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un sensor con esa MAC address")

    sensor = SensorModel(
        mac_address=body.mac_address,
        tipo=body.tipo,
        modelo=body.modelo,
        estado="activo",
        id_cola_mqtt=f"sensors/{body.mac_address}/data",
        provisioning_token=str(uuid.uuid4()),
        token_usado=False,
        fecha_registro=datetime.utcnow(),
    )
    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _audit(
        db, int(current_user.get("sub")), "crear_sensor", sensor.id_sensor, ip,
        {"mac_address": body.mac_address, "tipo": body.tipo, "modelo": body.modelo},
    )
    return _to_response(sensor)


@router.post("/alta-directa", response_model=AdminSensorAltaDirectaResponse, status_code=status.HTTP_201_CREATED)
async def alta_directa_sensor(
    body: AdminSensorAltaDirecta,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Da de alta un ESP32 por su identificador y lo asigna de inmediato a
    un usuario real (sin pasar por "sin vincular" + reclamar por QR).

    Replica a mano, vía ORM, el mismo flujo de 2 pasos que ya hacen los
    triggers de BD (trg_sensor_crea_lote_placeholder / trg_lote_reemplaza_placeholder):
    1) insertar el sensor -> el trigger crea el lote placeholder bajo
       ID_USUARIO_PLACEHOLDER.
    2) insertar el lote real para `id_usuario` -> el trigger cancela el
       placeholder del paso 1.
    Al final, además, se verifica y cancela cualquier placeholder que haya
    quedado activo para este sensor por si los triggers no estuvieran
    presentes en el entorno actual (red de seguridad, no reemplaza los
    triggers).
    """
    identificador = body.identificador.strip()
    if not identificador:
        raise HTTPException(status_code=400, detail="El identificador del ESP32 no puede estar vacío")

    existing = await db.execute(select(SensorModel).where(SensorModel.mac_address == identificador))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Ya existe un sensor con el identificador '{identificador}'")

    usuario_r = await db.execute(select(UsuarioModel).where(UsuarioModel.id_usuario == body.id_usuario))
    usuario = usuario_r.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="El usuario indicado no existe")
    if body.id_usuario == ID_USUARIO_PLACEHOLDER:
        raise HTTPException(status_code=400, detail="No puedes asignar el sensor al usuario placeholder")

    try:
        sensor = SensorModel(
            mac_address=identificador,
            id_cola_mqtt=identificador,
            tipo=body.tipo,
            modelo=body.modelo,
            estado="activo",
            provisioning_token=str(uuid.uuid4()),
            token_usado=True,
            fecha_registro=datetime.utcnow(),
            mide_viento=body.mide_viento,
            mide_radiacion=body.mide_radiacion,
            mide_humedad_grano=body.mide_humedad_grano,
        )
        db.add(sensor)
        await db.flush()  # asigna id_sensor y dispara trg_sensor_crea_lote_placeholder

        lote = LoteCafeModel(
            id_usuario=body.id_usuario,
            id_sensor=sensor.id_sensor,
            nombre_lote=body.nombre_lote or f"Lote {identificador}",
            variedad=body.variedad,
            tipo_proceso=body.tipo_proceso,
            ubicacion=body.ubicacion,
            codigo_qr=str(uuid.uuid4()),
            estado="en_proceso",
            created_at=datetime.utcnow(),
        )
        db.add(lote)
        await db.flush()  # dispara trg_lote_reemplaza_placeholder

        # Red de seguridad: si por lo que sea el placeholder no se canceló
        # solo (p. ej. el trigger no existe en este entorno), lo cancelamos
        # a mano para no dejar un lote "activo" duplicado y huérfano.
        await db.execute(
            text(
                "UPDATE lotes_cafe SET estado = 'cancelado' "
                "WHERE id_sensor = :sid AND id_usuario = :placeholder "
                "AND id_lote != :real_lote_id AND estado != 'cancelado'"
            ),
            {"sid": sensor.id_sensor, "placeholder": ID_USUARIO_PLACEHOLDER, "real_lote_id": lote.id_lote},
        )

        await db.commit()
        await db.refresh(sensor)
        await db.refresh(lote)
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo dar de alta el sensor. Verifica el identificador y el usuario.",
        ) from exc

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    await _audit(
        db, int(current_user.get("sub")), "alta_directa_sensor", sensor.id_sensor, ip,
        {"identificador": identificador, "id_usuario": body.id_usuario, "id_lote": lote.id_lote},
    )

    return AdminSensorAltaDirectaResponse(
        sensor=_to_response(sensor, lote.nombre_lote),
        id_lote=lote.id_lote,
        codigo_qr=lote.codigo_qr,
        nombre_lote=lote.nombre_lote,
        estado_lote=lote.estado,
    )


@router.get("", response_model=AdminSensorListResponse)
async def listar_sensores(
    estado: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    if estado and estado not in EstadoSensorEnum.enums:
        raise HTTPException(
            status_code=400,
            detail=f"estado inválido: '{estado}'. Valores permitidos: {', '.join(EstadoSensorEnum.enums)}",
        )

    query = select(SensorModel)
    if estado:
        query = query.where(SensorModel.estado == estado)
    result = await db.execute(query)
    sensores = result.scalars().all()

    items = [_to_response(s, await _lote_nombre(db, s.id_sensor)) for s in sensores]
    return AdminSensorListResponse(total=len(items), items=items)


@router.get("/{id}", response_model=AdminSensorDetalle)
async def detalle_sensor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel).where(SensorModel.id_sensor == id))
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    lote_nombre = await _lote_nombre(db, id)

    # Historial de lotes con lecturas del sensor
    historial_r = await db.execute(
        text(
            "SELECT DISTINCT l.id_lote, l.nombre_lote, l.estado "
            "FROM lotes_cafe l "
            "JOIN lecturas_ambientales la ON la.id_sensor = :sid "
            "WHERE la.id_sensor = :sid "
            "ORDER BY l.id_lote DESC"
        ),
        {"sid": id},
    )
    historial = [
        {"id_lote": r.id_lote, "nombre": r.nombre_lote, "estado": r.estado}
        for r in historial_r.all()
    ]

    base = _to_response(sensor, lote_nombre)
    return AdminSensorDetalle(**base.model_dump(), historial_lotes=historial)


@router.put("/{id}", response_model=AdminSensorResponse)
async def actualizar_sensor(
    id: int,
    body: AdminSensorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel).where(SensorModel.id_sensor == id))
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    if body.estado is not None:
        sensor.estado = body.estado
    if body.modelo is not None:
        sensor.modelo = body.modelo
    await db.commit()
    await db.refresh(sensor)

    lote_nombre = await _lote_nombre(db, id)
    return _to_response(sensor, lote_nombre)


@router.get("/{id}/qr", response_model=QRResponse)
async def generar_qr_sensor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel).where(SensorModel.id_sensor == id))
    sensor = result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    if not sensor.mac_address or not sensor.provisioning_token:
        raise HTTPException(status_code=400, detail="Sensor sin MAC o token de provisioning")

    qr_data = json.dumps({"esp32_id": sensor.mac_address, "token": sensor.provisioning_token})
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    return QRResponse(qr_base64=f"data:image/png;base64,{b64}")


@router.get("/{id}/lote-actual", response_model=AdminLoteActualResponse)
async def lote_actual_sensor(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel).where(SensorModel.id_sensor == id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    lote_r = await db.execute(
        select(LoteCafeModel)
        .where(LoteCafeModel.id_sensor == id, LoteCafeModel.estado == "en_proceso")
        .order_by(LoteCafeModel.created_at.desc())
        .limit(1)
    )
    lote = lote_r.scalars().first()
    if lote is None:
        raise HTTPException(status_code=404, detail="No hay lote activo para este sensor")

    return AdminLoteActualResponse(
        id_lote=lote.id_lote,
        codigo_qr=lote.codigo_qr,
        nombre_lote=lote.nombre_lote,
        estado=lote.estado,
    )
