"""Router admin — dashboard y estadísticas globales. Requiere rol=admin."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
from datetime import datetime, timedelta, timezone

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.usuario import UsuarioModel
from app.infrastructure.db.models.sensor import SensorModel
from app.infrastructure.db.models.lote_cafe import LoteCafeModel
from app.core.security import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin — Dashboard"])


@router.get("/dashboard", summary="Estadísticas globales del sistema")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    total_usuarios = (await db.execute(select(func.count()).select_from(UsuarioModel))).scalar_one()
    usuarios_activos = (
        await db.execute(select(func.count()).where(UsuarioModel.estado == "activo"))
    ).scalar_one()

    total_sensores = (await db.execute(select(func.count()).select_from(SensorModel))).scalar_one()
    sensores_activos = (
        await db.execute(select(func.count()).where(SensorModel.estado == "activo"))
    ).scalar_one()
    sensores_mantenimiento = (
        await db.execute(select(func.count()).where(SensorModel.estado == "mantenimiento"))
    ).scalar_one()

    total_lotes = (await db.execute(select(func.count()).select_from(LoteCafeModel))).scalar_one()
    lotes_en_proceso = (
        await db.execute(select(func.count()).where(LoteCafeModel.estado == "en_progreso"))
    ).scalar_one()
    lotes_finalizados = (
        await db.execute(select(func.count()).where(LoteCafeModel.estado == "completado"))
    ).scalar_one()

    # Alertas (tabla alertas — consulta con text si el modelo no está definido aún)
    from sqlalchemy import text
    hoy = datetime.now(timezone.utc).date()
    alertas_hoy_r = await db.execute(
        text("SELECT COUNT(*) FROM alertas WHERE DATE(created_at) = :hoy"), {"hoy": hoy}
    )
    total_alertas_hoy = alertas_hoy_r.scalar_one() or 0

    alertas_criticas_r = await db.execute(
        text("SELECT COUNT(*) FROM alertas WHERE severidad='critica' AND estado='activo'")
    )
    alertas_criticas = alertas_criticas_r.scalar_one() or 0

    inferencias_r = await db.execute(text("SELECT COUNT(*) FROM predicciones"))
    total_inferencias = inferencias_r.scalar_one() or 0

    hace_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    lecturas_r = await db.execute(
        text("SELECT COUNT(*) FROM lecturas_ambientales WHERE timestamp > :ts"),
        {"ts": hace_24h},
    )
    lecturas_24h = lecturas_r.scalar_one() or 0

    return {
        "total_usuarios": total_usuarios,
        "usuarios_activos": usuarios_activos,
        "total_sensores": total_sensores,
        "sensores_activos": sensores_activos,
        "sensores_mantenimiento": sensores_mantenimiento,
        "total_lotes": total_lotes,
        "lotes_en_proceso": lotes_en_proceso,
        "lotes_finalizados": lotes_finalizados,
        "total_alertas_hoy": total_alertas_hoy,
        "alertas_criticas_sin_atender": alertas_criticas,
        "total_inferencias_ml": total_inferencias,
        "lecturas_ultimas_24h": lecturas_24h,
    }


@router.get("/estadisticas/secado", summary="Estadísticas de secado por período")
async def estadisticas_secado(
    periodo: str = Query("7d", description="7d | 30d | 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    dias = {"7d": 7, "30d": 30, "90d": 90}.get(periodo, 7)
    desde = datetime.now(timezone.utc) - timedelta(days=dias)

    from sqlalchemy import text

    lotes_q = await db.execute(
        text(
            "SELECT COUNT(*) as total, "
            "AVG(EXTRACT(DAY FROM (COALESCE(fecha_fin_real, CURRENT_DATE) - fecha_inicio))) as avg_dias "
            "FROM lotes_cafe WHERE created_at > :desde"
        ),
        {"desde": desde},
    )
    row = lotes_q.one()
    promedio_dias = float(row.avg_dias or 0)

    # Calidad por estado (usamos nombre como proxy de calidad)
    excelente_r = await db.execute(
        text("SELECT COUNT(*) FROM lotes_cafe WHERE estado='completado' AND created_at > :desde AND temperatura_objetivo BETWEEN 25 AND 30"),
        {"desde": desde},
    )
    excelente = excelente_r.scalar_one() or 0

    buena_r = await db.execute(
        text("SELECT COUNT(*) FROM lotes_cafe WHERE estado='completado' AND created_at > :desde AND temperatura_objetivo IS NOT NULL"),
        {"desde": desde},
    )
    buena = max(0, (buena_r.scalar_one() or 0) - excelente)

    regular_r = await db.execute(
        text("SELECT COUNT(*) FROM lotes_cafe WHERE estado='en_progreso' AND created_at > :desde"),
        {"desde": desde},
    )
    regular = regular_r.scalar_one() or 0

    baja_r = await db.execute(
        text("SELECT COUNT(*) FROM lotes_cafe WHERE estado='cancelado' AND created_at > :desde"),
        {"desde": desde},
    )
    baja = baja_r.scalar_one() or 0

    lecturas_r = await db.execute(
        text(
            "SELECT AVG(temperatura) as avg_temp, AVG(humedad) as avg_hum "
            "FROM lecturas_ambientales WHERE timestamp > :desde"
        ),
        {"desde": desde},
    )
    lr = lecturas_r.one()
    temp_prom = round(float(lr.avg_temp or 0), 1)
    hum_prom = round(float(lr.avg_hum or 0), 1)

    return {
        "promedio_dias_secado": round(promedio_dias, 1),
        "calidad_promedio": "buena",
        "lotes_calidad_excelente": excelente,
        "lotes_calidad_buena": buena,
        "lotes_calidad_regular": regular,
        "lotes_calidad_baja": baja,
        "temperatura_promedio_global": temp_prom,
        "humedad_promedio_global": hum_prom,
    }


@router.get("/estadisticas/sensores", summary="Estado de sensores")
async def estadisticas_sensores(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel))
    sensores = result.scalars().all()

    from app.infrastructure.db.models.lote_cafe import LoteCafeModel

    items = []
    for s in sensores:
        lote_nombre = None
        if s.lote_id:
            lote_r = await db.execute(
                select(LoteCafeModel.nombre).where(LoteCafeModel.id == s.lote_id)
            )
            lote_nombre = lote_r.scalar_one_or_none()

        from sqlalchemy import text
        ultima_r = await db.execute(
            text(
                "SELECT MAX(timestamp) FROM lecturas_ambientales WHERE sensor_id = :sid"
            ),
            {"sid": s.id},
        )
        ultima_conexion = ultima_r.scalar_one_or_none()

        items.append({
            "id": s.id,
            "mac_address": s.mac_address,
            "modelo": s.modelo,
            "estado": s.estado,
            "ultima_conexion": ultima_conexion,
            "lote_asignado": lote_nombre,
        })

    return items
