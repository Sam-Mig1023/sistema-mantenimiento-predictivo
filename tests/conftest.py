"""
Configuración de Fixtures para Pruebas Unitarias con pytest.
Sistema de Mantenimiento Predictivo (UNT IS-402).
"""

import pytest
from datetime import datetime, timedelta
from utils.data_generator import SyntheticDataGenerator
from modules.ia_engine import PredictiveMaintenanceAIEngine

@pytest.fixture(scope="session")
def sample_data():
    """Fixture que provee datos sintéticos consistentes para pruebas."""
    gen = SyntheticDataGenerator(seed=42)
    return gen.generate_all_data()

@pytest.fixture(scope="session")
def ai_engine():
    """Fixture del motor de Inteligencia Artificial."""
    return PredictiveMaintenanceAIEngine(seed=42)
