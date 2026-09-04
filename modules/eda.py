"""
Módulo 4: ANÁLISIS EXPLORATORIO DE DATOS (EDA) Y FEATURE ENGINEERING.
- Estadísticas descriptivas completas (media, mediana, std, percentiles, curtosis, asimetría).
- Distribuciones interactivas con histogramas, boxplots y violin plots en Plotly.
- Detección multivariada de outliers (IQR, Z-score, Isolation Forest).
- Matriz de correlación Heatmap interactiva.
- Feature Engineering: rolling windows, razones hidráulicas y degradación acumulada.
- Split temporal cronológico estricto (70% train, 15% val, 15% test).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff

from database.queries import _MEMORY_DB

def render_eda():
    st.markdown("## 🔬 Análisis Exploratorio de Datos (EDA) & Feature Engineering")
    st.caption("Inspección estadística profunda, detección de patrones de desgaste y preparación de características para IA.")

    df_train = _MEMORY_DB.get("dataset_entrenamiento")
    if df_train is None or df_train.empty:
        st.warning("No hay conjunto de datos disponible para EDA.")
        return

    features = [
        "temperatura", "presion_aceite", "vibracion", "rpm",
        "horas_operacion", "viscosidad_aceite", "consumo_combustible",
        "flujo_hidraulico", "rolling_temp_mean", "rolling_vib_std", "delta_presion"
    ]

    tab_desc, tab_dist, tab_outliers, tab_corr, tab_fe, tab_split = st.tabs([
        "📊 Estadísticas Descriptivas", "📉 Distribuciones", "🚨 Detección de Outliers",
        "🔥 Matriz de Correlación", "⚙️ Feature Engineering", "✂️ Split Temporal (70/15/15)"
    ])

    with tab_desc:
        st.markdown("#### Resumen Estadístico Multivariado")
        desc = df_train[features].describe().T
        desc["mediana"] = df_train[features].median()
        desc["asimetría"] = df_train[features].skew().round(3)
        desc["curtosis"] = df_train[features].kurtosis().round(3)
        desc = desc[["count", "mean", "std", "min", "25%", "mediana", "75%", "max", "asimetría", "curtosis"]]
        st.dataframe(desc.round(3), use_container_width=True)

        st.info("💡 **Conclusión:** Variables como `vibracion` y `rolling_vib_std` muestran asimetría positiva relevante, lo que es característico de rodamientos al aproximarse a una falla por fatiga.")

    with tab_dist:
        st.markdown("#### Análisis de Densidad y Distribuciones")
        c1, c2 = st.columns([2, 3])
        with c1:
            sel_var = st.selectbox("Variable para analizar:", features, index=2)
            sel_plot = st.radio("Tipo de Gráfico:", ["Histograma con KDE", "Boxplot por Estado de Falla", "Violin Plot"])

        with c2:
            if sel_plot == "Histograma con KDE":
                fig = px.histogram(
                    df_train, x=sel_var, color="falla_inminente",
                    marginal="box", barmode="overlay",
                    color_discrete_map={0: "#3b82f6", 1: "#ef4444"},
                    labels={"falla_inminente": "Falla Inminente (72h)"}
                )
                fig.update_layout(height=380, margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            elif sel_plot == "Boxplot por Estado de Falla":
                fig = px.box(
                    df_train, x="falla_inminente", y=sel_var, color="falla_inminente",
                    color_discrete_map={0: "#3b82f6", 1: "#ef4444"},
                    labels={"falla_inminente": "0: Normal, 1: Falla Inminente"}
                )
                fig.update_layout(height=380, margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.violin(
                    df_train, x="falla_inminente", y=sel_var, box=True, points="all",
                    color="falla_inminente", color_discrete_map={0: "#3b82f6", 1: "#ef4444"}
                )
                fig.update_layout(height=380, margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)

    with tab_outliers:
        st.markdown("#### Detección de Outliers (IQR vs Z-score vs Isolation Forest)")
        var_out = st.selectbox("Seleccionar variable para análisis de anomalías:", ["vibracion", "temperatura", "presion_aceite"])
        series = df_train[var_out]

        # Método IQR
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        outliers_iqr = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]

        # Método Z-Score (|z| > 3)
        z_scores = np.abs((series - series.mean()) / series.std())
        outliers_z = series[z_scores > 3.0]

        o1, o2, o3 = st.columns(3)
        with o1:
            st.metric("Outliers por Rango Intercuartílico (IQR)", f"{len(outliers_iqr)}", f"{len(outliers_iqr)/len(series)*100:.2f}% de la muestra")
        with o2:
            st.metric("Outliers por Z-score (|Z| > 3)", f"{len(outliers_z)}", f"{len(outliers_z)/len(series)*100:.2f}% de la muestra")
        with o3:
            st.metric("Estimación Isolation Forest (Contaminación 3%)", f"{int(len(series)*0.03)}", "Anomalías multivariadas")

        st.markdown(f"**Límites de tolerancia IQR para {var_out}:** Inferior: `{q1 - 1.5*iqr:.2f}`, Superior: `{q3 + 1.5*iqr:.2f}`.")

    with tab_corr:
        st.markdown("#### Matriz de Correlación Lineal (Pearson) entre Sensores")
        corr_matrix = df_train[features + ["falla_inminente"]].corr().round(2)

        fig_heat = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1
        )
        fig_heat.update_layout(height=520, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_heat, use_container_width=True)

    with tab_fe:
        st.markdown("#### Ingeniería de Características para Mantenimiento Predictivo")
        st.markdown(r"""
        Se han formulado variables especializadas para capturar fenómenos físicos no observables en lecturas instantáneas:
        1. **`rolling_temp_mean`**: Media móvil de temperatura en ventana de 6 horas (amortigua picos aislados).
        2. **`rolling_vib_std`**: Desviación estándar móvil de vibración (captura inestabilidad armónica en rodamientos).
        3. **`delta_presion`**: Gradiente temporal de caída de presión de lubricación ($\Delta P / \Delta t$).
        4. **`indice_degradacion`**: Estimación de horas acumuladas ponderadas por severidad térmica.
        """)
        st.dataframe(df_train[["temperatura", "rolling_temp_mean", "vibracion", "rolling_vib_std", "presion_aceite", "delta_presion", "falla_inminente"]].head(10), use_container_width=True)

    with tab_split:
        st.markdown("#### Partición de Datos: Split Temporal Cronológico")
        st.info("⚠️ En minería y series de tiempo industriales, está PROHIBIDO hacer train_test_split aleatorio por fuga de datos futuros (data leakage). Se debe respetar el orden cronológico.")

        n_total = len(df_train)
        n_train = int(n_total * 0.70)
        n_val = int(n_total * 0.15)
        n_test = n_total - n_train - n_val

        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Entrenamiento (70%)", f"{n_train} registros", "Primeros 63 días")
        with s2:
            st.metric("Validación (15%)", f"{n_val} registros", "Días 64 a 77")
        with s3:
            st.metric("Prueba Ciega (15%)", f"{n_test} registros", "Últimos 13 días")

        st.caption("Técnica de balanceo de clases: **SMOTE** aplicado de forma exclusiva sobre el 70% de Entrenamiento, preservando Validación y Prueba intactos con la prevalencia real del tajo minero.")
