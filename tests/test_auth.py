"""
Pruebas Unitarias para el Módulo de Autenticación y JWT (auth/authentication.py).
Cubre:
- Login exitoso con credenciales válidas
- Fallo de login con contraseña incorrecta
- Bloqueo de cuenta tras 5 intentos fallidos consecutivos
- Validación y detección de expiración de token JWT
"""

import pytest
import time
from auth.authentication import AuthManager, USUARIOS_INICIALES

def test_login_credenciales_validas():
    users_copy = [dict(u) for u in USUARIOS_INICIALES]
    success, msg, user, token, exp = AuthManager.authenticate("admin", "Admin123*", users_copy)
    assert success is True
    assert user is not None
    assert user["nombre_usuario"] == "admin"
    assert token is not None
    assert user["intentos_fallidos"] == 0

def test_login_contrasena_incorrecta():
    users_copy = [dict(u) for u in USUARIOS_INICIALES]
    success, msg, user, token, exp = AuthManager.authenticate("admin", "ContrasenaEquivocada", users_copy)
    assert success is False
    assert user is None
    assert token is None
    # Verifica incremento de contador
    assert "incorrecta" in msg.lower()

def test_bloqueo_tras_5_intentos_fallidos():
    users_copy = [dict(u) for u in USUARIOS_INICIALES]
    # Ejecutar 5 intentos erróneos
    for i in range(5):
        success, msg, _, _, _ = AuthManager.authenticate("admin", f"Erroneo_{i}", users_copy)

    # El 6to intento debe indicar que la cuenta está bloqueada
    success, msg, _, _, _ = AuthManager.authenticate("admin", "Admin123*", users_copy)
    assert success is False
    assert "bloqueado" in msg.lower()

def test_expiracion_token_jwt():
    user = {"id_usuario": 1, "nombre_usuario": "admin", "rol": "Administrador", "email": "admin@unitru.edu.pe"}
    # Generar token con duración de 0 minutos (expirado inmediatamente)
    token, _ = AuthManager.generate_jwt_token(user, session_duration_minutes=0)
    time.sleep(1)
    payload = AuthManager.verify_jwt_token(token)
    assert payload is None, "El token JWT con duración 0 debe fallar la verificación por expiración"
