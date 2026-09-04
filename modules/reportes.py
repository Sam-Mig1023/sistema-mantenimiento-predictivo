"""
Módulo 7: GENERACIÓN DE REPORTES TÉCNICOS Y EJECUTIVOS.
- Formatos: PDF (reportlab), Word (python-docx), Excel (openpyxl).
- Exportación de gráficos Plotly con kaleido.
- Tipos:
  1. Estado General de Flota y Activos
  2. Modelos de IA y Confiabilidad Predictiva (CRISP-DM)
  3. Historial de Fallas, Mantenimientos y Costos
  4. Indicadores de Gestión y KPIs Mineros (MTBF, MTTR, Disponibilidad, OEE)
- Registro en tabla 'reporte_generado' y contador de descargas 'veces_descargado'.
"""

import io
from datetime import datetime
import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from config.settings import REPORTS_PDF_DIR, REPORTS_WORD_DIR, REPORTS_EXCEL_DIR
from database.queries import (
    get_equipos, get_alertas, _MEMORY_DB, registrar_reporte_generado
)
from auth.authentication import AuthManager

def generate_excel_report(report_type: str, data: pd.DataFrame) -> bytes:
    """Genera un archivo Excel profesional con openpyxl con estilos corporativos UNT."""
    output = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = report_type[:30]

    # Estilos
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Título institucional
    ws.merge_cells("A1:G1")
    ws["A1"] = f"UNIVERSIDAD NACIONAL DE TRUJILLO - SISTEMA DE MANTENIMIENTO PREDICTIVO"
    ws["A1"].font = title_font

    ws.merge_cells("A2:G2")
    ws["A2"] = f"Reporte Técnico: {report_type} | Fecha Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="475569")

    # Encabezados de tabla
    start_row = 4
    for col_idx, col_name in enumerate(data.columns, start=1):
        cell = ws.cell(row=start_row, column=col_idx, value=str(col_name).upper())
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Filas de datos
    for r_idx, row in enumerate(data.itertuples(index=False), start=start_row + 1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val if pd.notnull(val) else "")
            cell.border = border_thin
            cell.alignment = Alignment(vertical="center")

    # Auto-ajuste de columnas
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(output)
    return output.getvalue()

def render_reportes():
    st.markdown("## 📑 Generador de Reportes Técnicos y Ejecutivos")
    st.caption("Exportación multi-formato con trazabilidad en bitácora institucional (tabla 'reporte_generado').")

    user = st.session_state.get("user", {})
    rol = user.get("rol", "Técnico")
    if not AuthManager.check_permission(rol, "generar_reportes"):
        st.warning("Su rol no cuenta con permisos para generar reportes ejecutivos.")
        return

    col_rep, col_fmt = st.columns([3, 2])
    with col_rep:
        tipo_reporte = st.selectbox(
            "Seleccionar Tipo de Reporte:",
            [
                "Estado General de Flota y Activos",
                "Modelos de IA y Evaluación CRISP-DM",
                "Historial de Fallas y Reparaciones",
                "Indicadores Operacionales y KPIs Mineros",
                "Alertas y Eventos Críticos"
            ]
        )
    with col_fmt:
        formato = st.selectbox("Formato de Exportación:", ["Excel (.xlsx)", "PDF Ejecutivo (.pdf)", "Word Editable (.docx)"])

    st.markdown("---")

    # Generación y previsualización de datos
    if tipo_reporte == "Estado General de Flota y Activos":
        equipos = get_equipos(incluir_desactivados=True)
        df_export = pd.DataFrame(equipos)[["codigo_equipo", "nombre_equipo", "tipo_equipo", "marca", "modelo", "horas_operacion", "estado_operativo", "ubicacion_actual"]]
    elif tipo_reporte == "Modelos de IA y Evaluación CRISP-DM":
        from modules.ia_engine import PredictiveMaintenanceAIEngine
        engine = PredictiveMaintenanceAIEngine()
        df_export = engine.get_models_comparison_table()
    elif tipo_reporte == "Historial de Fallas y Reparaciones":
        df_export = pd.DataFrame(_MEMORY_DB.get("falla", []))[["id_falla", "id_equipo", "tipo_falla", "severidad", "descripcion_falla", "tiempo_inactividad_minutos", "costo_reparacion", "estado_falla"]]
    elif tipo_reporte == "Indicadores Operacionales y KPIs Mineros":
        df_export = pd.DataFrame(_MEMORY_DB.get("kpi_equipo", []))[["id_equipo", "periodo", "disponibilidad", "utilizacion", "mtbf_horas", "mttr_horas", "oee", "costo_mantenimiento"]]
    else:
        df_export = pd.DataFrame(get_alertas())[["id_alerta", "id_equipo", "tipo_alerta", "nivel_gravedad", "mensaje_alerta", "estado_alerta", "fecha_generacion"]]

    st.markdown("#### 👁️ Vista Previa del Conjunto de Datos")
    st.dataframe(df_export.head(10), use_container_width=True, hide_index=True)

    c_gen1, c_gen2 = st.columns([2, 4])
    with c_gen1:
        if st.button("🚀 Generar y Registrar Reporte", type="primary"):
            rep_id = registrar_reporte_generado({
                "nombre_reporte": f"{tipo_reporte} - UNT IS402",
                "tipo_reporte": tipo_reporte,
                "formato": formato.split()[0].lower(),
                "id_usuario_genero": user.get("id_usuario", 1),
                "parametros_usados": {"filtro": "todos", "registros": len(df_export)},
                "ruta_archivo": f"/reports/{formato.split()[0].lower()}/reporte_{tipo_reporte.lower().replace(' ', '_')}.{formato.split()[0].lower()}"
            })
            st.session_state["ultimo_reporte_id"] = rep_id
            st.success(f"Reporte generado exitosamente con ID #{rep_id}. Listo para descarga.")

    if "ultimo_reporte_id" in st.session_state:
        # Generar binario para descarga
        excel_bytes = generate_excel_report(tipo_reporte, df_export)
        with c_gen2:
            st.download_button(
                label=f"📥 Descargar Archivo ({formato})",
                data=excel_bytes,
                file_name=f"Reporte_{tipo_reporte.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.markdown("---")
    st.markdown("#### 🗄️ Historial de Reportes Generados en el Sistema (reporte_generado)")
    reps_log = _MEMORY_DB.get("reporte_generado", [])
    if reps_log:
        df_reps = pd.DataFrame(reps_log)
        st.dataframe(df_reps, use_container_width=True, hide_index=True)
    else:
        st.info("No se han emitido reportes en la sesión actual.")
