"""Router admin — reportes PDF/Excel. Requiere rol=admin."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import io

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models.reporte import ReporteModel
from app.infrastructure.db.models.lote_cafe import LoteCafeModel
from app.infrastructure.db.models.usuario import UsuarioModel
from app.core.security import get_current_admin_user

router = APIRouter(prefix="/admin/reportes", tags=["Admin — Reportes"])

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def _generar_pdf(lote_data: dict, estadisticas: dict, alertas: list) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Reporte de Lote: {lote_data.get('nombre', 'N/A')}", styles["Title"]))
    story.append(Spacer(1, 0.25 * inch))

    info = [
        ["ID Lote", str(lote_data.get("id", ""))],
        ["Estado", lote_data.get("estado", "")],
        ["Fecha Inicio", str(lote_data.get("fecha_inicio", ""))],
        ["Temp. Objetivo", str(lote_data.get("temperatura_objetivo", ""))],
        ["Humedad Objetivo", str(lote_data.get("humedad_objetivo", ""))],
    ]
    tabla_info = Table(info, colWidths=[2.5 * inch, 4 * inch])
    tabla_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ]))
    story.append(tabla_info)
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Estadísticas Ambientales", styles["Heading2"]))
    est_data = [
        ["Métrica", "Valor"],
        ["Temp. Promedio", f"{estadisticas.get('temp_avg', 0):.1f} °C"],
        ["Humedad Promedio", f"{estadisticas.get('hum_avg', 0):.1f} %"],
        ["Total Lecturas", str(estadisticas.get("total_lecturas", 0))],
    ]
    tabla_est = Table(est_data, colWidths=[3 * inch, 3 * inch])
    tabla_est.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(tabla_est)
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Alertas del Lote", styles["Heading2"]))
    if alertas:
        alerta_data = [["Tipo", "Severidad", "Mensaje", "Estado"]]
        for a in alertas[:20]:
            alerta_data.append([
                str(a.get("tipo", "")),
                str(a.get("severidad", "")),
                str(a.get("mensaje", ""))[:40],
                str(a.get("estado", "")),
            ])
        tabla_al = Table(alerta_data, colWidths=[1.5 * inch, 1.2 * inch, 3 * inch, 1 * inch])
        tabla_al.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.red),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(tabla_al)
    else:
        story.append(Paragraph("Sin alertas registradas.", styles["Normal"]))

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Recomendaciones: Mantener temperatura y humedad dentro de rangos óptimos.", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _generar_excel(lote_data: dict, estadisticas: dict, alertas: list) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Lote"

    ws["A1"] = f"Reporte de Lote: {lote_data.get('nombre', 'N/A')}"
    ws["A1"].font = Font(bold=True, size=14)

    ws["A3"] = "Información del Lote"
    ws["A3"].font = Font(bold=True)
    datos = [
        ("ID Lote", lote_data.get("id", "")),
        ("Nombre", lote_data.get("nombre", "")),
        ("Estado", lote_data.get("estado", "")),
        ("Fecha Inicio", str(lote_data.get("fecha_inicio", ""))),
        ("Temp. Objetivo", lote_data.get("temperatura_objetivo", "")),
        ("Humedad Objetivo", lote_data.get("humedad_objetivo", "")),
    ]
    for i, (k, v) in enumerate(datos, start=4):
        ws[f"A{i}"] = k
        ws[f"B{i}"] = v

    row = len(datos) + 6
    ws[f"A{row}"] = "Estadísticas Ambientales"
    ws[f"A{row}"].font = Font(bold=True)
    row += 1
    ws[f"A{row}"] = "Temp. Promedio"
    ws[f"B{row}"] = estadisticas.get("temp_avg", 0)
    row += 1
    ws[f"A{row}"] = "Humedad Promedio"
    ws[f"B{row}"] = estadisticas.get("hum_avg", 0)
    row += 1
    ws[f"A{row}"] = "Total Lecturas"
    ws[f"B{row}"] = estadisticas.get("total_lecturas", 0)

    row += 2
    ws[f"A{row}"] = "Alertas"
    ws[f"A{row}"].font = Font(bold=True)
    row += 1
    for col, header in enumerate(["Tipo", "Severidad", "Mensaje", "Estado"], 1):
        ws.cell(row=row, column=col, value=header).font = Font(bold=True)
    row += 1
    for a in alertas[:50]:
        ws.cell(row=row, column=1, value=a.get("tipo", ""))
        ws.cell(row=row, column=2, value=a.get("severidad", ""))
        ws.cell(row=row, column=3, value=str(a.get("mensaje", ""))[:100])
        ws.cell(row=row, column=4, value=a.get("estado", ""))
        row += 1

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()


@router.get("", summary="Listar todos los reportes generados")
async def listar_reportes(
    formato: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    query = select(ReporteModel)
    if formato:
        query = query.where(ReporteModel.formato == formato)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    offset = (page - 1) * limit
    result = await db.execute(query.order_by(ReporteModel.created_at.desc()).offset(offset).limit(limit))
    reportes = result.scalars().all()

    items = []
    for r in reportes:
        lote_r = await db.execute(
            select(LoteCafeModel.nombre).where(LoteCafeModel.id == r.lote_id)
        )
        lote_nombre = lote_r.scalar_one_or_none()

        usr_r = await db.execute(
            select(UsuarioModel.nombre_completo).where(UsuarioModel.id == r.generado_por)
        )
        usuario_nombre = usr_r.scalar_one_or_none()

        items.append({
            "id": r.id,
            "lote_id": r.lote_id,
            "lote_nombre": lote_nombre,
            "tipo": r.tipo,
            "formato": r.formato,
            "archivo_url": r.archivo_url,
            "generado_por_nombre": usuario_nombre,
            "created_at": r.created_at,
        })

    return {"total": total, "page": page, "limit": limit, "items": items}


@router.post("/generar", status_code=status.HTTP_201_CREATED, summary="Generar reporte PDF o Excel")
async def generar_reporte(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    id_lote = body.get("id_lote")
    tipo_reporte = body.get("tipo_reporte", "secado_completo")
    formato = body.get("formato", "pdf").lower()

    if formato not in ("pdf", "excel"):
        raise HTTPException(status_code=400, detail="Formato debe ser 'pdf' o 'excel'")

    lote_r = await db.execute(select(LoteCafeModel).where(LoteCafeModel.id == id_lote))
    lote = lote_r.scalar_one_or_none()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    lote_data = {
        "id": lote.id,
        "nombre": lote.nombre,
        "estado": lote.estado,
        "fecha_inicio": lote.fecha_inicio,
        "temperatura_objetivo": float(lote.temperatura_objetivo) if lote.temperatura_objetivo else None,
        "humedad_objetivo": float(lote.humedad_objetivo) if lote.humedad_objetivo else None,
    }

    est_r = await db.execute(
        text(
            "SELECT AVG(temperatura) as ta, AVG(humedad) as ha, COUNT(*) as cnt "
            "FROM lecturas_ambientales WHERE lote_id = :lid"
        ),
        {"lid": id_lote},
    )
    est_row = est_r.one()
    estadisticas = {
        "temp_avg": float(est_row.ta or 0),
        "hum_avg": float(est_row.ha or 0),
        "total_lecturas": int(est_row.cnt or 0),
    }

    alertas_r = await db.execute(
        text("SELECT tipo, severidad, mensaje, estado FROM alertas WHERE lote_id = :lid LIMIT 50"),
        {"lid": id_lote},
    )
    alertas = [{"tipo": r.tipo, "severidad": r.severidad, "mensaje": r.mensaje, "estado": r.estado}
               for r in alertas_r.all()]

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    ext = "pdf" if formato == "pdf" else "xlsx"
    filename = f"reporte_lote_{id_lote}_{tipo_reporte}_{ts}.{ext}"
    filepath = os.path.join(REPORTS_DIR, filename)

    if formato == "pdf":
        content = _generar_pdf(lote_data, estadisticas, alertas)
        with open(filepath, "wb") as f:
            f.write(content)
    else:
        content = _generar_excel(lote_data, estadisticas, alertas)
        with open(filepath, "wb") as f:
            f.write(content)

    reporte = ReporteModel(
        lote_id=id_lote,
        tipo=tipo_reporte,
        formato=formato,
        archivo_url=filepath,
        generado_por=int(current_user.get("sub")),
    )
    db.add(reporte)
    await db.commit()
    await db.refresh(reporte)

    return {
        "id": reporte.id,
        "lote_id": reporte.lote_id,
        "tipo": reporte.tipo,
        "formato": reporte.formato,
        "archivo_url": reporte.archivo_url,
        "created_at": reporte.created_at,
    }


@router.get("/{id}/descargar", summary="Descargar archivo de reporte")
async def descargar_reporte(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_admin_user),
):
    result = await db.execute(select(ReporteModel).where(ReporteModel.id == id))
    reporte = result.scalar_one_or_none()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    if not reporte.archivo_url or not os.path.exists(reporte.archivo_url):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")

    media_type = "application/pdf" if reporte.formato == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(
        path=reporte.archivo_url,
        media_type=media_type,
        filename=os.path.basename(reporte.archivo_url),
    )
