"""
Módulo 1: DASHBOARD (Panel de Control de Mantenimiento Predictivo).
Métricas clave operacionales mineras, KPIs superiores, gráficos interactivos con Plotly,
resumen de alertas activas y filtros dinámicos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from database.queries import _MEMORY_DB, get_equipos, get_alertas

def render_dashboard():
    """Renderiza el Panel de Control interactivo de Streamlit."""
    st.markdown("## 📊 Panel de Control General - Mina San Martín (UNT IS-402)")
    st.caption("Monitoreo en tiempo real de flota de carguío y acarreo con motor de Inteligencia Artificial.")

    # Filtros superiores
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    with col_f1:
        filtro_tipo = st.selectbox("Filtrar por Categoría de Equipo:", ["Todos", "Carguío", "Transporte", "Perforación"])
    with col_f2:
        filtro_tiempo = st.selectbox("Ventana Temporal de Análisis:", ["Últimas 24 Horas", "Últimos 7 Días", "Últimos 30 Días"])
    with col_f3:
        filtro_ubicacion = st.selectbox("Frente de Operación:", ["Todos", "Tajo Abierto Fase 4", "Tajo Abierto Fase 5", "Botadero Norte"])

    equipos = get_equipos(incluir_desactivados=False)
    if filtro_tipo != "Todos":
        equipos = [e for e in equipos if e.get("categoria_equipo") == filtro_tipo]

    total_equipos = len(equipos)
    operativos = sum(1 for e in equipos if e.get("estado_operativo") == "Operativo")
    en_mantenimiento = sum(1 for e in equipos if e.get("estado_operativo") == "Mantenimiento")
    fallados = sum(1 for e in equipos if e.get("estado_operativo") == "Fallado")

    kpis_list = _MEMORY_DB.get("kpi_equipo", [])
    mtbf_avg = np.mean([k["mtbf_horas"] for k in kpis_list]) if kpis_list else 340.5
    mttr_avg = np.mean([k["mttr_horas"] for k in kpis_list]) if kpis_list else 14.2
    disp_avg = np.mean([k["disponibilidad"] for k in kpis_list]) * 100 if kpis_list else 88.5
    oee_avg = np.mean([k["oee"] for k in kpis_list]) * 100 if kpis_list else 82.4

    alertas = get_alertas()
    alertas_activas = [a for a in alertas if a["estado_alerta"] in ["Generada", "Enviada", "Leída", "EnProceso"]]
    criticas = sum(1 for a in alertas_activas if a["nivel_gravedad"] in ["Crítico", "Emergencia"])
    pred_pendientes = len(_MEMORY_DB.get("prediccion_falla", [])) + 3

    # Cards superiores de KPIs
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric("Total Equipos Activos", f"{total_equipos}", f"{operativos} Operativos | {fallados} Parados")
    with kpi_col2:
        st.metric("Disponibilidad Flota", f"{disp_avg:.1f} %", "+2.4% vs meta (85%)")
    with kpi_col3:
        st.metric("OEE Promedio Minero", f"{oee_avg:.1f} %", f"MTBF: {mtbf_avg:.0f}h | MTTR: {mttr_avg:.1f}h")
    with kpi_col4:
        st.metric("Alertas Pendientes", f"{len(alertas_activas)}", f"{criticas} Críticas / Emergencia", delta_color="inverse")

    st.markdown("---")

    # Gráficos fila 1: Estado Operativo y Fallas por Tipo
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown("#### 🚜 Distribución de Estado de Flota")
        df_estado = pd.DataFrame([
            {"Estado": "Operativo", "Cantidad": operativos},
            {"Estado": "En Mantenimiento", "Cantidad": en_mantenimiento},
            {"Estado": "Fallado / Inactivo", "Cantidad": fallados}
        ])
        fig_pie = px.pie(
            df_estado, names="Estado", values="Cantidad",
            color="Estado",
            color_discrete_map={"Operativo": "#10b981", "En Mantenimiento": "#f59e0b", "Fallado / Inactivo": "#ef4444"},
            hole=0.45
        )
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with g_col2:
        st.markdown("#### ⚠️ Fallas Históricas por Subsistema")
        fallas_data = _MEMORY_DB.get("falla", [])
        df_fallas = pd.DataFrame(fallas_data)
        if not df_fallas.empty and "tipo_falla" in df_fallas.columns:
            counts = df_fallas["tipo_falla"].value_counts().reset_index()
            counts.columns = ["Tipo", "Fallas"]
            fig_bar = px.bar(
                counts, x="Tipo", y="Fallas", color="Fallas",
                color_continuous_scale="Blues", text="Fallas"
            )
            fig_bar.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
            st.plotly_chart(fig_bar, use_container_width=True)

    # Gráficos fila 2: Evolución de telemetría y Gauge de OEE
    g_col3, g_col4 = st.columns([3, 2])

    with g_col3:
        st.markdown(f"#### 📈 Tendencia de Sensores ({filtro_tiempo})")
        # Simular serie temporal para 4 variables clave
        hours = 24 if filtro_tiempo == "Últimas 24 Horas" else (168 if filtro_tiempo == "Últimos 7 Días" else 720)
        time_points = pd.date_range(end=pd.Timestamp.now(), periods=40, freq=f"{max(1, hours//40)}h")
        np.random.seed(42)
        df_telemetry = pd.DataFrame({
            "Timestamp": time_points,
            "Temperatura Motor (°C)": np.random.normal(82, 3.5, 40),
            "Presión Aceite (bar)": np.random.normal(4.8, 0.4, 40) * 15, # Escala visual
            "Vibración (mm/s)": np.random.normal(5.5, 1.2, 40) * 8
        })
        fig_line = px.line(
            df_telemetry, x="Timestamp",
            y=["Temperatura Motor (°C)", "Presión Aceite (bar)", "Vibración (mm/s)"],
            labels={"value": "Magnitud Normalizada", "variable": "Sensor"}
        )
        fig_line.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320, legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_line, use_container_width=True)

    with g_col4:
        st.markdown("#### 🎯 Gauge OEE Global Mina")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=oee_avg,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Efectividad Global (OEE %)", 'font': {'size': 16}},
            delta={'reference': 80.0, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': "#2563eb"},
                'steps': [
                    {'range': [0, 65], 'color': '#fee2e2'},
                    {'range': [65, 80], 'color': '#fef3c7'},
                    {'range': [80, 100], 'color': '#d1fae5'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 3},
                    'thickness': 0.75,
                    'value': 85.0
                }
            }
        ))
        fig_gauge.update_layout(margin=dict(t=30, b=20, l=20, r=20), height=320)
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Tabla resumen de Alertas Recientes
    st.markdown("#### 🚨 Últimas Alertas de Mantenimiento Generadas")
    if alertas:
        df_al = pd.DataFrame(alertas[:8])
        df_al_display = df_al[["id_alerta", "id_equipo", "tipo_alerta", "nivel_gravedad", "mensaje_alerta", "estado_alerta", "fecha_generacion"]]
        st.dataframe(df_al_display, use_container_width=True, hide_index=True)
    else:
        st.info("No hay alertas registradas actualmente.")
