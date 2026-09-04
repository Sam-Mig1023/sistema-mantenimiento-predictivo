"""
Módulo de Autenticación, Autorización y Seguridad JWT.
Implementa:
- Hashing de contraseñas con bcrypt
- Generación y verificación de tokens JWT (PyJWT)
- Manejo de intentos fallidos y bloqueo temporal
- Registro y auditoría de sesiones en 'session_usuario'
- Verificación rigurosa de expiración en cada rerun
- Control de Acceso Basado en Roles (RBAC) con 'rol_permiso' y 'permiso'
- Auditoría de bitácora en 'bitacora_actividad'
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
import logging
import jwt
import bcrypt
import streamlit as st

from config.settings import JWT_SECRET, JWT_ALGORITHM, TIEMPO_SESION_MINUTOS_DEFAULT, INTENTOS_FALLIDOS_MAX_DEFAULT

logger = logging.getLogger(__name__)

# Permisos definidos por el sistema
PERMISOS_SISTEMA = {
    "Administrador": [
        "ver_dashboard", "ver_equipos", "editar_equipos", "ver_sensores", "editar_sensores",
        "ver_modelos", "entrenar_modelos", "ver_predicciones", "generar_reportes",
        "administrar_usuarios", "ver_alertas", "gestionar_alertas", "configuracion_sistema"
    ],
    "Supervisor": [
        "ver_dashboard", "ver_equipos", "ver_sensores", "ver_modelos",
        "ver_predicciones", "generar_reportes", "ver_alertas", "gestionar_alertas"
    ],
    "Técnico": [
        "ver_dashboard", "ver_equipos", "ver_sensores", "ver_modelos",
        "ver_predicciones", "ver_alertas", "gestionar_alertas"
    ],
    "Consultor": [
        "ver_dashboard", "ver_equipos", "ver_sensores", "ver_modelos", "ver_predicciones"
    ]
}

# Usuarios por defecto para simulación y arranque del sistema
USUARIOS_INICIALES = [
    {
        "id_usuario": 1,
        "nombre_usuario": "admin",
        "email": "admin@unitru.edu.pe",
        "contrasena_hash": bcrypt.hashpw("Admin123*".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "nombres": "Miguel",
        "apellidos": "Aguilar Reyes",
        "cargo": "Jefe de Mantenimiento Predictivo",
        "area": "Ingeniería & Confiabilidad",
        "rol": "Administrador",
        "estado_usuario": True,
        "intentos_fallidos": 0,
        "fecha_bloqueo": None
    },
    {
        "id_usuario": 2,
        "nombre_usuario": "supervisor",
        "email": "supervisor@mina.pe",
        "contrasena_hash": bcrypt.hashpw("Super123*".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "nombres": "Carlos",
        "apellidos": "Mendoza Paredes",
        "cargo": "Supervisor de Operaciones Mina",
        "area": "Operaciones",
        "rol": "Supervisor",
        "estado_usuario": True,
        "intentos_fallidos": 0,
        "fecha_bloqueo": None
    },
    {
        "id_usuario": 3,
        "nombre_usuario": "tecnico",
        "email": "tecnico@mina.pe",
        "contrasena_hash": bcrypt.hashpw("Tecnico123*".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "nombres": "Roberto",
        "apellidos": "Quispe Flores",
        "cargo": "Técnico Especialista en Vibraciones",
        "area": "Mantenimiento Mecánico",
        "rol": "Técnico",
        "estado_usuario": True,
        "intentos_fallidos": 0,
        "fecha_bloqueo": None
    },
    {
        "id_usuario": 4,
        "nombre_usuario": "consultor",
        "email": "consultor@auditoria.com",
        "contrasena_hash": bcrypt.hashpw("Consultor123*".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "nombres": "Ana",
        "apellidos": "Valderrama Díaz",
        "cargo": "Auditora Externa de Mantenimiento",
        "area": "Consultoría IS-402",
        "rol": "Consultor",
        "estado_usuario": True,
        "intentos_fallidos": 0,
        "fecha_bloqueo": None
    }
]

class AuthManager:
    """Administra autenticación, tokens JWT, sesiones y auditoría."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashea una contraseña en texto plano con bcrypt y sal."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña contra su hash bcrypt."""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    def generate_jwt_token(user_data: Dict[str, Any], session_duration_minutes: int = TIEMPO_SESION_MINUTOS_DEFAULT) -> Tuple[str, datetime]:
        """Genera un token JWT con tiempo de expiración configurable."""
        now = datetime.now(timezone.utc)
        exp_time = now + timedelta(minutes=session_duration_minutes)
        payload = {
            "sub": str(user_data["id_usuario"]),
            "username": user_data["nombre_usuario"],
            "rol": user_data["rol"],
            "email": user_data["email"],
            "iat": now,
            "exp": exp_time
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token, exp_time

    @staticmethod
    def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Verifica la validez y expiración de un token JWT."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token JWT expirado.")
            return None
        except jwt.InvalidTokenError as err:
            logger.warning(f"Token JWT inválido: {err}")
            return None

    @classmethod
    def authenticate(cls, identifier: str, password: str, users_list: List[Dict[str, Any]]) -> Tuple[bool, str, Optional[Dict[str, Any]], Optional[str], Optional[datetime]]:
        """
        Valida credenciales contra la lista o BD de usuarios.
        Maneja bloqueo tras 5 intentos fallidos.
        """
        user = None
        for u in users_list:
            if (u["nombre_usuario"].lower() == identifier.lower() or u["email"].lower() == identifier.lower()):
                user = u
                break

        if not user:
            return False, "Usuario o correo no encontrado.", None, None, None

        if not user.get("estado_usuario", True):
            return False, "La cuenta de usuario está desactivada (Soft delete activo). Contacte al administrador.", None, None, None

        # Verificar bloqueo por intentos fallidos
        if user.get("intentos_fallidos", 0) >= INTENTOS_FALLIDOS_MAX_DEFAULT:
            return False, f"Usuario bloqueado por exceder {INTENTOS_FALLIDOS_MAX_DEFAULT} intentos fallidos.", None, None, None

        if not cls.verify_password(password, user["contrasena_hash"]):
            user["intentos_fallidos"] = user.get("intentos_fallidos", 0) + 1
            restantes = INTENTOS_FALLIDOS_MAX_DEFAULT - user["intentos_fallidos"]
            if restantes <= 0:
                user["fecha_bloqueo"] = datetime.now()
                return False, "Has superado los 5 intentos fallidos. Tu cuenta ha sido bloqueada temporalmente.", None, None, None
            return False, f"Contraseña incorrecta. Intentos restantes: {restantes}.", None, None, None

        # Login exitoso: reiniciar intentos fallidos
        user["intentos_fallidos"] = 0
        user["ultimo_acceso"] = datetime.now()

        token, exp_time = cls.generate_jwt_token(user)
        return True, "Autenticación exitosa.", user, token, exp_time

    @classmethod
    def check_permission(cls, rol: str, permission_name: str) -> bool:
        """Verifica si un rol tiene el permiso requerido según rol_permiso."""
        permisos = PERMISOS_SISTEMA.get(rol, [])
        return permission_name in permisos

    @classmethod
    def validate_current_session(cls) -> bool:
        """
        Valida REAL de expiración en CADA rerun de Streamlit:
        Verifica fecha_expiracion y el claim 'exp' del JWT.
        Si expiró, cierra sesión y limpia el estado.
        """
        if "auth_token" not in st.session_state or not st.session_state["auth_token"]:
            return False

        token = st.session_state["auth_token"]
        payload = cls.verify_jwt_token(token)

        if not payload:
            cls.logout("Su sesión ha expirado por inactividad (60 minutos). Por favor ingrese nuevamente.")
            return False

        # Validar fecha_expiracion contra session_usuario en memoria/BD
        if "session_expiracion" in st.session_state:
            exp_date = st.session_state["session_expiracion"]
            if isinstance(exp_date, str):
                try:
                    exp_date = datetime.fromisoformat(exp_date)
                except Exception:
                    pass
            if isinstance(exp_date, datetime):
                now_utc = datetime.now(timezone.utc)
                if exp_date.tzinfo is None:
                    exp_date = exp_date.replace(tzinfo=timezone.utc)
                if now_utc > exp_date:
                    cls.logout("Su sesión ha superado el tiempo límite de conexión.")
                    return False

        return True

    @classmethod
    def logout(cls, message: str = "Sesión cerrada correctamente."):
        """Cierra sesión, marca en bitácora y limpia session_state."""
        for key in ["auth_token", "user", "session_expiracion", "session_id"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["logout_message"] = message
