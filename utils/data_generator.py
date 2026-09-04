"""
Generador de Datos Sintéticos Realistas para el Sistema de Mantenimiento Predictivo.
Contexto: Minería peruana (Antamina, Yanacocha, Cerro Verde, Las Bambas).
Garantiza reproducibilidad absoluta con semilla fija (random_state=42).
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np
import pandas as pd

from config.settings import RANDOM_STATE

class SyntheticDataGenerator:
    """Genera datos sintéticos para todas las tablas core de la BD."""

    def __init__(self, seed: int = RANDOM_STATE):
        self.seed = seed
        random.seed(self.seed)
        np.random.seed(self.seed)

    def generate_all_data(self) -> Dict[str, Any]:
        """Genera el conjunto de datos completo y consistente."""
        tipos_equipo = self._generate_tipos_equipo()
        equipos = self._generate_equipos(tipos_equipo)
        sensores = self._generate_sensores(equipos)
        parametros_referencia = self._generate_parametros_referencia(sensores)
        lecturas_sensor = self._generate_lecturas_sensor(sensores, total_records=10000)
        eventos = self._generate_eventos_mantenimiento(equipos)
        fallas = self._generate_fallas(equipos, eventos)
        alertas = self._generate_alertas(equipos, sensores, fallas)
        kpis = self._generate_kpis(equipos)
        piezas = self._generate_piezas_reposicion(tipos_equipo)
        usos_piezas = self._generate_usos_piezas(eventos, piezas)
        mantenimientos_prog = self._generate_mantenimientos_programados(equipos)
        dependencias = self._generate_dependencias(equipos)
        training_data = self._generate_training_dataset(lecturas_sensor)

        return {
            "tipo_equipo": tipos_equipo,
            "equipo": equipos,
            "sensor": sensores,
            "parametro_referencia_sensor": parametros_referencia,
            "lectura_sensor": lecturas_sensor,
            "evento_mantenimiento": eventos,
            "falla": fallas,
            "alerta": alertas,
            "kpi_equipo": kpis,
            "pieza_reposicion": piezas,
            "uso_pieza_mantenimiento": usos_piezas,
            "mantenimiento_programado": mantenimientos_prog,
            "dependencia_equipo": dependencias,
            "dataset_entrenamiento": training_data
        }

    def _generate_tipos_equipo(self) -> List[Dict[str, Any]]:
        return [
            {"id_tipo_equipo": 1, "nombre_tipo": "Excavadora", "descripcion": "Excavadora hidráulica minera", "categoria": "Carguío", "estado": True},
            {"id_tipo_equipo": 2, "nombre_tipo": "Camión Minero", "descripcion": "Camión de acarreo de alto tonelaje", "categoria": "Transporte", "estado": True},
            {"id_tipo_equipo": 3, "nombre_tipo": "Perforadora", "descripcion": "Perforadora rotativa sobre orugas", "categoria": "Perforación", "estado": True},
            {"id_tipo_equipo": 4, "nombre_tipo": "Cargador Frontal", "descripcion": "Cargador de ruedas para material volado", "categoria": "Carguío", "estado": True},
            {"id_tipo_equipo": 5, "nombre_tipo": "Tractor", "descripcion": "Tractor de orugas para desmonte", "categoria": "Transporte", "estado": True}
        ]

    def _generate_equipos(self, tipos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        marcas_modelos = {
            1: [("Komatsu", "PC8000-11"), ("Caterpillar", "6060"), ("Hitachi", "EX5600-7")],
            2: [("Caterpillar", "797F"), ("Komatsu", "930E-5"), ("Liebherr", "T 284")],
            3: [("Epiroc", "Pit Viper 351"), ("Sandvik", "DR412i"), ("Caterpillar", "MD6310")],
            4: [("Caterpillar", "994K"), ("Komatsu", "WA900-8")],
            5: [("Caterpillar", "D11T"), ("Komatsu", "D475A-8")]
        }

        equipos = []
        eq_id = 1
        ubicaciones = ["Tajo Abierto Fase 4", "Tajo Abierto Fase 5", "Botadero Norte", "Planta Chancado", "Taller Central Mina"]

        for id_tipo in range(1, 6):
            pairs = marcas_modelos[id_tipo]
            for i, (marca, modelo) in enumerate(pairs):
                # Estados: Operativo, Mantenimiento, Fallado
                estado = "Operativo"
                if eq_id in [4, 9]:
                    estado = "Mantenimiento"
                elif eq_id == 7:
                    estado = "Fallado"

                equipos.append({
                    "id_equipo": eq_id,
                    "id_tipo_equipo": id_tipo,
                    "codigo_equipo": f"EQ-MIN-{eq_id:03d}",
                    "nombre_equipo": f"{tipos[id_tipo-1]['nombre_tipo']} {marca} {modelo}",
                    "marca": marca,
                    "modelo": modelo,
                    "ano_fabricacion": 2018 + (eq_id % 6),
                    "numero_serie": f"SN-{marca[:3].upper()}-{20000+eq_id*113}",
                    "horas_operacion": 12000 + (eq_id * 1450),
                    "ubicacion_actual": random.choice(ubicaciones),
                    "fecha_instalacion": (datetime.now() - timedelta(days=1200 + eq_id * 30)).date(),
                    "estado_operativo": estado
                })
                eq_id += 1

        return equipos

    def _generate_sensores(self, equipos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sensores = []
        s_id = 1
        plantillas = [
            ("Temperatura Motor", "Temperatura", "°C", 40.0, 115.0, 30, "Bloque de Motor"),
            ("Presión Aceite Motor", "Presión", "bar", 1.5, 7.5, 30, "Línea Principal de Lubricación"),
            ("Vibración Rodamientos", "Vibración", "mm/s", 0.5, 25.0, 10, "Eje de Transmisión"),
            ("Velocidad Giro RPM", "RPM", "rpm", 600.0, 2400.0, 15, "Cigüeñal"),
            ("Temperatura Aceite Hidráulico", "Temperatura", "°C", 35.0, 95.0, 30, "Tanque Hidráulico")
        ]

        for eq in equipos:
            for p_nombre, p_tipo, p_unid, r_min, r_max, freq, ubic in plantillas:
                sensores.append({
                    "id_sensor": s_id,
                    "id_equipo": eq["id_equipo"],
                    "codigo_sensor": f"SENS-{eq['id_equipo']:02d}-{s_id:03d}",
                    "nombre_sensor": f"{p_nombre} ({eq['codigo_equipo']})",
                    "tipo_sensor": p_tipo,
                    "unidad_medida": p_unid,
                    "rango_minimo": r_min,
                    "rango_maximo": r_max,
                    "frecuencia_muestreo": freq,
                    "ubicacion_instalacion": ubic,
                    "estado": True
                })
                s_id += 1
        return sensores

    def _generate_parametros_referencia(self, sensores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        params = []
        p_id = 1
        for s in sensores:
            tipo = s["tipo_sensor"]
            if tipo == "Temperatura":
                val_min, val_max, crit_min, crit_max = 65.0, 85.0, 50.0, 100.0
            elif tipo == "Presión":
                val_min, val_max, crit_min, crit_max = 3.0, 6.0, 2.0, 7.0
            elif tipo == "Vibración":
                val_min, val_max, crit_min, crit_max = 2.0, 8.0, 1.0, 15.0
            else: # RPM
                val_min, val_max, crit_min, crit_max = 800.0, 1800.0, 600.0, 2100.0

            params.append({
                "id_parametro": p_id,
                "id_sensor": s["id_sensor"],
                "condicion_operacion": "Normal",
                "valor_esperado_min": val_min,
                "valor_esperado_max": val_max,
                "desviacion_permitida": 0.10,
                "umbral_critico_min": crit_min,
                "umbral_critico_max": crit_max,
                "establecido_por": 1
            })
            p_id += 1
        return params

    def _generate_lecturas_sensor(self, sensores: List[Dict[str, Any]], total_records: int = 10000) -> List[Dict[str, Any]]:
        lecturas = []
        now = datetime.now()
        readings_per_sensor = max(15, total_records // len(sensores))
        lectura_id = 1

        for s in sensores:
            tipo = s["tipo_sensor"]
            r_min = float(s["rango_minimo"])
            r_max = float(s["rango_maximo"])
            media = (r_min + r_max) / 2.0
            std = (r_max - r_min) / 8.0

            for i in range(readings_per_sensor):
                # Generar timestamp en los últimos 90 días ordenados cronológicamente
                delta_minutes = (readings_per_sensor - i) * 60
                ts = now - timedelta(minutes=delta_minutes)

                # Generar anomalía ocasional (5% de las veces)
                is_anomaly = random.random() < 0.05
                if is_anomaly:
                    val = media + std * random.choice([3.2, 4.0, -3.5])
                    calidad = "Dudoso" if random.random() < 0.7 else "Inválido"
                else:
                    val = np.random.normal(media, std)
                    calidad = "Válido"

                val = max(r_min, min(r_max * 1.1, val))
                norm_val = (val - r_min) / (r_max - r_min) if r_max > r_min else 0.5

                lecturas.append({
                    "id_lectura": lectura_id,
                    "id_sensor": s["id_sensor"],
                    "valor_medido": round(float(val), 2),
                    "valor_normalizado": round(float(norm_val), 4),
                    "timestamp_lectura": ts,
                    "calidad_dato": calidad
                })
                lectura_id += 1
                if len(lecturas) >= total_records:
                    break
            if len(lecturas) >= total_records:
                break

        return lecturas

    def _generate_eventos_mantenimiento(self, equipos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        eventos = []
        tipos = ["Preventivo", "Predictivo", "Correctivo", "Emergencia"]
        estados = ["Completado", "Completado", "EnProgreso", "Planificado"]
        responsables = ["Ing. Carlos Mendoza", "Ing. Roberto Quispe", "Téc. Manuel Huamán", "Téc. Jorge Silva"]
        now = datetime.now()

        for ev_id in range(1, 56):
            eq = random.choice(equipos)
            tipo = random.choice(tipos)
            estado = random.choice(estados)
            duracion = random.randint(120, 1440)
            costo_est = random.uniform(1500, 25000)
            costo_real = costo_est * random.uniform(0.9, 1.25) if estado == "Completado" else None
            inicio = now - timedelta(days=random.randint(1, 90))
            fin = inicio + timedelta(minutes=duracion) if estado == "Completado" else None

            eventos.append({
                "id_evento": ev_id,
                "id_equipo": eq["id_equipo"],
                "tipo_evento": tipo,
                "descripcion_evento": f"Servicio {tipo} del sistema principal de {eq['nombre_equipo']}",
                "fecha_inicio": inicio,
                "fecha_fin": fin,
                "duracion_minutos": duracion if estado == "Completado" else None,
                "costo_estimado": round(costo_est, 2),
                "costo_real": round(costo_real, 2) if costo_real else None,
                "estado_evento": estado,
                "prioridad": random.choice(["Alta", "Media", "Baja"]),
                "responsable": random.choice(responsables)
            })
        return eventos

    def _generate_fallas(self, equipos: List[Dict[str, Any]], eventos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        fallas = []
        tipos_falla = ["Mecánica", "Eléctrica", "Hidráulica", "Estructural", "Software"]
        severidades = ["Critica", "Alta", "Media", "Baja"]
        estados = ["Resuelta", "Resuelta", "EnReparacion", "Reportada"]
        now = datetime.now()

        for f_id in range(1, 35):
            eq = random.choice(equipos)
            ev = random.choice(eventos)
            tipo_f = random.choice(tipos_falla)
            det = now - timedelta(days=random.randint(2, 90))
            fal = det + timedelta(minutes=random.randint(30, 240))
            estado = random.choice(estados)

            fallas.append({
                "id_falla": f_id,
                "id_equipo": eq["id_equipo"],
                "id_evento_mantenimiento": ev["id_evento"],
                "fecha_deteccion": det,
                "fecha_falla": fal,
                "tipo_falla": tipo_f,
                "severidad": random.choice(severidades),
                "descripcion_falla": f"Falla {tipo_f} reportada en subsistema motriz / hidráulico",
                "causa_raiz": "Fatiga de material por sobrecarga de mineral y vibración armónica",
                "solucion_aplicada": "Reemplazo de rodamientos, purga hidráulica y calibración de torque",
                "tiempo_inactividad_minutos": random.randint(90, 720),
                "costo_reparacion": round(random.uniform(2000, 35000), 2),
                "estado_falla": estado
            })
        return fallas

    def _generate_alertas(self, equipos: List[Dict[str, Any]], sensores: List[Dict[str, Any]], fallas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        alertas = []
        tipos = ["Umbral", "Tendencia", "Anomalía", "Predictivo"]
        gravedades = ["Información", "Advertencia", "Crítico", "Emergencia"]
        estados = ["Resuelta", "EnProceso", "Leída", "Generada"]
        now = datetime.now()

        for a_id in range(1, 105):
            eq = random.choice(equipos)
            s = random.choice(sensores)
            grav = random.choice(gravedades)
            estado = "Generada" if a_id > 85 else random.choice(estados)
            f_gen = now - timedelta(hours=random.randint(1, 240))

            alertas.append({
                "id_alerta": a_id,
                "id_equipo": eq["id_equipo"],
                "id_sensor": s["id_sensor"],
                "id_falla": random.choice(fallas)["id_falla"] if random.random() < 0.3 else None,
                "tipo_alerta": random.choice(tipos),
                "mensaje_alerta": f"Anomalía detectada en {s['nombre_sensor']}: valor excede umbral nominal.",
                "nivel_gravedad": grav,
                "fecha_generacion": f_gen,
                "fecha_lectura": f_gen + timedelta(minutes=15) if estado != "Generada" else None,
                "fecha_resolucion": f_gen + timedelta(hours=3) if estado == "Resuelta" else None,
                "estado_alerta": estado,
                "usuario_resolvio": "Ing. Carlos Mendoza" if estado == "Resuelta" else None,
                "comentarios_resolucion": "Equipo inspeccionado y parámetros recalibrados" if estado == "Resuelta" else None
            })
        return alertas

    def _generate_kpis(self, equipos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        kpis = []
        k_id = 1
        for eq in equipos:
            disponibilidad = round(random.uniform(0.82, 0.95), 4)
            utilizacion = round(random.uniform(0.75, 0.90), 4)
            mtbf = round(random.uniform(180, 450), 2)
            mttr = round(random.uniform(8, 22), 2)
            oee = round(disponibilidad * utilizacion * 0.96, 4)

            kpis.append({
                "id_kpi": k_id,
                "id_equipo": eq["id_equipo"],
                "periodo": "Mensual",
                "ano_periodo": 2026,
                "mes_periodo": 9,
                "semana_periodo": 36,
                "disponibilidad": disponibilidad,
                "utilizacion": utilizacion,
                "mtbf_horas": mtbf,
                "mttr_horas": mttr,
                "confiabilidad": round(random.uniform(0.85, 0.96), 4),
                "mantenibilidad": round(random.uniform(0.80, 0.94), 4),
                "numero_fallas": random.randint(1, 4),
                "horas_operacion": random.randint(550, 700),
                "horas_parada": random.randint(20, 80),
                "costo_mantenimiento": round(random.uniform(5000, 30000), 2),
                "produccion_estimada": round(random.uniform(80000, 250000), 2),
                "oee": oee,
                "fecha_calculo": datetime.now()
            })
            k_id += 1
        return kpis

    def _generate_piezas_reposicion(self, tipos_equipo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        piezas_raw = [
            ("PZ-ROD-01", "Rodamiento de Rodillos Cónicos SKF", 25, 5, 850.0, "SKF Perú", "Almacén Central Estante A-12"),
            ("PZ-FIL-02", "Filtro Hidráulico Principal Donaldson", 48, 12, 220.0, "Donaldson Corp", "Almacén Central Estante B-04"),
            ("PZ-BOM-03", "Bomba de Engrase Automático Lincoln", 8, 2, 3400.0, "Lincoln Industrial", "Almacén Mecánico E-01"),
            ("PZ-RET-04", "Juego de Retenes y Sellos O-Ring Viton", 60, 15, 140.0, "Parker Hannifin", "Almacén Central Gaveta 22"),
            ("PZ-MANG-05", "Manguera Hidráulica Alta Presión 5000 PSI", 35, 10, 380.0, "Gates Sudamericana", "Almacén Central Estante C-08"),
            ("PZ-DISC-06", "Disco de Freno Húmedo Enfriado por Aceite", 14, 4, 2100.0, "Caterpillar Logistics", "Taller Frenos B-02"),
            ("PZ-SEN-07", "Sensor de Presión Piezorresistivo 0-250 bar", 18, 6, 650.0, "Bosch Rexroth", "Laboratorio Instrumentación"),
            ("PZ-CORR-08", "Faja de Transmisión Dentada Poly-V", 40, 8, 195.0, "Optibelt", "Almacén Central Estante D-03")
        ]
        piezas = []
        for idx, (cod, nom, stock, min_st, precio, prov, ubic) in enumerate(piezas_raw, start=1):
            piezas.append({
                "id_pieza": idx,
                "codigo_pieza": cod,
                "nombre_pieza": nom,
                "descripcion_pieza": f"Componente original para mantenimiento de flota pesada",
                "id_tipo_equipo": (idx % 5) + 1,
                "cantidad_stock": stock,
                "cantidad_minima": min_st,
                "precio_unitario": precio,
                "proveedor": prov,
                "tiempo_entrega_dias": random.randint(3, 15),
                "ubicacion_almacen": ubic,
                "estado_pieza": "Activo"
            })
        return piezas

    def _generate_usos_piezas(self, eventos: List[Dict[str, Any]], piezas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        usos = []
        u_id = 1
        for ev in eventos[:30]:
            p = random.choice(piezas)
            cant = random.randint(1, 4)
            usos.append({
                "id_uso": u_id,
                "id_evento_mantenimiento": ev["id_evento"],
                "id_pieza": p["id_pieza"],
                "cantidad_usada": cant,
                "costo_unitario": p["precio_unitario"],
                "fecha_uso": ev["fecha_inicio"]
            })
            u_id += 1
        return usos

    def _generate_mantenimientos_programados(self, equipos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        progs = []
        now = datetime.now().date()
        for idx, eq in enumerate(equipos, start=1):
            proxima = now + timedelta(days=random.randint(5, 30))
            progs.append({
                "id_mantenimiento": idx,
                "id_equipo": eq["id_equipo"],
                "tipo_mantenimiento": "Preventivo 500H" if idx % 2 == 0 else "Predictivo Vibraciones",
                "descripcion_mantenimiento": f"Mantenimiento programado de rutina para {eq['codigo_equipo']}",
                "frecuencia_dias": 30,
                "proxima_fecha": proxima,
                "ultima_ejecucion": proxima - timedelta(days=30),
                "horas_programadas": 8,
                "estado_mantenimiento": "Programado",
                "prioridad": "Media",
                "responsable": "Ing. Roberto Quispe",
                "notas": "Revisar muestra de aceite para análisis espectrométrico de metales de desgaste."
            })
        return progs

    def _generate_dependencias(self, equipos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Ej: Camiones alimentan chancadora o dependen de excavadoras
        deps = []
        dep_id = 1
        # Excavadoras (IDs 1, 2, 3) alimentan Camiones (IDs 4, 5, 6)
        relaciones = [
            (1, 4, "Alimenta", "Excavadora 01 carga material a Camión 01"),
            (1, 5, "Alimenta", "Excavadora 01 carga material a Camión 02"),
            (2, 6, "Alimenta", "Excavadora 02 carga material a Camión 03"),
            (7, 1, "Controla", "Perforadora 01 delimita frente para Excavadora 01")
        ]
        for padre, hijo, tipo_rel, desc in relaciones:
            deps.append({
                "id_dependencia": dep_id,
                "id_equipo_padre": padre,
                "id_equipo_hijo": hijo,
                "tipo_relacion": tipo_rel,
                "descripcion_relacion": desc,
                "fecha_establecimiento": datetime.now().date() - timedelta(days=300),
                "estado_relacion": "Activa"
            })
            dep_id += 1
        return deps

    def _generate_training_dataset(self, lecturas: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Genera el DataFrame con variables predictivas e ingeniería de características:
        - Temperatura, Presión, Vibración, RPM, Horas Operación, Delta Temperatura,
          Rolling Std Vibración, Tasa Degradación, etc.
        - Variable objetivo: falla_inminente (0 = No Falla, 1 = Falla en 72h).
        """
        n_samples = 2500
        # Simulación de telemetría de carguío minero
        np.random.seed(self.seed)

        temp = np.clip(np.random.normal(82.0, 10.5, n_samples), a_min=15.0, a_max=None)
        presion = np.clip(np.random.normal(4.8, 1.1, n_samples), a_min=0.5, a_max=None)
        vibracion = np.clip(np.random.normal(5.5, 2.4, n_samples), a_min=0.1, a_max=None)
        rpm = np.clip(np.random.normal(1650, 220, n_samples), a_min=500.0, a_max=None)
        horas_op = np.random.uniform(5000, 28000, n_samples)
        aceite_viscosidad = np.random.normal(46.0, 6.0, n_samples)
        consumo_combustible = np.random.normal(120.0, 18.0, n_samples)
        flujo_hidraulico = np.random.normal(320.0, 35.0, n_samples)

        # Variables de ingeniería de características (ventanas y degradación)
        rolling_temp_mean = temp + np.random.normal(0, 1.2, n_samples)
        rolling_vib_std = np.abs(vibracion * 0.25 + np.random.normal(0.4, 0.2, n_samples))
        delta_presion = np.random.normal(0.05, 0.35, n_samples)

        # Regla física de falla en minería: sobretemperatura + alta vibración o caída súbita de presión
        score_falla = (
            (temp - 82.0) / 10.5 * 0.35 +
            (vibracion - 5.5) / 2.4 * 0.45 -
            (presion - 4.8) / 1.1 * 0.30 +
            (horas_op / 28000.0) * 0.25 +
            np.random.normal(0, 0.4, n_samples)
        )

        prob_falla = 1.0 / (1.0 + np.exp(-score_falla))
        falla_inminente = (prob_falla > 0.72).astype(int)

        df = pd.DataFrame({
            "temperatura": np.round(temp, 2),
            "presion_aceite": np.round(presion, 2),
            "vibracion": np.round(vibracion, 2),
            "rpm": np.round(rpm, 1),
            "horas_operacion": np.round(horas_op, 0).astype(int),
            "viscosidad_aceite": np.round(aceite_viscosidad, 2),
            "consumo_combustible": np.round(consumo_combustible, 1),
            "flujo_hidraulico": np.round(flujo_hidraulico, 1),
            "rolling_temp_mean": np.round(rolling_temp_mean, 2),
            "rolling_vib_std": np.round(rolling_vib_std, 3),
            "delta_presion": np.round(delta_presion, 3),
            "falla_inminente": falla_inminente
        })

        return df
