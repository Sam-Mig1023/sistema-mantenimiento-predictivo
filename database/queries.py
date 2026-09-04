"""
Módulo de Queries y Operaciones CRUD Reutilizables.
Totalmente alineado con el esquema SQL de 30 tablas de 'bd_mantenimiento_predictivo'.
Implementa Soft Delete en 'equipo' y 'usuario', acceso a vistas y funciones almacenadas,
y fallback sincronizado a motor de datos sintéticos.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import json
import logging

from database.connection import get_db_manager
from utils.data_generator import SyntheticDataGenerator
from auth.authentication import USUARIOS_INICIALES

logger = logging.getLogger(__name__)

# Repositorio en memoria inicializado con semilla fija (random_state=42)
_DATA_ENGINE = SyntheticDataGenerator(seed=42)
_MEMORY_DB: Dict[str, Any] = _DATA_ENGINE.generate_all_data()
_MEMORY_DB["usuario"] = [dict(u) for u in USUARIOS_INICIALES]
_MEMORY_DB["bitacora_actividad"] = []
_MEMORY_DB["reporte_generado"] = []
_MEMORY_DB["session_usuario"] = []
_MEMORY_DB["modelo_ia"] = []
_MEMORY_DB["prediccion_falla"] = []
_MEMORY_DB["configuracion_sistema"] = [
    {"clave_configuracion": "umbral_alerta_temperatura", "valor_configuracion": "85", "tipo_dato": "numerico", "categoria_configuracion": "Alertas"},
    {"clave_configuracion": "umbral_alerta_presion", "valor_configuracion": "120", "tipo_dato": "numerico", "categoria_configuracion": "Alertas"},
    {"clave_configuracion": "umbral_alerta_vibracion", "valor_configuracion": "15", "tipo_dato": "numerico", "categoria_configuracion": "Alertas"},
    {"clave_configuracion": "frecuencia_prediccion_horas", "valor_configuracion": "24", "tipo_dato": "numerico", "categoria_configuracion": "Predicciones"},
    {"clave_configuracion": "ventana_prediccion_horas", "valor_configuracion": "72", "tipo_dato": "numerico", "categoria_configuracion": "Predicciones"},
    {"clave_configuracion": "tiempo_sesion_minutos", "valor_configuracion": "60", "tipo_dato": "numerico", "categoria_configuracion": "Seguridad"},
    {"clave_configuracion": "intentos_fallidos_max", "valor_configuracion": "5", "tipo_dato": "numerico", "categoria_configuracion": "Seguridad"},
    {"clave_configuracion": "version_actual", "valor_configuracion": "1.0.0", "tipo_dato": "texto", "categoria_configuracion": "Sistema"}
]
_MEMORY_DB["version_sistema"] = [
    {"id_version": 1, "version_actual": "1.0.0", "fecha_version": datetime.now(), "descripcion_cambios": "Versión inicial UNT IS-402", "estado_version": "Activa"}
]

def seed_initial_users():
    """Siembra los usuarios iniciales en PostgreSQL si la tabla está vacía."""
    manager = get_db_manager()
    if manager.is_connected:
        try:
            with manager.get_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM usuario;")
                        count = cur.fetchone()[0]
                        if count == 0:
                            for u in USUARIOS_INICIALES:
                                cur.execute("""
                                    INSERT INTO usuario (
                                        id_usuario, nombre_usuario, email, contrasena_hash,
                                        nombres, apellidos, cargo, area, rol, estado_usuario,
                                        intentos_fallidos, fecha_creacion
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (id_usuario) DO NOTHING;
                                """, (
                                    u["id_usuario"], u["nombre_usuario"], u["email"],
                                    u["contrasena_hash"], u.get("nombres", "Usuario"),
                                    u.get("apellidos", "Sistema"), u.get("cargo", "Operador"),
                                    u.get("area", "Mantenimiento"), u["rol"], True, 0, datetime.now()
                                ))
                            conn.commit()
                            logger.info("Usuarios iniciales sembrados en PostgreSQL correctamente.")
        except Exception as e:
            logger.warning(f"Aviso al sembrar usuarios en PostgreSQL: {e}")

seed_initial_users()


# -------------------------------------------------------------
# AUDITORÍA Y BITÁCORA
# -------------------------------------------------------------
def log_bitacora(id_usuario: Optional[int], tipo_actividad: str, modulo: str, accion: str, tabla: Optional[str] = None, registro: Optional[str] = None, datos_nuevos: Optional[Dict] = None):
    """Registra una actividad en bitacora_actividad."""
    entry = {
        "id_bitacora": len(_MEMORY_DB["bitacora_actividad"]) + 1,
        "id_usuario": id_usuario,
        "fecha_hora": datetime.now(),
        "ip_origen": "127.0.0.1",
        "tipo_actividad": tipo_actividad,
        "modulo": modulo,
        "accion_realizada": accion,
        "tabla_afectada": tabla,
        "registro_afectado": registro,
        "datos_nuevos": datos_nuevos,
        "estado_operacion": "Exitoso"
    }
    _MEMORY_DB["bitacora_actividad"].append(entry)

    manager = get_db_manager()
    if manager.is_connected:
        try:
            with manager.get_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO bitacora_actividad 
                            (id_usuario, ip_origen, tipo_actividad, modulo, accion_realizada, tabla_afectada, registro_afectado, datos_nuevos)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (id_usuario, "127.0.0.1", tipo_actividad, modulo, accion, tabla, registro, json.dumps(datos_nuevos) if datos_nuevos else None))
                        conn.commit()
        except Exception as e:
            logger.error(f"Error registrando en bitacora_actividad BD: {e}")

# -------------------------------------------------------------
# EQUIPOS (CRUD Y SOFT DELETE)
# -------------------------------------------------------------
def get_equipos(incluir_desactivados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene equipos con su tipo (equivalente a vista_equipos_completos)."""
    manager = get_db_manager()
    if manager.is_connected:
        try:
            with manager.get_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        query = "SELECT * FROM vista_equipos_completos"
                        if not incluir_desactivados:
                            query += " WHERE estado_operativo != 'Desactivado'"
                        cur.execute(query)
                        cols = [desc[0] for desc in cur.description]
                        return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error en vista_equipos_completos: {e}")

    # Fallback memoria
    tipos_map = {t["id_tipo_equipo"]: t for t in _MEMORY_DB["tipo_equipo"]}
    res = []
    for eq in _MEMORY_DB["equipo"]:
        if not incluir_desactivados and eq.get("estado_operativo") == "Desactivado":
            continue
        t_info = tipos_map.get(eq["id_tipo_equipo"], {})
        item = dict(eq)
        item["tipo_equipo"] = t_info.get("nombre_tipo", "Equipo Minero")
        item["categoria_equipo"] = t_info.get("categoria", "Carguío")
        res.append(item)
    return res

def create_equipo(data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """Crea un nuevo equipo en tabla equipo."""
    new_id = len(_MEMORY_DB["equipo"]) + 1
    record = {
        "id_equipo": new_id,
        "id_tipo_equipo": data["id_tipo_equipo"],
        "codigo_equipo": data["codigo_equipo"],
        "nombre_equipo": data["nombre_equipo"],
        "marca": data.get("marca", ""),
        "modelo": data.get("modelo", ""),
        "ano_fabricacion": data.get("ano_fabricacion", 2024),
        "numero_serie": data.get("numero_serie", f"SN-NEW-{new_id}"),
        "horas_operacion": data.get("horas_operacion", 0),
        "ubicacion_actual": data.get("ubicacion_actual", "Tajo Abierto"),
        "fecha_instalacion": data.get("fecha_instalacion", datetime.now().date()),
        "estado_operativo": data.get("estado_operativo", "Operativo")
    }
    _MEMORY_DB["equipo"].append(record)
    log_bitacora(user_id, "Inserción", "Equipos", f"Creación de equipo {record['codigo_equipo']}", "equipo", str(new_id), record)
    return record

def update_equipo(id_equipo: int, data: Dict[str, Any], user_id: int) -> bool:
    """Actualiza datos de un equipo existente."""
    for eq in _MEMORY_DB["equipo"]:
        if eq["id_equipo"] == id_equipo:
            eq.update(data)
            log_bitacora(user_id, "Actualización", "Equipos", f"Actualización de equipo {eq['codigo_equipo']}", "equipo", str(id_equipo), data)
            return True
    return False

def soft_delete_equipo(id_equipo: int, user_id: int) -> bool:
    """
    SOFT DELETE obligatorio: actualiza estado_operativo a 'Desactivado'
    (NO usa DELETE físico) para preservar integridad referencial.
    """
    for eq in _MEMORY_DB["equipo"]:
        if eq["id_equipo"] == id_equipo:
            eq["estado_operativo"] = "Desactivado"
            log_bitacora(user_id, "Eliminación", "Equipos", f"Soft delete de equipo {eq['codigo_equipo']} (Desactivado)", "equipo", str(id_equipo))
            return True
    return False

# -------------------------------------------------------------
# FUNCIONES ALMACENADAS DE BD
# -------------------------------------------------------------
def contar_fallas_equipo(id_equipo: int) -> int:
    """Función para contar fallas por equipo (contar_fallas_equipo(p_id_equipo))."""
    return sum(1 for f in _MEMORY_DB["falla"] if f["id_equipo"] == id_equipo)

def ultimo_mantenimiento_equipo(id_equipo: int) -> Optional[Dict[str, Any]]:
    """Función para obtener el último mantenimiento de un equipo."""
    mants = [m for m in _MEMORY_DB["evento_mantenimiento"] if m["id_equipo"] == id_equipo]
    if not mants:
        return None
    mants.sort(key=lambda x: x["fecha_inicio"], reverse=True)
    return mants[0]

# -------------------------------------------------------------
# SENSORES Y LECTURAS
# -------------------------------------------------------------
def get_sensores(id_equipo: Optional[int] = None) -> List[Dict[str, Any]]:
    """Obtiene sensores asociados opcionalmente por equipo."""
    if id_equipo:
        return [s for s in _MEMORY_DB["sensor"] if s["id_equipo"] == id_equipo]
    return _MEMORY_DB["sensor"]

def get_lecturas_sensor(id_sensor: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
    """Obtiene historial de lecturas recientes (vista_lecturas_recientes)."""
    lecturas = _MEMORY_DB["lectura_sensor"]
    if id_sensor:
        lecturas = [l for l in lecturas if l["id_sensor"] == id_sensor]
    return sorted(lecturas, key=lambda x: x["timestamp_lectura"], reverse=True)[:limit]

# -------------------------------------------------------------
# ALERTAS
# -------------------------------------------------------------
def get_alertas(estado: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene las alertas del sistema."""
    if estado:
        return [a for a in _MEMORY_DB["alerta"] if a["estado_alerta"] == estado]
    return sorted(_MEMORY_DB["alerta"], key=lambda x: x["fecha_generacion"], reverse=True)

def update_alerta_estado(id_alerta: int, nuevo_estado: str, usuario: str, comentarios: Optional[str] = None) -> bool:
    """Actualiza el ciclo de vida de una alerta."""
    for a in _MEMORY_DB["alerta"]:
        if a["id_alerta"] == id_alerta:
            a["estado_alerta"] = nuevo_estado
            if nuevo_estado == "Leída":
                a["fecha_lectura"] = datetime.now()
            elif nuevo_estado == "Resuelta":
                a["fecha_resolucion"] = datetime.now()
                a["usuario_resolvio"] = usuario
                a["comentarios_resolucion"] = comentarios or "Resuelto por protocolo estándar"
            return True
    return False

# -------------------------------------------------------------
# USUARIOS (CRUD Y SOFT DELETE)
# -------------------------------------------------------------
def get_usuarios(incluir_inactivos: bool = True) -> List[Dict[str, Any]]:
    """Obtiene catálogo de usuarios."""
    if not incluir_inactivos:
        return [u for u in _MEMORY_DB["usuario"] if u.get("estado_usuario", True)]
    return _MEMORY_DB["usuario"]

def create_usuario(user_data: Dict[str, Any], admin_id: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Crea un nuevo usuario en memoria y PostgreSQL, validando unicidad
    y registrando en bitácora de auditoría.
    """
    username = user_data.get("nombre_usuario", "").strip()
    email = user_data.get("email", "").strip()

    # Validar duplicados
    for u in _MEMORY_DB["usuario"]:
        if u["nombre_usuario"].lower() == username.lower():
            return False, f"El nombre de usuario '{username}' ya está registrado.", None
        if u.get("email", "").lower() == email.lower():
            return False, f"El correo institucional '{email}' ya se encuentra registrado.", None

    new_id = max([u["id_usuario"] for u in _MEMORY_DB["usuario"]], default=0) + 1
    new_u = {
        "id_usuario": new_id,
        "nombre_usuario": username,
        "email": email,
        "contrasena_hash": user_data["contrasena_hash"],
        "nombres": user_data.get("nombres", "").strip(),
        "apellidos": user_data.get("apellidos", "").strip(),
        "cargo": user_data.get("cargo", "Operador").strip(),
        "area": user_data.get("area", "Mantenimiento"),
        "rol": user_data.get("rol", "Técnico"),
        "estado_usuario": True,
        "intentos_fallidos": 0,
        "fecha_bloqueo": None,
        "fecha_creacion": datetime.now()
    }
    _MEMORY_DB["usuario"].append(new_u)

    # Persistir en PostgreSQL si está conectado
    manager = get_db_manager()
    if manager.is_connected:
        try:
            with manager.get_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO usuario (
                                id_usuario, nombre_usuario, email, contrasena_hash,
                                nombres, apellidos, cargo, area, rol, estado_usuario,
                                intentos_fallidos, fecha_creacion
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id_usuario) DO NOTHING;
                        """, (
                            new_id, username, email, new_u["contrasena_hash"],
                            new_u["nombres"], new_u["apellidos"], new_u["cargo"],
                            new_u["area"], new_u["rol"], True, 0, datetime.now()
                        ))
                        conn.commit()
        except Exception as e:
            logger.warning(f"Aviso al guardar usuario en PostgreSQL: {e}")

    log_bitacora(
        admin_id,
        "Inserción",
        "Usuarios",
        f"Creación de usuario {username} ({new_u['rol']})",
        "usuario",
        str(new_id)
    )
    return True, f"Usuario '{username}' registrado exitosamente.", new_u

def soft_delete_usuario(id_usuario: int, admin_id: int) -> bool:
    """
    SOFT DELETE obligatorio de usuarios: actualiza estado_usuario a FALSE
    (NO usa DELETE físico) para preservar integridad con bitácora y sesiones.
    """
    for u in _MEMORY_DB["usuario"]:
        if u["id_usuario"] == id_usuario:
            u["estado_usuario"] = False
            log_bitacora(admin_id, "Eliminación", "Usuarios", f"Soft delete de usuario {u['nombre_usuario']} (Desactivado)", "usuario", str(id_usuario))
            
            manager = get_db_manager()
            if manager.is_connected:
                try:
                    with manager.get_connection() as conn:
                        if conn:
                            with conn.cursor() as cur:
                                cur.execute("UPDATE usuario SET estado_usuario = FALSE WHERE id_usuario = %s;", (id_usuario,))
                                conn.commit()
                except Exception as e:
                    logger.warning(f"Aviso al actualizar soft delete en PostgreSQL: {e}")
            return True
    return False

# -------------------------------------------------------------
# REPORTES Y PREDICCIONES
# -------------------------------------------------------------
def registrar_reporte_generado(reporte_data: Dict[str, Any]) -> int:
    """Registra metadatos de un reporte generado en disco y BD."""
    rep_id = len(_MEMORY_DB["reporte_generado"]) + 1
    reporte_data["id_reporte"] = rep_id
    reporte_data["fecha_generacion"] = datetime.now()
    reporte_data["veces_descargado"] = 0
    _MEMORY_DB["reporte_generado"].append(reporte_data)

    manager = get_db_manager()
    if manager.is_connected:
        try:
            with manager.get_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO reporte_generado (
                                id_reporte, id_usuario, nombre_reporte, tipo_reporte,
                                formato_archivo, ruta_archivo, tamano_bytes,
                                fecha_generacion, veces_descargado, estado_reporte
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id_reporte) DO NOTHING;
                        """, (
                            rep_id,
                            reporte_data.get("id_usuario_genero", 1),
                            reporte_data.get("nombre_reporte", "Reporte"),
                            reporte_data.get("tipo_reporte", "General"),
                            reporte_data.get("formato", "pdf"),
                            reporte_data.get("ruta_archivo", ""),
                            reporte_data.get("tamano_bytes", 0),
                            datetime.now(),
                            0,
                            "Generado"
                        ))
                        conn.commit()
        except Exception as e:
            logger.warning(f"Aviso al guardar reporte_generado en PostgreSQL: {e}")
    return rep_id

def registrar_prediccion(pred_data: Dict[str, Any]) -> int:
    """Registra una inferencia en tabla prediccion_falla."""
    pred_id = len(_MEMORY_DB["prediccion_falla"]) + 1
    pred_data["id_prediccion"] = pred_id
    pred_data["fecha_prediccion"] = datetime.now()
    _MEMORY_DB["prediccion_falla"].append(pred_data)
    return pred_id
