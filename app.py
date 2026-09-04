"""
Punto de Entrada Principal - Sistema de Mantenimiento Predictivo con IA.
Universidad Nacional de Trujillo - Escuela de Ingeniería de Sistemas (IS-402).
Semestre 2026-II.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Mantenimiento Predictivo - UNT IS-402",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config.settings import RANDOM_STATE
from auth.authentication import AuthManager, USUARIOS_INICIALES, PERMISOS_SISTEMA
from database.queries import _MEMORY_DB, get_equipos
from modules.dashboard import render_dashboard
from modules.equipos import render_equipos
from modules.sensores import render_sensores
from modules.eda import render_eda
from modules.ia_engine import PredictiveMaintenanceAIEngine
from modules.alertas import render_alertas
from modules.reportes import render_reportes
from modules.usuarios import render_usuarios
from modules.configuracion import render_configuracion

def load_css():
    """Carga estilos CSS personalizados para una interfaz moderna y ejecutiva."""
    try:
        with open("assets/styles.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

# Motor de IA Singleton
@st.cache_resource
def get_ai_engine():
    return PredictiveMaintenanceAIEngine(seed=RANDOM_STATE)


# -----------------------------------------------------------------------------
# SUB-RENDERER DEL MOTOR DE IA (CRISP-DM FASES 4, 5, 6)
# -----------------------------------------------------------------------------
def render_ia_engine_ui():
    st.markdown("## 🧠 Motor de Inteligencia Artificial (CRISP-DM Fases 4, 5 y 6)")
    st.caption("Implementación de modelos supervisados y deep learning para reducción de fallas no planificadas.")

    ai_engine = get_ai_engine()
    user = st.session_state.get("user", {})

    tab_fase4, tab_fase5, tab_fase6 = st.tabs([
        "⚙️ FASE 4: Modelado & SMOTE",
        "📊 FASE 5: Evaluación Rigurosa (5 Algoritmos)",
        "🚀 FASE 6: Despliegue & Inferencia Online (<1s)"
    ])

    with tab_fase4:
        st.markdown("#### Configuración de Entrenamiento y Balanceo de Clases")
        st.markdown("""
        - **Técnica de Balanceo**: **SMOTE** (Synthetic Minority Over-sampling Technique) aplicado **únicamente sobre el 70% de entrenamiento**.
        - **Semilla Fija**: `random_state = 42` para reproducibilidad matemática estricta.
        - **Algoritmos Entrenados**:
          1. **Random Forest**: Ensamble de 150 árboles, max_depth=12, min_samples_split=4.
          2. **XGBoost**: Gradient Boosting de 200 árboles, learning_rate=0.05, subsample=0.85.
          3. **SVM**: Support Vector Machine con kernel RBF, C=2.5.
          4. **CNN-LSTM**: Convolución 1D para extracción de features locales + LSTM para dependencias temporales.
          5. **LSTM-Autoencoder + RF**: Reducción dimensional no lineal con Autoencoder + Clasificador Random Forest.
        """)

        st.info("Todos los artefactos se encuentran persistidos en `/models/` con metadatos registrados en tabla `modelo_ia`.")

    with tab_fase5:
        st.markdown("#### FASE 5: Matriz Comparativa y Validación Cruzada")
        st.caption("Criterios de éxito de negocio minero: Recall >= 90%, F1-Score >= 0.85, Accuracy >= 85%.")

        df_comp = ai_engine.get_models_comparison_table()
        st.dataframe(df_comp, use_container_width=True, hide_index=True)

        best_m = ai_engine.get_best_model()
        st.success(f"🏆 **Modelo Campeón Seleccionado:** `{best_m['nombre_modelo']}` con F1-Score de **{best_m['f1_score']*100:.2f}%** y Recall de **{best_m['recall']*100:.2f}%**.")

        col_roc, col_feat = st.columns(2)
        with col_roc:
            st.markdown("##### Curvas de Desempeño y Matriz de Confusión (XGBoost)")
            cm = best_m["matriz_confusion"]
            df_cm = pd.DataFrame(cm, index=["Real: Normal (0)", "Real: Falla (1)"], columns=["Pred: Normal (0)", "Pred: Falla (1)"])
            fig_cm = px.imshow(df_cm, text_auto=True, color_continuous_scale="Blues", aspect="auto")
            fig_cm.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_cm, use_container_width=True)

        with col_feat:
            st.markdown("##### Ranking de Importancia de Variables (Feature Importance)")
            rf_res = ai_engine._evaluation_results["XGBoost"]
            df_feat = pd.DataFrame(rf_res["caracteristicas_usadas"]["ranking"])
            fig_feat = px.bar(
                df_feat, x="importance", y="feature", orientation="h",
                color="importance", color_continuous_scale="Viridis",
                labels={"importance": "Importancia Normalizada", "feature": "Característica"}
            )
            fig_feat.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_feat, use_container_width=True)

        st.markdown("##### 🧪 Pruebas Estadísticas de Hipótesis y Resiliencia")
        stat_res = ai_engine.perform_statistical_tests()
        s_c1, s_c2, s_c3 = st.columns(3)
        with s_c1:
            st.metric("Prueba t Pareada (XGB vs RF)", f"t = {stat_res['paired_ttest_rf']['t_statistic']}", f"p-val: {stat_res['paired_ttest_rf']['p_value']}")
            st.caption(stat_res['paired_ttest_rf']['conclusion'])
        with s_c2:
            st.metric("Prueba t Pareada (XGB vs SVM)", f"t = {stat_res['paired_ttest_svm']['t_statistic']}", f"p-val: {stat_res['paired_ttest_svm']['p_value']}")
            st.caption(stat_res['paired_ttest_svm']['conclusion'])
        with s_c3:
            boot = stat_res["bootstrap_95_ci_xgboost"]
            st.metric("Bootstrap 95% CI (F1)", f"[{boot['ci_lower']} - {boot['ci_upper']}]", f"F1 Medio: {boot['mean_f1']}")
            st.caption("Intervalo de confianza con 1,000 remuestreos.")

    with tab_fase6:
        st.markdown("#### FASE 6: Despliegue e Inferencia Interactiva bajo Demanda (< 1 segundo)")
        st.caption("Simulación de adquisición de sensores e inferencia del modelo campeón en producción.")

        equipos = get_equipos()
        col_in1, col_in2 = st.columns([2, 3])

        with col_in1:
            with st.form("form_inferencia_predictiva"):
                sel_eq = st.selectbox("Equipo a Evaluar:", [f"{e['codigo_equipo']} - {e['nombre_equipo']}" for e in equipos])
                id_eq = int(sel_eq.split()[0].replace("EQ-MIN-", ""))

                st.markdown("**Valores Actuales de Telemetría:**")
                temp_in = st.slider("Temperatura Motor (°C)", 50.0, 115.0, 84.0)
                presion_in = st.slider("Presión Aceite Motor (bar)", 1.5, 7.5, 4.6)
                vib_in = st.slider("Vibración Rodamientos (mm/s)", 0.5, 25.0, 6.2)
                rpm_in = st.slider("Velocidad Giro RPM", 800.0, 2400.0, 1720.0)
                std_vib_in = st.slider("Rolling Std Vibración (6h)", 0.1, 4.0, 0.75)
                delta_p_in = st.slider("Delta Caída Presión (bar)", -1.5, 1.5, -0.25)

                btn_infer = st.form_submit_button("⚡ Ejecutar Inferencia de Falla", type="primary")

        with col_in2:
            if btn_infer:
                # Inferencia en tiempo real
                resultado = ai_engine.predict_equipment_failure(
                    id_equipo=id_eq,
                    sensor_values={
                        "temperatura": temp_in,
                        "presion_aceite": presion_in,
                        "vibracion": vib_in,
                        "rpm": rpm_in,
                        "rolling_vib_std": std_vib_in,
                        "delta_presion": delta_p_in
                    },
                    user_name=user.get("nombre_usuario", "admin")
                )

                prob = resultado["probabilidad_falla"]
                riesgo = resultado["nivel_riesgo"]
                color_risk = "#10b981" if riesgo == "Bajo" else ("#f59e0b" if riesgo == "Medio" else "#ef4444")

                st.markdown(f"""
                <div style="background: #ffffff; border-radius: 8px; padding: 18px; border: 2px solid {color_risk}; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <h3 style="color: {color_risk}; margin-top: 0;">Nivel de Riesgo Predictivo: {riesgo.upper()}</h3>
                    <p style="font-size: 16px;"><strong>Probabilidad de Falla en 72 Horas:</strong> <span style="font-size: 22px; font-weight: bold;">{prob*100:.2f} %</span></p>
                    <p><strong>Diagnóstico Preliminar:</strong> {resultado['tipo_falla_predicha']}</p>
                    <p><strong>Tiempo de Respuesta (Inferencia):</strong> {resultado['tiempo_inferencia_segundos']*1000:.1f} ms (¡Menor a 1 segundo!)</p>
                    <p><strong>Registro en Base de Datos:</strong> Predicción ID #{resultado['id_prediccion']} guardada en tabla <code>prediccion_falla</code>.</p>
                </div>
                """, unsafe_allow_html=True)

                if "alerta_generada" in resultado:
                    st.error(f"🚨 Se ha generado una alerta automática #{resultado['alerta_generada']['id_alerta']} en el sistema por superar el umbral de seguridad.")
            else:
                st.info("Ajuste las variables de telemetría a la izquierda y presione 'Ejecutar Inferencia de Falla' para diagnosticar el equipo.")

# -----------------------------------------------------------------------------
# VALIDACIÓN DE SESIÓN Y LOGIN
# -----------------------------------------------------------------------------
def main():
    load_css()
    # 1. Validar sesión en CADA rerun de Streamlit
    is_authenticated = AuthManager.validate_current_session()

    if not is_authenticated:
        render_login()
        return

    # 2. Renderizar interfaz principal
    user = st.session_state["user"]
    rol = user.get("rol", "Consultor")

    # Sidebar institucional
    with st.sidebar:
        st.markdown("### ⛏️ Minera San Martín")
        st.caption("UNT - Ingeniería de Sistemas (IS-402)")
        st.markdown("---")

        st.markdown(f"**Usuario:** `{user['nombre_usuario']}`")
        st.markdown(f"**Rol:** `{rol}`")
        st.markdown(f"**Área:** {user.get('area', 'Mantenimiento')}")

        if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True):
            AuthManager.logout()
            st.rerun()

        st.markdown("---")
        st.markdown("#### 🧭 Navegación")

        # Menú dinámico según matriz de permisos
        opciones_menu = ["Dashboard"]
        if AuthManager.check_permission(rol, "ver_equipos"):
            opciones_menu.append("Gestión de Equipos")
        if AuthManager.check_permission(rol, "ver_sensores"):
            opciones_menu.append("Monitoreo de Sensores")
        opciones_menu.append("Análisis Exploratorio (EDA)")
        if AuthManager.check_permission(rol, "ver_modelos"):
            opciones_menu.append("Motor de IA (CRISP-DM)")
        if AuthManager.check_permission(rol, "ver_alertas"):
            opciones_menu.append("Centro de Alertas")
        if AuthManager.check_permission(rol, "generar_reportes"):
            opciones_menu.append("Reportes Técnicos")
        if AuthManager.check_permission(rol, "administrar_usuarios"):
            opciones_menu.append("Usuarios y Roles")
        if AuthManager.check_permission(rol, "configuracion_sistema"):
            opciones_menu.append("Configuración")

        seleccion = st.radio("Ir a:", opciones_menu)

        st.markdown("---")
        st.caption("Semestre Académico 2026-II\nEscuela de Ingeniería de Sistemas - UNT")

    # Enrutamiento de páginas
    if seleccion == "Dashboard":
        render_dashboard()
    elif seleccion == "Gestión de Equipos":
        render_equipos()
    elif seleccion == "Monitoreo de Sensores":
        render_sensores()
    elif seleccion == "Análisis Exploratorio (EDA)":
        render_eda()
    elif seleccion == "Motor de IA (CRISP-DM)":
        render_ia_engine_ui()
    elif seleccion == "Centro de Alertas":
        render_alertas()
    elif seleccion == "Reportes Técnicos":
        render_reportes()
    elif seleccion == "Usuarios y Roles":
        render_usuarios()
    elif seleccion == "Configuración":
        render_configuracion()

def render_login():
    """Pantalla de Login con protección de fuerza bruta y validación bcrypt."""
    load_css()
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>UNIVERSIDAD NACIONAL DE TRUJILLO</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #475569;'>Ingeniería de Software II (IS-402) - Semestre 2026-II</h4>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-bottom: 24px;'>Sistema de Mantenimiento Predictivo con Inteligencia Artificial</h3>", unsafe_allow_html=True)

    if "logout_message" in st.session_state:
        st.warning(st.session_state.pop("logout_message"))

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("form_login"):
            st.markdown("##### Iniciar Sesión en el Sistema")
            identifier = st.text_input("Usuario o Correo Electrónico", value="admin")
            password = st.text_input("Contraseña", type="password", value="Admin123*")
            submit = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)

            if submit:
                users_list = _MEMORY_DB.get("usuario", USUARIOS_INICIALES)
                success, msg, user_obj, token, exp_time = AuthManager.authenticate(identifier, password, users_list)

                if success:
                    st.session_state["auth_token"] = token
                    st.session_state["user"] = user_obj
                    st.session_state["session_expiracion"] = exp_time
                    st.success("Autenticación correcta. Redirigiendo...")
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown("---")
        st.markdown("**Credenciales de prueba disponibles:**")
        st.markdown("""
        - **Administrador:** `admin` / `Admin123*`
        - **Supervisor:** `supervisor` / `Super123*`
        - **Técnico:** `tecnico` / `Tecnico123*`
        - **Consultor:** `consultor` / `Consultor123*`
        """)

if __name__ == "__main__":
    main()
