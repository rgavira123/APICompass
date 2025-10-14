from dataclasses import dataclass
from typing import List, Optional, Tuple
from APICompass.ancillary.time_unit import TimeDuration
from APICompass.basic.bounded_rate import BoundedRate, Rate, Quota
from APICompass.basic.plan_and_demand import Plan
from APICompass.utils import parse_time_string_to_duration
import sympy as sp


import sympy as sp
from dataclasses import dataclass
from typing import List, Tuple, Optional, Union

@dataclass
class AnalysisResult:
    """
    Almacena todos los resultados calculados del análisis de un Plan.
    Es una estructura de datos limpia que reemplaza el diccionario.
    """
    # Puntos de las curvas
    raw_load_points: List[Tuple["TimeDuration", float]]
    raw_discharge_points: List[Tuple["TimeDuration", float]]
    normalized_load_points: List[Tuple[float, float]]
    normalized_discharge_points: List[Tuple[float, float]]

    # Puntos de corte
    raw_intersection_point: Optional[Tuple["TimeDuration", float]]
    normalized_intersection_point: Optional[Tuple[float, float]]
    
    # Intervalos de meseta
    raw_plateau_interval: Optional[Tuple[Tuple["TimeDuration", float], Tuple["TimeDuration", float]]]
    normalized_plateau_interval: Optional[Tuple[Tuple[float, float], Tuple[float, float]]]

    # Metadatos
    quota_value: float
    quota_period: "TimeDuration"
    exhaustion_threshold: Optional["TimeDuration"]
    case: str


def generate_points_for_curves(plan: "Plan") -> AnalysisResult:
    """
    Genera curvas de carga, descarga y metadatos para un plan,
    detectando automáticamente caso normal / evenly / unreachable / immediate.
    """

    thresholds = plan.quota_exhaustion_thresholds()
    threshold_td = None
    exhaustion_threshold_s = None
    case = "normal"

    # 1️⃣ Varias cuotas → tomar la más restrictiva (la de menor periodo)
    if isinstance(thresholds, (list, tuple)) and len(thresholds) > 0:
        thresholds_td = [parse_time_string_to_duration(t) for t in thresholds]
        threshold_td = min(thresholds_td, key=lambda d: d.to_seconds())
        exhaustion_threshold_s = threshold_td.to_seconds()
    # 2️⃣ Cadena simple
    elif isinstance(thresholds, str) and thresholds != "":
        threshold_td = parse_time_string_to_duration(thresholds)
        exhaustion_threshold_s = threshold_td.to_seconds()
    # 3️⃣ Sin thresholds
    else:
        threshold_td = None
        exhaustion_threshold_s = None

    # Datos base del plan
    rate_value = plan.bounded_rate.rate.consumption_unit
    quota_obj = plan.bounded_rate.quota[0]
    quota_value = quota_obj.consumption_unit
    quota_period = quota_obj.consumption_period
    quota_period_s = quota_period.to_seconds()

    def to_td(seconds: float) -> "TimeDuration":
        val = quota_period.unit.seconds_to_time_unit(seconds)
        return TimeDuration(val, quota_period.unit)

    # ---------------------------------------------------------
    # CASOS ESPECIALES
    # ---------------------------------------------------------
    if exhaustion_threshold_s is None and plan.capacity_at(quota_period) < quota_value:
        # --- UNREACHABLE ---
        cap = plan.capacity_at(quota_period)
        carga_raw = [(TimeDuration(0, quota_period.unit), rate_value),
                     (quota_period, cap)]
        descarga_raw = [(TimeDuration(0, quota_period.unit), quota_value),
                        (quota_period, rate_value)]
        case = "unreachable"
        punto_corte_norm = (0.05, cap / quota_value)  # sólo referencia visual, no real
        punto_corte_raw = (to_td(quota_period_s * 0.05), cap)
        intervalo_norm = None
        intervalo_raw = None

    elif abs(plan.capacity_during(quota_period) - quota_value) < 1e-6:
        # --- EVENLY DISTRIBUTED ---
        carga_raw = [(TimeDuration(0, quota_period.unit), rate_value),
                     (quota_period, quota_value)]
        descarga_raw = [(TimeDuration(0, quota_period.unit), quota_value),
                        (quota_period, rate_value)]
        case = "evenly"

        # Corte en el punto central ideal
        punto_corte_norm = (0.5, 0.5)
        punto_corte_raw = (to_td(quota_period_s / 2), quota_value / 2)
        intervalo_norm = None
        intervalo_raw = None

    elif threshold_td and threshold_td.to_seconds() == 0:
        # --- IMMEDIATE ---
        carga_raw = [(TimeDuration(0, quota_period.unit), rate_value),
                     (TimeDuration(0, quota_period.unit), quota_value),
                     (quota_period, quota_value)]
        descarga_raw = [(TimeDuration(0, quota_period.unit), quota_value),
                        (quota_period, quota_value)]
        case = "immediate"
        punto_corte_norm = (0.0, 1.0)
        punto_corte_raw = (to_td(0), quota_value)
        intervalo_norm = None
        intervalo_raw = None

    else:
        # --- Caso normal ---
        case = "normal"
        carga_raw = [(TimeDuration(0, quota_period.unit), rate_value),
                     (to_td(exhaustion_threshold_s), quota_value),
                     (quota_period, quota_value)]
        descarga_raw = [(TimeDuration(0, quota_period.unit), quota_value),
                        (to_td(quota_period_s - exhaustion_threshold_s), quota_value),
                        (quota_period, rate_value)]

        # Calcular corte
        def normalize(points):
            return [(p[0].to_seconds() / quota_period_s, p[1] / quota_value) for p in points]

        carga_norm = normalize(carga_raw)
        descarga_norm = normalize(descarga_raw)
        (xa1, ya1), (xa2, ya2) = carga_norm[0], carga_norm[1]
        (xr1, yr1), (xr2, yr2) = descarga_norm[1], descarga_norm[2]

        x = sp.Symbol('x')
        f_azul = (ya2 - ya1) / (xa2 - xa1) * (x - xa1) + ya1
        f_roja = (yr2 - yr1) / (xr2 - xr1) * (x - xr1) + yr1
        sol = sp.solve(sp.Eq(f_azul, f_roja), x)

        if sol:
            x_cut = float(sol[0])
            y_cut = float(f_azul.subs(x, x_cut))
            punto_corte_norm = (x_cut, y_cut)
            punto_corte_raw = (to_td(x_cut * quota_period_s), y_cut * quota_value)
        else:
            punto_corte_norm = None
            punto_corte_raw = None
        intervalo_norm = None
        intervalo_raw = None

    # Normalización (si no existen todavía)
    def normalize(points):
        return [(p[0].to_seconds() / quota_period_s, p[1] / quota_value) for p in points]

    carga_norm = normalize(carga_raw)
    descarga_norm = normalize(descarga_raw)

    return AnalysisResult(
        raw_load_points=carga_raw,
        raw_discharge_points=descarga_raw,
        normalized_load_points=carga_norm,
        normalized_discharge_points=descarga_norm,
        raw_intersection_point=punto_corte_raw,
        normalized_intersection_point=punto_corte_norm,
        raw_plateau_interval=intervalo_raw,
        normalized_plateau_interval=intervalo_norm,
        quota_value=quota_value,
        quota_period=quota_period,
        exhaustion_threshold=threshold_td,
        case=case
    )
    
    
if __name__ == "__main__":
    plan = Plan("prop plan", bounded_rate=BoundedRate(rate=Rate(100, "1min"), quota=Quota(5000, "1h")), cost=0, overage_cost=0, max_number_of_subscriptions=1, billing_period="1month")
    
    #resultado = run_plan_analysis(plan)
    #print(resultado)
    plan_azure = Plan("Azure AI", BoundedRate(rate=Rate(1000, "1min"), quota=[Quota(2000000, "1h")]), 0, 0, 1, "1month")

    print(plan_azure.quota_exhaustion_thresholds())
    print(plan_azure.bounded_rate.quota)
    print (generate_points_for_curves(plan_azure))