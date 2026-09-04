"""
Módulo 3: MONITOREO DE SENSORES Y TELEMETRÍA.
- Visualización en tiempo real de telemetría minera.
- Gráficos interactivos de series temporales con Plotly (zoom, pan, cursor dinámico).
- Detección de anomalías contra 'parametro_referencia_sensor'.
- Indicador de calidad de dato (Válido, Dudoso, Inválido).
- Paginación y exportación de lecturas a CSV.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from database.queries import get_equipos, get_sensores, get_lecturas_sensor, _MEMORY_DB

def render_sensores():
    st.markdown("## 📡 Monitoreo de Sensores e Instrumentación")
    st.caption("Adquisición de telemetría continua, control de umbrales nominales y validación de calidad de señal.")

    equipos = get_equipos()
    if not equipos:
        st.warning("No hay equipos disponibles.")
        return

    col_eq, col_sen, col_cal = st.columns([3, 3, 2])
    with col_eq:
        sel_eq_id = st.selectbox(
            "Seleccionar Equipo:",
            options=[e["id_equipo"] for e in equipos],
            format_func=lambda x: next((f"{e['codigo_equipo']} - {e['nombre_equipo']}" for e in equipos if e["id_equipo"] == x), str(x))
        )

    sensores_eq = get_sensores(id_equipo=sel_eq_id)
    if not sensores_eq:
        st.info("Este equipo no tiene sensores configurados.")
        return

    with col_sen:
        sel_sens_id = st.selectbox(
            "Seleccionar Sensor:",
            options=[s["id_sensor"] for s in sensores_eq],
            format_func=lambda x: next((f"{s['nombre_sensor']} ({s['tipo_sensor']})" for s in sensores_eq if s["id_sensor"] == x), str(x))
        )

    sensor_obj = next((s for s in sensores_eq if s["id_sensor"] == sel_sens_id), sensores_eq[0])

    # Buscar parámetros de referencia
    params_ref = [p for p in _MEMORY_DB.get("parametro_referencia_sensor", []) if p["id_sensor"] == sel_sens_id]
    param = params_ref[0] if params_ref else {
        "valor_esperado_min": sensor_obj["rango_minimo"],
        "valor_esperado_max": sensor_obj["rango_maximo"],
        "umbral_critico_min": sensor_obj["rango_minimo"] * 0.9,
        "umbral_critico_max": sensor_obj["rango_maximo"] * 1.1
    }

    # Tarjetas de parámetros
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Rango Nominal Esperado", f"{param['valor_esperado_min']} - {param['valor_esperado_max']} {sensor_obj['unidad_medida']}")
    with m2:
        st.metric("Umbral Crítico Máximo", f"{param['umbral_critico_max']} {sensor_obj['unidad_medida']}", delta_color="inverse")
    with m3:
        st.metric("Frecuencia Muestreo", f"{sensor_obj.get('frecuencia_muestreo', 30)} seg")
    with m4:
        st.metric("Ubicación Sensor", f"{sensor_obj.get('ubicacion_instalacion', 'Motor')}")

    st.markdown("---")

    # Serie temporal con Plotly
    st.markdown("#### 📈 Serie Temporal con Bandas de Control y Anomalías")
    lecturas = get_lecturas_sensor(id_sensor=sel_sens_id, limit=300)

    if lecturas:
        df_lect = pd.DataFrame(lecturas)
        df_lect["timestamp_lectura"] = pd.to_datetime(df_lect["timestamp_lectura"])
        df_lect = df_lect.sort_values("timestamp_lectura")

        fig = go.Figure()

        # Línea de valor medido
        fig.add_trace(go.Scatter(
            x=df_lect["timestamp_lectura"],
            y=df_lect["valor_medido"],
            mode="lines+markers",
            name=f"{sensor_obj['nombre_sensor']}",
            line=dict(color="#2563eb", width=2),
            marker=dict(size=4)
        ))

        # Bandas de referencia
        fig.add_hline(y=param['valor_esperado_max'], line_dash="dash", line_color="#f59e0b", annotation_text="Límite Nominal Máx")
        fig.add_hline(y=param['valor_esperado_min'], line_dash="dash", line_color="#f59e0b", annotation_text="Límite Nominal Mín")
        fig.add_hline(y=param['umbral_critico_max'], line_dash="dot", line_color="#ef4444", annotation_text="Alarma Crítica")

        # Marcar anomalías (Dudoso / Inválido)
        anomalias = df_lect[df_lect["calidad_dato"] != "Válido"]
        if not anomalias.empty:
            fig.add_trace(go.Scatter(
                x=anomalias["timestamp_lectura"],
                y=anomalias["valor_medido"],
                mode="markers",
                name="Lectura Anómala / Ruido",
                marker=dict(color="#dc2626", size=9, symbol="diamond")
            ))

        fig.update_layout(
            height=420,
            xaxis_title="Tiempo de Registro",
            yaxis_title=f"Valor ({sensor_obj['unidad_medida']})",
            hovermode="x unified",
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Resumen de calidad de datos
        st.markdown("#### 🎯 Auditoría de Calidad de Datos (Data Quality)")
        val_counts = df_lect["calidad_dato"].value_counts().to_dict()
        q1, q2, q3 = st.columns(3)
        with q1:
            st.success(f"✅ Válidos: {val_counts.get('Válido', 0)} ({val_counts.get('Válido', 0)/len(df_lect)*100:.1f}%)")
        with q2:
            st.warning(f"⚠️ Dudosos: {val_counts.get('Dudoso', 0)} ({val_counts.get('Dudoso', 0)/len(df_lect)*100:.1f}%)")
        with q3:
            st.error(f"❌ Inválidos / Ruido: {val_counts.get('Inválido', 0)} ({val_counts.get('Inválido', 0)/len(df_lect)*100:.1f}%)")

        # Exportación CSV
        csv_data = df_lect.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Lecturas a CSV",
            data=csv_data,
            file_name=f"lecturas_sensor_{sensor_obj['codigo_sensor']}.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay lecturas registradas para el sensor seleccionado.")
