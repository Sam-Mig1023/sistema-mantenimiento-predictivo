"""
Pruebas Unitarias para el Módulo de Inferencia Predictiva.
Cubre:
- Inferencia con modelo entrenado
- Tiempo de respuesta menor a 1 segundo (< 1000 ms)
- Registro correcto en la tabla prediccion_falla
"""

import pytest
import time
from database.queries import _MEMORY_DB

def test_inference_time_under_one_second(ai_engine):
    """Verifica que el tiempo de inferencia sea estrictamente menor a 1 segundo."""
    sensor_input = {
        "temperatura": 85.5,
        "presion_aceite": 4.5,
        "vibracion": 6.8,
        "rpm": 1750.0,
        "horas_operacion": 16000.0,
        "rolling_vib_std": 0.85,
        "delta_presion": -0.3
    }

    t_start = time.time()
    result = ai_engine.predict_equipment_failure(id_equipo=1, sensor_values=sensor_input)
    t_elapsed = time.time() - t_start

    assert t_elapsed < 1.0, f"El tiempo de inferencia ({t_elapsed:.4f}s) debe ser menor a 1 segundo"
    assert "probabilidad_falla" in result
    assert 0.0 <= result["probabilidad_falla"] <= 1.0
    assert result["nivel_riesgo"] in ["Bajo", "Medio", "Alto", "Crítico"]

def test_prediction_saved_in_database(ai_engine):
    """Verifica que cada predicción quede registrada en la tabla prediccion_falla."""
    initial_count = len(_MEMORY_DB["prediccion_falla"])

    sensor_input = {
        "temperatura": 95.0,
        "presion_aceite": 2.2,
        "vibracion": 12.5, # Alta probabilidad de falla
        "rpm": 1800.0,
        "horas_operacion": 22000.0,
        "rolling_vib_std": 2.1,
        "delta_presion": -0.8
    }

    res = ai_engine.predict_equipment_failure(id_equipo=2, sensor_values=sensor_input)
    assert len(_MEMORY_DB["prediccion_falla"]) == initial_count + 1

    last_pred = _MEMORY_DB["prediccion_falla"][-1]
    assert last_pred["id_equipo"] == 2
    assert last_pred["nivel_riesgo"] in ["Alto", "Crítico"]
    assert "id_prediccion" in res
