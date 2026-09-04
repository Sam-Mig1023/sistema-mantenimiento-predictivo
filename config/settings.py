"""
Módulo de Configuración Global del Sistema de Mantenimiento Predictivo.
Universidad Nacional de Trujillo - Escuela de Ingeniería de Sistemas (IS-402).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de Base de Datos PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "bd_mantenimiento_predictivo")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Configuración de Seguridad y JWT
JWT_SECRET = os.getenv("JWT_SECRET", "unt_is402_predictive_maint_secret_key_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TIEMPO_SESION_MINUTOS_DEFAULT = 60
INTENTOS_FALLIDOS_MAX_DEFAULT = 5

# Semilla fija para reproducibilidad matemática
RANDOM_STATE = 42

# Rutas de artefactos y almacenamiento
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_PDF_DIR = REPORTS_DIR / "pdf"
REPORTS_WORD_DIR = REPORTS_DIR / "word"
REPORTS_EXCEL_DIR = REPORTS_DIR / "excel"
ASSETS_DIR = BASE_DIR / "assets"

# Asegurar existencia de directorios
for folder in [MODELS_DIR, REPORTS_PDF_DIR, REPORTS_WORD_DIR, REPORTS_EXCEL_DIR, ASSETS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
