"""
Pruebas Unitarias para el Pipeline de Limpieza y Transformación de Sensores.
"""

import pytest
import pandas as pd
import numpy as np

def test_sensor_data_ranges_and_nulls(sample_data):
    """Verifica que no existan valores nulos críticos y los rangos de telemetría."""
    df_train = sample_data["dataset_entrenamiento"]
    assert isinstance(df_train, pd.DataFrame)
    assert df_train.isnull().sum().sum() == 0, "No deben existir valores nulos en el dataset limpio"

    assert (df_train["temperatura"] > 0).all(), "Temperatura debe ser positiva"
    assert (df_train["presion_aceite"] > 0).all(), "Presión de aceite debe ser positiva"
    assert (df_train["vibracion"] >= 0).all(), "Vibración no puede ser negativa"

def test_feature_engineering_consistency(sample_data):
    """Verifica que las variables derivadas calculadas conserven coherencia física."""
    df_train = sample_data["dataset_entrenamiento"]
    assert "rolling_temp_mean" in df_train.columns
    assert "rolling_vib_std" in df_train.columns
    assert "delta_presion" in df_train.columns

    # rolling_vib_std no puede ser negativo
    assert (df_train["rolling_vib_std"] >= 0).all()
