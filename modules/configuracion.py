"""
Módulo 9: CONFIGURACIÓN GENERAL DEL SISTEMA Y VERSIONES.
- Gestión de parámetros de 'configuracion_sistema'.
- Historial de cambios y despliegues en 'version_sistema'.
- Diagnóstico de conectividad a PostgreSQL 'bd_mantenimiento_predictivo'.
- Herramienta de regeneración de datos sintéticos reproducibles (semilla=42).
"""

import streamlit as st
import pandas as pd

from database.connection import get_db_manager
from database.queries import _MEMORY_DB, _DATA_ENGINE
from auth.authentication import AuthManager

def render_configuracion():
    st.markdown("## ⚙️ Configuración del Sistema & Diagnóstico Operativo")
    st.caption("Ajuste de parámetros globales, umbrales de telemetría y estado de infraestructura.")

    user = st.session_state.get("user", {})
    rol = user.get("rol", "Técnico")
    can_config = AuthManager.check_permission(rol, "configuracion_sistema")

    tab_params, tab_version, tab_db, tab_datos = st.tabs([
        "🔧 Parámetros Operativos", "🏷️ Versiones del Sistema", "🗄️ Estado de Base de Datos", "🔄 Generador de Datos Sintéticos"
    ])

    with tab_params:
        st.markdown("#### Parámetros Globales (tabla 'configuracion_sistema')")
        configs = _MEMORY_DB.get("configuracion_sistema", [])
        df_cfg = pd.DataFrame(configs)
        st.dataframe(df_cfg, use_container_width=True, hide_index=True)

        if can_config:
            st.markdown("##### Modificar Parámetro")
            with st.form("form_edit_param"):
                sel_param = st.selectbox("Clave de Configuración:", [c["clave_configuracion"] for c in configs])
                nuevo_val = st.text_input("Nuevo Valor:")
                if st.form_submit_button("Guardar Cambio"):
                    for c in configs:
                        if c["clave_configuracion"] == sel_param:
                            c["valor_configuracion"] = nuevo_val
                            st.success(f"Parámetro '{sel_param}' actualizado a '{nuevo_val}'.")
                            st.rerun()

    with tab_version:
        st.markdown("#### Historial de Versiones y Despliegues (tabla 'version_sistema')")
        versions = _MEMORY_DB.get("version_sistema", [])
        st.dataframe(pd.DataFrame(versions), use_container_width=True, hide_index=True)

    with tab_db:
        st.markdown("#### Diagnóstico de Base de Datos PostgreSQL")
        manager = get_db_manager()
        if manager.is_connected:
            st.success("🟢 Conexión Activa con Base de Datos 'bd_mantenimiento_predictivo' (Pool SimpleConnectionPool 1-20 conexiones).")
        else:
            st.warning("🟡 Modo Fallback Activo: PostgreSQL local no detectado en puerto 5432. El sistema opera con su motor de datos sintéticos reproducibles en memoria.")

        st.markdown("""
        **Verificación de Esquema:**
        - Total de tablas mapeadas: **30 tablas relacionales**.
        - Vistas implementadas: `vista_equipos_completos`, `vista_lecturas_recientes`, `vista_resumen_kpi_equipo`.
        - Funciones PostgreSQL: `contar_fallas_equipo(p_id_equipo)`, `ultimo_mantenimiento_equipo(p_id_equipo)`.
        """)

    with tab_datos:
        st.markdown("#### Motor de Generación de Datos Sintéticos (random_state=42)")
        st.write("Genera datos coherentes para 12 equipos mineros, 60 sensores, 10,000 lecturas y fallas históricas.")
        if st.button("🔄 Regenerar Datos Sintéticos con Semilla 42", type="secondary"):
            fresh_data = _DATA_ENGINE.generate_all_data()
            for k, v in fresh_data.items():
                _MEMORY_DB[k] = v
            st.success("¡Datos regenerados exitosamente con random_state=42!")
            st.rerun()
