"""
Módulo 6: GESTIÓN DE ALERTAS Y NOTIFICACIONES.
- Panel de alertas activas por gravedad (Información, Advertencia, Crítico, Emergencia).
- Ciclo de vida completo: Generada -> Enviada -> Leída -> EnProceso -> Resuelta.
- Acciones de gestión: Marcar como leída, asignar técnico, resolver con bitácora obligatoria.
- Historial y métricas de resolución (MTTA - Mean Time to Acknowledge).
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from database.queries import get_alertas, update_alerta_estado, get_equipos, _MEMORY_DB
from auth.authentication import AuthManager

def render_alertas():
    st.markdown("## 🚨 Centro de Gestión de Alertas y Eventos Críticos")
    st.caption("Control operativo, despacho a cuadrillas de mantenimiento y resolución trazable.")

    user = st.session_state.get("user", {})
    rol = user.get("rol", "Técnico")
    can_manage = AuthManager.check_permission(rol, "gestionar_alertas")

    alertas = get_alertas()
    equipos = {e["id_equipo"]: e["codigo_equipo"] for e in get_equipos(incluir_desactivados=True)}

    # KPIs de Alertas
    activas = [a for a in alertas if a["estado_alerta"] != "Resuelta"]
    criticas = [a for a in activas if a["nivel_gravedad"] in ["Crítico", "Emergencia"]]
    resueltas = [a for a in alertas if a["estado_alerta"] == "Resuelta"]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Alertas Activas", f"{len(activas)}")
    with k2:
        st.metric("Críticas / Emergencia", f"{len(criticas)}", delta_color="inverse")
    with k3:
        st.metric("En Atención (EnProceso)", f"{sum(1 for a in activas if a['estado_alerta'] == 'EnProceso')}")
    with k4:
        st.metric("Resueltas este Mes", f"{len(resueltas)}")

    st.markdown("---")

    tab_activas, tab_historial = st.tabs(["⚡ Alertas Activas en Trámite", "📜 Historial de Alertas Resueltas"])

    with tab_activas:
        filtro_grav = st.multiselect(
            "Filtrar por Severidad:",
            ["Información", "Advertencia", "Crítico", "Emergencia"],
            default=["Crítico", "Emergencia", "Advertencia"]
        )

        alertas_filtradas = [a for a in activas if a["nivel_gravedad"] in filtro_grav]

        if not alertas_filtradas:
            st.success("No hay alertas activas para el filtro seleccionado.")
        else:
            for al in alertas_filtradas[:15]:
                grav = al["nivel_gravedad"]
                color_border = "#ef4444" if grav in ["Crítico", "Emergencia"] else ("#f59e0b" if grav == "Advertencia" else "#3b82f6")
                eq_code = equipos.get(al["id_equipo"], f"EQ-{al['id_equipo']}")

                with st.container():
                    st.markdown(f"""
                    <div style="border-left: 5px solid {color_border}; padding: 12px; background: #ffffff; border-radius: 6px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="color: #1e3a8a; font-size: 15px;">[{eq_code}] {al['tipo_alerta']} - Nivel: {al['nivel_gravedad']}</strong>
                            <span style="font-size: 12px; color: #64748b;">Generada: {al['fecha_generacion'].strftime('%d/%m/%Y %H:%M') if isinstance(al['fecha_generacion'], datetime) else str(al['fecha_generacion'])}</span>
                        </div>
                        <p style="margin: 6px 0; color: #334155;">{al['mensaje_alerta']}</p>
                        <div style="font-size: 13px; color: #64748b;">
                            Estado actual: <span style="font-weight: 600; color: #0f172a;">{al['estado_alerta']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if can_manage:
                        btn_c1, btn_c2, btn_c3 = st.columns([2, 2, 4])
                        with btn_c1:
                            if al["estado_alerta"] == "Generada":
                                if st.button(f"👁️ Marcar Leída #{al['id_alerta']}", key=f"read_{al['id_alerta']}"):
                                    update_alerta_estado(al["id_alerta"], "Leída", user.get("nombre_usuario", "admin"))
                                    st.rerun()
                        with btn_c2:
                            if al["estado_alerta"] in ["Generada", "Leída"]:
                                if st.button(f"🛠️ Atender #{al['id_alerta']}", key=f"proc_{al['id_alerta']}"):
                                    update_alerta_estado(al["id_alerta"], "EnProceso", user.get("nombre_usuario", "admin"))
                                    st.rerun()
                        with btn_c3:
                            with st.popover(f"✅ Resolver #{al['id_alerta']}"):
                                motivo = st.text_input("Comentarios de Solución Aplicada *", key=f"com_{al['id_alerta']}")
                                if st.button("Confirmar Solución", key=f"res_{al['id_alerta']}"):
                                    if not motivo:
                                        st.error("El comentario de resolución es obligatorio.")
                                    else:
                                        update_alerta_estado(al["id_alerta"], "Resuelta", user.get("nombre_usuario", "admin"), motivo)
                                        st.success(f"Alerta #{al['id_alerta']} resuelta y archivada.")
                                        st.rerun()

    with tab_historial:
        st.markdown("#### Historial de Resoluciones y Causa-Efecto")
        if resueltas:
            df_res = pd.DataFrame(resueltas)
            cols = ["id_alerta", "id_equipo", "tipo_alerta", "nivel_gravedad", "mensaje_alerta", "fecha_generacion", "fecha_resolucion", "usuario_resolvio", "comentarios_resolucion"]
            st.dataframe(df_res[cols], use_container_width=True, hide_index=True)
        else:
            st.info("No hay alertas resueltas aún.")
