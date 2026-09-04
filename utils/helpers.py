"""
Módulo de Funciones Auxiliares del Sistema.
Cálculos de confiabilidad, métricas operacionales mineras, formateo y validaciones.
"""

from datetime import datetime, date
from typing import Any, Dict, Optional
import json

def format_datetime(dt: Optional[datetime]) -> str:
    """Formatea un objeto datetime a string legible en español."""
    if not dt:
        return "N/A"
    if isinstance(dt, (datetime, date)):
        return dt.strftime("%d/%m/%Y %H:%M")
    return str(dt)

def format_currency(val: Optional[float], currency: str = "USD") -> str:
    """Formatea un monto numérico a formato monetario."""
    if val is None:
        return f"$ 0.00 {currency}"
    return f"$ {val:,.2f} {currency}"

def calculate_kpis(operating_hours: float, failure_count: int, repair_hours: float) -> Dict[str, float]:
    """
    Calcula los principales indicadores de mantenimiento:
    - MTBF: Mean Time Between Failures = Horas Operación / Fallas
    - MTTR: Mean Time To Repair = Horas de Reparación / Fallas
    - Disponibilidad = MTBF / (MTBF + MTTR)
    - OEE = Disponibilidad * Rendimiento * Calidad (estimado para minería)
    """
    if failure_count <= 0:
        mtbf = operating_hours
        mttr = 0.0
        disponibilidad = 1.0
    else:
        mtbf = operating_hours / failure_count
        mttr = repair_hours / failure_count
        total_time = mtbf + mttr
        disponibilidad = mtbf / total_time if total_time > 0 else 1.0

    # Rendimiento y Calidad típicos en flota de minería a cielo abierto (92% y 98%)
    oee = disponibilidad * 0.92 * 0.98

    return {
        "mtbf_horas": round(mtbf, 2),
        "mttr_horas": round(mttr, 2),
        "disponibilidad": round(disponibilidad, 4),
        "oee": round(oee, 4)
    }

def safe_json_serialize(obj: Any) -> str:
    """Serializa un objeto de forma segura a cadena JSON."""
    def default_handler(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return str(o)
    return json.dumps(obj, default=default_handler, ensure_ascii=False)
