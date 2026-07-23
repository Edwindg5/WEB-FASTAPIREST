"""Router admin — dashboard y estadísticas globales. Requiere rol=administrador."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.usuario import UsuarioModel
from app.infrastructure.db.models.sensor import SensorModel
from app.infrastructure.db.models.lote_cafe import LoteCafeModel
from app.core.security import get_current_admin_user
from app.core.logging import logger

router = APIRouter(prefix="/admin", tags=["Admin — Dashboard"])


async def _safe_scalar(db: AsyncSession, sql, params: Optional[Dict[str, Any]] = None, default=0, label: str = ""):
    """Ejecuta un `select(...)` de SQLAlchemy o un `text(...)` con params y
    devuelve su scalar, o `default` si algo falla (tabla/columna que no
    existe todavía en este entorno, tipo de dato inesperado, etc.). Loguea
    el error completo para poder diagnosticarlo en los logs del servidor,
    pero nunca deja que tumbe el endpoint entero con un 500 — antes, un
    solo query roto en /estadisticas/secado hacía caer TODA la respuesta,
    y como el frontend pedía todo con Promise.all, un solo endpoint
    fallando dejaba el dashboard entero sin datos aunque el resto sí
    hubiera respondido bien."""
    try:
        result = await db.execute(sql, params or {})
        return result.scalar_one_or_none()
    except Exception:
        logger.exception(f"Error ejecutando query de estadísticas ({label}), devolviendo valor por defecto")
        await db.rollback()
        return default


@router.get("/dashboard", summary="Estadísticas globales del sistema")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    total_usuarios = await _safe_scalar(db, select(func.count()).select_from(UsuarioModel), label="total_usuarios")
    usuarios_activos = await _safe_scalar(
        db, select(func.count()).where(UsuarioModel.estado == "activo"), label="usuarios_activos"
    )
    total_productores = await _safe_scalar(
        db, select(func.count()).where(UsuarioModel.rol == "productor"), label="total_productores"
    )
    total_usuarios_premium = await _safe_scalar(
        db, select(func.count()).where(UsuarioModel.es_premium.is_(True)), label="total_usuarios_premium"
    )

    total_sensores = await _safe_scalar(db, select(func.count()).select_from(SensorModel), label="total_sensores")
    sensores_activos = await _safe_scalar(
        db, select(func.count()).where(SensorModel.estado == "activo"), label="sensores_activos"
    )
    sensores_mantenimiento = await _safe_scalar(
        db, select(func.count()).where(SensorModel.estado == "mantenimiento"), label="sensores_mantenimiento"
    )

    total_lotes = await _safe_scalar(db, select(func.count()).select_from(LoteCafeModel), label="total_lotes")
    lotes_en_proceso = await _safe_scalar(
        db, select(func.count()).where(LoteCafeModel.estado == "en_proceso"), label="lotes_en_proceso"
    )
    lotes_finalizados = await _safe_scalar(
        db, select(func.count()).where(LoteCafeModel.estado == "finalizado"), label="lotes_finalizados"
    )

    hoy = datetime.utcnow().date()
    total_alertas_hoy = await _safe_scalar(
        db, text("SELECT COUNT(*) FROM alertas WHERE DATE(fecha_generada) = :hoy"), {"hoy": hoy},
        label="total_alertas_hoy",
    )

    alertas_criticas = await _safe_scalar(
        db, text("SELECT COUNT(*) FROM alertas WHERE nivel_severidad='critica' AND atendida=false"),
        label="alertas_criticas",
    )

    total_inferencias = await _safe_scalar(db, text("SELECT COUNT(*) FROM predicciones"), label="total_inferencias")

    hace_24h = datetime.utcnow() - timedelta(hours=24)
    lecturas_24h = await _safe_scalar(
        db, text("SELECT COUNT(*) FROM lecturas_ambientales WHERE timestamp > :ts"), {"ts": hace_24h},
        label="lecturas_24h",
    )

    return {
        "total_usuarios": total_usuarios,
        "usuarios_activos": usuarios_activos,
        "total_productores": total_productores,
        "total_usuarios_premium": total_usuarios_premium,
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


@router.get("/estadisticas/usuarios", summary="Usuarios registrados a lo largo del tiempo + premium vs normal")
async def estadisticas_usuarios(
    dias: int = Query(30, ge=7, le=365, description="Tamaño de la ventana de la serie de tiempo"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Alimenta dos gráficas del panel admin:

    - dashboard: usuarios creados por día (serie de tiempo, últimos `dias`).
    - estadisticas: pastel de usuarios premium vs normales.
    """
    desde = datetime.utcnow() - timedelta(days=dias)

    por_dia: Dict[str, int] = {}
    try:
        serie_r = await db.execute(
            text(
                "SELECT DATE(fecha_registro) AS dia, COUNT(*) AS cantidad "
                "FROM usuarios "
                "WHERE fecha_registro >= :desde "
                "GROUP BY DATE(fecha_registro) "
                "ORDER BY dia"
            ),
            {"desde": desde},
        )
        por_dia = {row.dia.isoformat(): row.cantidad for row in serie_r.all()}
    except Exception:
        logger.exception("Error obteniendo serie de tiempo de usuarios, se devuelve vacía")
        await db.rollback()

    # Rellenamos los días sin registros con 0 para que la gráfica no tenga huecos.
    serie = []
    for i in range(dias, -1, -1):
        fecha = (datetime.utcnow() - timedelta(days=i)).date()
        clave = fecha.isoformat()
        serie.append({"fecha": clave, "cantidad": por_dia.get(clave, 0)})

    total_premium = await _safe_scalar(
        db, select(func.count()).where(UsuarioModel.es_premium.is_(True)), label="total_premium"
    )
    total_normales = await _safe_scalar(
        db, select(func.count()).where(UsuarioModel.es_premium.is_(False)), label="total_normales"
    )
    total_productores = await _safe_scalar(
        db, select(func.count()).where(UsuarioModel.rol == "productor"), label="total_productores"
    )
    total_administradores = await _safe_scalar(
        db, select(func.count()).where(UsuarioModel.rol == "administrador"), label="total_administradores"
    )

    return {
        "serie_tiempo": serie,
        "premium_vs_normal": {"premium": total_premium, "normal": total_normales},
        "roles": {"productor": total_productores, "administrador": total_administradores},
    }


@router.get("/estadisticas/secado", summary="Estadísticas de secado por período")
async def estadisticas_secado(
    periodo: str = Query("7d", description="7d | 30d | 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    dias = {"7d": 7, "30d": 30, "90d": 90}.get(periodo, 7)
    desde = datetime.utcnow() - timedelta(days=dias)

    avg_horas = await _safe_scalar(
        db,
        text(
            "SELECT AVG(EXTRACT(EPOCH FROM (COALESCE(fecha_fin_secado, NOW()) - fecha_inicio_secado))/3600) as avg_h "
            "FROM lotes_cafe WHERE created_at > :desde"
        ),
        {"desde": desde},
        default=0,
        label="avg_horas_secado",
    )
    promedio_dias = round(float(avg_horas or 0) / 24, 1)

    lotes_calidad_excelente = await _safe_scalar(
        db,
        text("SELECT COUNT(*) FROM predicciones p JOIN lotes_cafe l ON l.id_lote = p.id_lote "
             "WHERE l.created_at > :desde AND p.calidad_estimada = 'excelente'"),
        {"desde": desde},
        label="lotes_calidad_excelente",
    )
    lotes_calidad_buena = await _safe_scalar(
        db,
        text("SELECT COUNT(*) FROM predicciones p JOIN lotes_cafe l ON l.id_lote = p.id_lote "
             "WHERE l.created_at > :desde AND p.calidad_estimada = 'buena'"),
        {"desde": desde},
        label="lotes_calidad_buena",
    )
    lotes_calidad_regular = await _safe_scalar(
        db,
        text("SELECT COUNT(*) FROM predicciones p JOIN lotes_cafe l ON l.id_lote = p.id_lote "
             "WHERE l.created_at > :desde AND p.calidad_estimada = 'regular'"),
        {"desde": desde},
        label="lotes_calidad_regular",
    )
    lotes_calidad_baja = await _safe_scalar(
        db,
        text("SELECT COUNT(*) FROM predicciones p JOIN lotes_cafe l ON l.id_lote = p.id_lote "
             "WHERE l.created_at > :desde AND p.calidad_estimada = 'baja'"),
        {"desde": desde},
        label="lotes_calidad_baja",
    )

    temperatura_promedio = 0.0
    humedad_promedio = 0.0
    try:
        lecturas_r = await db.execute(
            text("SELECT AVG(temperatura) as ta, AVG(humedad) as ha "
                 "FROM lecturas_ambientales WHERE timestamp > :desde"),
            {"desde": desde},
        )
        lr = lecturas_r.first()
        if lr is not None:
            temperatura_promedio = float(lr.ta or 0)
            humedad_promedio = float(lr.ha or 0)
    except Exception:
        logger.exception("Error obteniendo promedios de lecturas ambientales para /estadisticas/secado")
        await db.rollback()

    return {
        "promedio_dias_secado": promedio_dias,
        "calidad_promedio": "buena",
        "lotes_calidad_excelente": lotes_calidad_excelente,
        "lotes_calidad_buena": lotes_calidad_buena,
        "lotes_calidad_regular": lotes_calidad_regular,
        "lotes_calidad_baja": lotes_calidad_baja,
        "temperatura_promedio_global": round(temperatura_promedio, 1),
        "humedad_promedio_global": round(humedad_promedio, 1),
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
        lote_nombre = None
        ultima_conexion = None
        try:
            lote_r = await db.execute(
                select(LoteCafeModel.nombre_lote)
                .where(LoteCafeModel.id_sensor == s.id_sensor)
                .order_by(LoteCafeModel.created_at.desc())
                .limit(1)
            )
            lote_nombre = lote_r.scalar()

            ultima_r = await db.execute(
                text("SELECT MAX(timestamp) FROM lecturas_ambientales WHERE id_sensor = :sid"),
                {"sid": s.id_sensor},
            )
            ultima_conexion = ultima_r.scalar_one_or_none()
        except Exception:
            logger.exception(f"Error obteniendo datos del sensor {s.id_sensor} en /estadisticas/sensores")
            await db.rollback()

        items.append({
            "id_sensor": s.id_sensor,
            "mac_address": s.mac_address,
            "modelo": s.modelo,
            "estado": s.estado,
            "ultima_conexion": ultima_conexion,
            "lote_asignado": lote_nombre,
        })
    return items
