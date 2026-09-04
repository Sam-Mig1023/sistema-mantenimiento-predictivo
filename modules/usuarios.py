"""
Módulo 8: ADMINISTRACIÓN DE USUARIOS, ROLES Y SEGURIDAD RBAC.
- CRUD de usuarios con SOFT DELETE obligatorio (estado_usuario = FALSE).
- Gestión de roles (Administrador, Supervisor, Técnico, Consultor).
- Matriz de permisos visual e interactiva (rol_permiso, permiso).
- Auditoría de sesiones activas (session_usuario).
- Registro histórico de bitácora y auditoría forense (bitacora_actividad).
"""

from datetime import datetime
import streamlit as st
import pandas as pd

from database.queries import (
    get_usuarios, create_usuario, soft_delete_usuario, _MEMORY_DB, log_bitacora
)
from auth.authentication import AuthManager, PERMISOS_SISTEMA

def render_usuarios():
    st.markdown("## 👥 Administración de Usuarios y Seguridad RBAC")
    st.caption("Control de acceso basado en roles, auditoría de sesiones y bitácora forense de operaciones.")

    current_user = st.session_state.get("user", {})
    rol = current_user.get("rol", "Técnico")
    if not AuthManager.check_permission(rol, "administrar_usuarios"):
        st.error("Acceso restringido: Se requieren privilegios de Administrador del Sistema.")
        return

    # Mensaje global persistente para avisos tras recargar la página
    if "mensaje_usuario_global" in st.session_state:
        st.success(st.session_state.pop("mensaje_usuario_global"))

    tab_usuarios, tab_nuevo, tab_matriz, tab_sesiones, tab_bitacora = st.tabs([
        "📋 Usuarios Registrados", "➕ Registrar Usuario", "🛡️ Matriz de Permisos", "🔑 Sesiones Activas", "📜 Bitácora de Actividades"
    ])

    with tab_usuarios:
        usuarios = get_usuarios(incluir_inactivos=True)
        df_u = pd.DataFrame(usuarios)
        cols = ["id_usuario", "nombre_usuario", "email", "nombres", "apellidos", "cargo", "area", "rol", "estado_usuario", "intentos_fallidos"]
        st.dataframe(df_u[cols], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### Desactivación de Usuario (Soft Delete)")
        opciones_desact = [u["nombre_usuario"] for u in usuarios if u.get("estado_usuario", True) and u["id_usuario"] != current_user.get("id_usuario", 1)]
        if opciones_desact:
            u_desact = st.selectbox("Seleccionar Usuario para Desactivar:", opciones_desact)
            if st.button(f"🗑️ Desactivar Usuario '{u_desact}' (Soft Delete)", type="secondary"):
                target_u = next(u for u in usuarios if u["nombre_usuario"] == u_desact)
                soft_delete_usuario(target_u["id_usuario"], current_user.get("id_usuario", 1))
                st.session_state["mensaje_usuario_global"] = f"✅ Usuario '{u_desact}' desactivado (estado_usuario = FALSE). Se preserva integridad referencial."
                st.rerun()
        else:
            st.info("No hay otros usuarios activos disponibles para desactivar.")

    with tab_nuevo:
        st.markdown("#### Registrar Nuevo Usuario del Sistema")
        st.caption("Complete los campos obligatorios (*) para dar de alta una nueva cuenta con rol RBAC.")

        # Notificación de éxito específica en la pestaña de registro
        if "registro_usuario_exito" in st.session_state:
            st.success(st.session_state.pop("registro_usuario_exito"))

        with st.form("form_nuevo_usuario", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                username = st.text_input("Nombre de Usuario *", placeholder="Ej: jquispe")
                email = st.text_input("Correo Institucional *", placeholder="Ej: jquispe@mina.pe")
                pwd = st.text_input("Contraseña Temporal *", type="password", placeholder="Mínimo 6 caracteres")
                nombres = st.text_input("Nombres *", placeholder="Ej: Juan Carlos")
            with c2:
                apellidos = st.text_input("Apellidos *", placeholder="Ej: Quispe Ramos")
                cargo = st.text_input("Cargo", value="Ingeniero de Mantenimiento")
                area = st.selectbox("Área", ["Mantenimiento", "Operaciones Mina", "Confiabilidad", "Tecnología"])
                rol_sel = st.selectbox("Rol Asignado", ["Administrador", "Supervisor", "Técnico", "Consultor"])

            sub = st.form_submit_button("💾 Crear Cuenta de Usuario", type="primary", use_container_width=True)
            if sub:
                u_clean = username.strip()
                e_clean = email.strip()
                p_clean = pwd.strip()
                n_clean = nombres.strip()
                a_clean = apellidos.strip()

                if not u_clean or not e_clean or not p_clean or not n_clean or not a_clean:
                    st.error("⚠️ Todos los campos marcados con asterisco (*) son obligatorios.")
                elif len(p_clean) < 6:
                    st.error("⚠️ La contraseña debe tener al menos 6 caracteres por políticas de seguridad.")
                else:
                    success, msg, nuevo = create_usuario({
                        "nombre_usuario": u_clean,
                        "email": e_clean,
                        "contrasena_hash": AuthManager.hash_password(p_clean),
                        "nombres": n_clean,
                        "apellidos": a_clean,
                        "cargo": cargo.strip() if cargo else "Operador",
                        "area": area,
                        "rol": rol_sel
                    }, current_user.get("id_usuario", 1))

                    if success:
                        msg_exito = (
                            f"✅ ¡El usuario **{u_clean}** ({rol_sel}) ha sido registrado exitosamente!\n\n"
                            f"• **ID Asignado:** #{nuevo['id_usuario']}\n"
                            f"• **Correo:** {e_clean}\n"
                            f"• **Rol:** {rol_sel}\n"
                            f"• **Estado:** Activo\n\n"
                            f"El formulario ha sido limpiado y las credenciales ya se encuentran operativas para iniciar sesión."
                        )
                        st.session_state["registro_usuario_exito"] = msg_exito
                        st.session_state["mensaje_usuario_global"] = f"✅ Usuario '{u_clean}' registrado exitosamente."
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")

    with tab_matriz:
        st.markdown("#### Matriz de Control de Acceso Basado en Roles (RBAC)")
        st.caption("Configuración de privilegios por rol (tablas 'rol_permiso' y 'permiso').")
        all_perms = [
            "ver_dashboard", "ver_equipos", "editar_equipos", "ver_sensores", "editar_sensores",
            "ver_modelos", "entrenar_modelos", "ver_predicciones", "generar_reportes",
            "administrar_usuarios", "ver_alertas", "gestionar_alertas", "configuracion_sistema"
        ]
        matrix_rows = []
        for p in all_perms:
            matrix_rows.append({
                "Permiso del Sistema": p,
                "Administrador": "✅ Permitido" if p in PERMISOS_SISTEMA["Administrador"] else "❌ Denegado",
                "Supervisor": "✅ Permitido" if p in PERMISOS_SISTEMA["Supervisor"] else "❌ Denegado",
                "Técnico": "✅ Permitido" if p in PERMISOS_SISTEMA["Técnico"] else "❌ Denegado",
                "Consultor": "✅ Permitido" if p in PERMISOS_SISTEMA["Consultor"] else "❌ Denegado"
            })
        st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)

    with tab_sesiones:
        st.markdown("#### Monitor de Sesiones de Usuario (session_usuario)")
        sesiones = _MEMORY_DB.get("session_usuario", [])
        if not sesiones:
            # Mostrar la sesión actual
            sesiones = [{
                "id_session": 1,
                "id_usuario": current_user.get("id_usuario", 1),
                "token_jwt": st.session_state.get("auth_token", "jwt_token_unt_active")[:25] + "...",
                "ip_origen": "127.0.0.1",
                "user_agent": "Streamlit Cloud Client / Chrome 124",
                "fecha_inicio": "2026-09-03 08:00",
                "fecha_expiracion": "2026-09-03 09:00",
                "estado_session": "Activa"
            }]
        st.dataframe(pd.DataFrame(sesiones), use_container_width=True, hide_index=True)

    with tab_bitacora:
        st.markdown("#### Registro Histórico de Auditoría (bitacora_actividad)")
        bits = _MEMORY_DB.get("bitacora_actividad", [])
        if bits:
            df_b = pd.DataFrame(bits)
            cols_b = ["id_bitacora", "id_usuario", "fecha_hora", "ip_origen", "tipo_actividad", "modulo", "accion_realizada", "tabla_afectada", "estado_operacion"]
            st.dataframe(df_b[cols_b].sort_values("id_bitacora", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No hay eventos de auditoría registrados.")
