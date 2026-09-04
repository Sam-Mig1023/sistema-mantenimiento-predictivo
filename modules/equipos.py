"""
Módulo 2: GESTIÓN DE EQUIPOS (Mantenimiento de Flota Minera).
- CRUD completo de equipos con SOFT DELETE obligatorio (estado_operativo='Desactivado').
- Visualización con vista_equipos_completos.
- Ficha técnica y detalle: sensores, historial de mantenimientos, fallas, KPIs.
- Árbol de dependencias entre equipos (dependencia_equipo).
- Gestión de repuestos (pieza_reposicion) y programación (mantenimiento_programado).
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from database.queries import (
    get_equipos, create_equipo, update_equipo, soft_delete_equipo,
    contar_fallas_equipo, ultimo_mantenimiento_equipo, _MEMORY_DB
)
from auth.authentication import AuthManager

def render_equipos():
    st.markdown("## 🚜 Gestión de Flota y Activos Industriales")
    st.caption("Administración del ciclo de vida de maquinaria pesada, repuestos y dependencias de proceso.")

    user = st.session_state.get("user", {})
    rol = user.get("rol", "Técnico")
    can_edit = AuthManager.check_permission(rol, "editar_equipos")

    tab_equipos, tab_nuevo, tab_dependencias, tab_repuestos, tab_programados = st.tabs([
        "📋 Catálogo de Equipos", "➕ Registrar / Editar Equipo", "🌳 Árbol de Dependencias", "⚙️ Stock de Piezas", "📅 Mantenimientos Programados"
    ])

    with tab_equipos:
        col_busq, col_filtro = st.columns([3, 2])
        with col_busq:
            query = st.text_input("Buscar por código, nombre o marca:", placeholder="Ej. PC8000, 797F, Komatsu...")
        with col_filtro:
            incluir_inactivos = st.checkbox("Mostrar equipos desactivados (Soft Deleted)", value=False)

        equipos = get_equipos(incluir_desactivados=incluir_inactivos)
        if query:
            q = query.lower()
            equipos = [e for e in equipos if q in e["nombre_equipo"].lower() or q in e["codigo_equipo"].lower() or q in e.get("marca", "").lower()]

        df_eq = pd.DataFrame(equipos)
        if not df_eq.empty:
            cols_show = ["codigo_equipo", "nombre_equipo", "tipo_equipo", "categoria_equipo", "marca", "modelo", "estado_operativo", "horas_operacion", "ubicacion_actual"]
            st.dataframe(df_eq[cols_show], use_container_width=True, hide_index=True)

            # Detalle interactivo de equipo seleccionado
            st.markdown("---")
            st.markdown("### 🔍 Ficha Técnica & Diagnóstico de Equipo")
            sel_cod = st.selectbox("Seleccionar equipo para ver diagnóstico profundo:", [e["codigo_equipo"] for e in equipos])
            selected_eq = next((e for e in equipos if e["codigo_equipo"] == sel_cod), None)

            if selected_eq:
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.write(f"**Código:** {selected_eq['codigo_equipo']}")
                    st.write(f"**Nombre:** {selected_eq['nombre_equipo']}")
                    st.write(f"**Año:** {selected_eq.get('ano_fabricacion')}")
                with c2:
                    st.write(f"**Marca:** {selected_eq.get('marca')}")
                    st.write(f"**Modelo:** {selected_eq.get('modelo')}")
                    st.write(f"**N° Serie:** {selected_eq.get('numero_serie')}")
                with c3:
                    st.write(f"**Estado:** `{selected_eq.get('estado_operativo')}`")
                    st.write(f"**Horas Op:** {selected_eq.get('horas_operacion'):,} hrs")
                    st.write(f"**Ubicación:** {selected_eq.get('ubicacion_actual')}")
                with c4:
                    n_fallas = contar_fallas_equipo(selected_eq["id_equipo"])
                    ult_mant = ultimo_mantenimiento_equipo(selected_eq["id_equipo"])
                    st.metric("Total Fallas", f"{n_fallas}")
                    if ult_mant:
                        st.write(f"**Último Mantenimiento:** {ult_mant.get('tipo_evento')} ({ult_mant.get('estado_evento')})")

                # Botón de Soft Delete si tiene permisos
                if can_edit:
                    st.markdown("##### Acciones de Administración")
                    if selected_eq.get("estado_operativo") != "Desactivado":
                        if st.button(f"🗑️ Desactivar {selected_eq['codigo_equipo']} (Soft Delete)", type="secondary"):
                            soft_delete_equipo(selected_eq["id_equipo"], user.get("id_usuario", 1))
                            st.success(f"Equipo {selected_eq['codigo_equipo']} marcado como 'Desactivado' sin romper integridad referencial.")
                            st.rerun()

    with tab_nuevo:
        if not can_edit:
            st.warning("Su rol actual no posee permisos de 'editar_equipos'. Modo de solo lectura.")
        else:
            st.markdown("#### Registrar o Modificar Equipo Industrial")
            with st.form("form_nuevo_equipo"):
                c_a, c_b = st.columns(2)
                with c_a:
                    codigo = st.text_input("Código de Equipo *", value=f"EQ-MIN-{len(_MEMORY_DB['equipo'])+1:03d}")
                    nombre = st.text_input("Nombre de Equipo *", placeholder="Ej: Camión Minero Caterpillar 797F #05")
                    id_tipo = st.selectbox("Tipo de Equipo *", options=[1, 2, 3, 4, 5], format_func=lambda x: {1: "Excavadora", 2: "Camión Minero", 3: "Perforadora", 4: "Cargador Frontal", 5: "Tractor"}[x])
                    marca = st.selectbox("Marca", ["Caterpillar", "Komatsu", "Hitachi", "Liebherr", "Epiroc", "Sandvik"])
                with c_b:
                    modelo = st.text_input("Modelo", placeholder="Ej: 797F / PC8000")
                    ano = st.number_input("Año de Fabricación", min_value=2000, max_value=2026, value=2022)
                    horas = st.number_input("Horas de Operación Acumuladas", min_value=0, value=12500)
                    ubicacion = st.selectbox("Ubicación", ["Tajo Abierto Fase 4", "Tajo Abierto Fase 5", "Botadero Norte", "Planta Chancado", "Taller Central Mina"])

                submit = st.form_submit_button("💾 Guardar Equipo", type="primary")
                if submit:
                    if not codigo or not nombre:
                        st.error("Código y nombre son obligatorios.")
                    else:
                        create_equipo({
                            "codigo_equipo": codigo,
                            "nombre_equipo": nombre,
                            "id_tipo_equipo": id_tipo,
                            "marca": marca,
                            "modelo": modelo,
                            "ano_fabricacion": int(ano),
                            "horas_operacion": int(horas),
                            "ubicacion_actual": ubicacion,
                            "estado_operativo": "Operativo"
                        }, user.get("id_usuario", 1))
                        st.success(f"Equipo {codigo} registrado con éxito en la base de datos.")
                        st.rerun()

    with tab_dependencias:
        st.markdown("#### 🌳 Red de Dependencias de Producción y Flujo Minero")
        st.caption("Relaciones de proceso entre equipos de carguío, acarreo y trituración (tabla 'dependencia_equipo').")
        deps = _MEMORY_DB.get("dependencia_equipo", [])
        if deps:
            df_deps = pd.DataFrame(deps)
            st.dataframe(df_deps, use_container_width=True, hide_index=True)
        else:
            st.info("No hay dependencias registradas.")

    with tab_repuestos:
        st.markdown("#### ⚙️ Inventario de Repuestos Críticos (pieza_reposicion)")
        piezas = _MEMORY_DB.get("pieza_reposicion", [])
        if piezas:
            df_p = pd.DataFrame(piezas)
            st.dataframe(df_p[["codigo_pieza", "nombre_pieza", "cantidad_stock", "cantidad_minima", "precio_unitario", "proveedor", "ubicacion_almacen", "estado_pieza"]], use_container_width=True, hide_index=True)

    with tab_programados:
        st.markdown("#### 📅 Programación de Mantenimiento Preventivo y Predictivo")
        mants = _MEMORY_DB.get("mantenimiento_programado", [])
        if mants:
            df_m = pd.DataFrame(mants)
            st.dataframe(df_m[["id_mantenimiento", "id_equipo", "tipo_mantenimiento", "descripcion_mantenimiento", "proxima_fecha", "estado_mantenimiento", "prioridad", "responsable"]], use_container_width=True, hide_index=True)
