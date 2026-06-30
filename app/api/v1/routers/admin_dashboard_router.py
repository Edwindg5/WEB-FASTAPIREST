"""Router admin — dashboard y estadísticas globales. Requiere rol=administrador."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
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
        await db.execute(select(func.count()).where(LoteCafeModel.estado == "en_proceso"))
    ).scalar_one()
    lotes_finalizados = (
        await db.execute(select(func.count()).where(LoteCafeModel.estado == "completado"))
    ).scalar_one()

    hoy = datetime.now(timezone.utc).date()
    alertas_hoy_r = await db.execute(
        text("SELECT COUNT(*) FROM alertas WHERE DATE(fecha_generada) = :hoy"), {"hoy": hoy}
    )
    total_alertas_hoy = alertas_hoy_r.scalar_one() or 0

    alertas_criticas_r = await db.execute(
        text("SELECT COUNT(*) FROM alertas WHERE nivel_severidad='critico' AND atendida=false")
    )
    alertas_criticas = alertas_criticas_r.scalar_one() or 0

    inferencias_r = await db.execute(text("SELECT COUNT(*) FROM predicciones"))
    total_inferencias = inferencias_r.scalar_one() or 0

    hace_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    lecturas_r = await db.execute(
        text("SELECT COUNT(*) FROM lecturas_ambientales WHERE timestamp > :ts"), {"ts": hace_24h}
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

    avg_r = await db.execute(
        text(
            "SELECT AVG(EXTRACT(EPOCH FROM (COALESCE(fecha_fin_secado, NOW()) - fecha_inicio_secado))/3600) as avg_h "
            "FROM lotes_cafe WHERE created_at > :desde"
        ),
        {"desde": desde},
    )
    avg_horas = float(avg_r.scalar_one() or 0)
    promedio_dias = round(avg_horas / 24, 1)

    excelente_r = await db.execute(
        text("SELECT COUNT(*) FROM predicciones p JOIN lotes_cafe l ON l.id_lote = p.id_lote "
             "WHERE l.created_at > :desde AND p.calidad_estimada = 'excelente'"),
        {"desde": desde},
    )
    buena_r = await db.execute(
        text("SELECT COUNT(*) FROM predicciones p JOIN lotes_cafe l ON l.id_lote = p.id_lote "
             "WHERE l.created_at > :desde AND p.calidad_estimada = 'buena'"),
        {"desde": desde},
    )
    regular_r = await db.execute(
        text("SELECT COUNT(*) FROM predicciones p JOIN lotes_cafe l ON l.id_lote = p.id_lote "
             "WHERE l.created_at > :desde AND p.calidad_estimada = 'regular'"),
        {"desde": desde},
    )
    baja_r = await db.execute(
        text("SELECT COUNT(*) FROM predicciones p JOIN lotes_cafe l ON l.id_lote = p.id_lote "
             "WHERE l.created_at > :desde AND p.calidad_estimada = 'baja'"),
        {"desde": desde},
    )

    lecturas_r = await db.execute(
        text("SELECT AVG(temperatura) as ta, AVG(humedad) as ha "
             "FROM lecturas_ambientales WHERE timestamp > :desde"),
        {"desde": desde},
    )
    lr = lecturas_r.one()

    return {
        "promedio_dias_secado": promedio_dias,
        "calidad_promedio": "buena",
        "lotes_calidad_excelente": excelente_r.scalar_one() or 0,
        "lotes_calidad_buena": buena_r.scalar_one() or 0,
        "lotes_calidad_regular": regular_r.scalar_one() or 0,
        "lotes_calidad_baja": baja_r.scalar_one() or 0,
        "temperatura_promedio_global": round(float(lr.ta or 0), 1),
        "humedad_promedio_global": round(float(lr.ha or 0), 1),
    }


@router.get("/estadisticas/sensores", summary="Estado de sensores con última conexión")
async def estadisticas_sensores(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(SensorModel))
    sensores = result.scalars().all()

    items = []
    for s in sensores:
        lote_r = await db.execute(
            select(LoteCafeModel.nombre_lote).where(LoteCafeModel.id_sensor == s.id_sensor)
        )
        lote_nombre = lote_r.scalar_one_or_none()

        ultima_r = await db.execute(
            text("SELECT MAX(timestamp) FROM lecturas_ambientales WHERE id_sensor = :sid"),
            {"sid": s.id_sensor},
        )
        ultima_conexion = ultima_r.scalar_one_or_none()

        items.append({
            "id_sensor": s.id_sensor,
            "mac_address": s.mac_address,
            "modelo": s.modelo,
            "estado": s.estado,
            "ultima_conexion": ultima_conexion,
            "lote_asignado": lote_nombre,
        })
    return items
