from dataclasses import dataclass
from typing import List, Optional, Tuple
from APICompass.ancillary.time_unit import TimeDuration
from APICompass.basic.bounded_rate import BoundedRate, Quota, Rate
from APICompass.basic.plan_and_demand import Plan
from APICompass.utils import parse_time_string_to_duration
import sympy as sp


def generate_points_for_curves(plan: Plan):
    threshold_str = plan.quota_exhaustion_thresholds()
    threshold_td = parse_time_string_to_duration(threshold_str)
    exhaustion_threshold_s = threshold_td.to_seconds()
 
    rate_value = plan.bounded_rate.rate.consumption_unit
 
    quota_obj = plan.bounded_rate.quota[0]
    quota_value = quota_obj.consumption_unit
    quota_period_s = quota_obj.consumption_period.to_seconds()
    quota_period = quota_obj.consumption_period
 
    # helper: segundos -> TimeDuration en unidades de quota_period
    def to_td(seconds):
        val = quota_period.unit.seconds_to_time_unit(seconds)
        return TimeDuration(val, quota_period.unit)
 
    # --- Raw points como TimeDuration ---
    carga_raw = [
        (TimeDuration(0, quota_period.unit), rate_value),
        (to_td(exhaustion_threshold_s), quota_value),
        (quota_period, quota_value)
    ]
 
    descarga_raw = [
        (TimeDuration(0, quota_period.unit), quota_value),
        (to_td(quota_period_s - exhaustion_threshold_s), quota_value),
        (quota_period, rate_value)
    ]
 
    ventana_raw = [
        (TimeDuration(0, quota_period.unit), rate_value),
        (to_td(exhaustion_threshold_s), quota_value),
        (to_td(quota_period_s - exhaustion_threshold_s), quota_value),
        (quota_period, rate_value)
    ]
 
    # --- Normalización ---
    def normalize(points):
        return [
            (p[0].to_seconds() / quota_period_s, p[1] / quota_value)
            for p in points
        ]
 
    carga_norm = normalize(carga_raw)
    descarga_norm = normalize(descarga_raw)
    ventana_norm = normalize(ventana_raw)
 
    # --- Detección de corte o meseta ---
    corte_raw = None
    corte_norm = None
    intervalo_raw = None
    intervalo_norm = None
 
    if 2*exhaustion_threshold_s < quota_period_s:
        # Caso meseta central (After-half)
        intervalo_raw = (
            (to_td(exhaustion_threshold_s), quota_value),
            (to_td(quota_period_s - exhaustion_threshold_s), quota_value)
        )
        intervalo_norm = (
            (exhaustion_threshold_s / quota_period_s, 1.0),
            ((quota_period_s - exhaustion_threshold_s)/quota_period_s, 1.0)
        )
    else:
        # Caso normal: corte único
        x = sp.Symbol('x')
 
        # Azul: tramo inicial
        (xa1, ya1), (xa2, ya2) = carga_norm[0], carga_norm[1]
        f_azul = (ya2 - ya1) / (xa2 - xa1) * (x - xa1) + ya1
 
        # Roja: tramo final
        (xr1, yr1), (xr2, yr2) = descarga_norm[1], descarga_norm[2]
        f_roja = (yr2 - yr1) / (xr2 - xr1) * (x - xr1) + yr1
 
        sol = sp.solve(sp.Eq(f_azul, f_roja), x)
        if sol:
            x_cut = float(sol[0])
            y_cut = float(f_azul.subs(x, x_cut))
            corte_norm = (x_cut, y_cut)
            corte_raw = (
                to_td(x_cut * quota_period_s),
                y_cut * quota_value
            )
 
    return {
        "carga_raw": carga_raw,
        "descarga_raw": descarga_raw,
        "ventana_raw": ventana_raw,
        "carga_norm": carga_norm,
        "descarga_norm": descarga_norm,
        "ventana_norm": ventana_norm,
        "punto_corte_raw": corte_raw,
        "punto_corte_norm": corte_norm,
        "intervalo_corte_raw": intervalo_raw,
        "intervalo_corte_norm": intervalo_norm,
        "quota_value": quota_value,
        "quota_period": quota_period,
        "exhaustion_threshold": threshold_td
    }
    
    
@dataclass
class AnalysisResult:
    """
    Almacena todos los resultados calculados del análisis de un Plan.
    Es una estructura de datos limpia que reemplaza el diccionario.
    """
    # Puntos de las curvas
    raw_load_points: List[Tuple[TimeDuration, float]]
    raw_discharge_points: List[Tuple[TimeDuration, float]]
    normalized_load_points: List[Tuple[float, float]]
    normalized_discharge_points: List[Tuple[float, float]]

    # Puntos de corte
    raw_intersection_point: Optional[Tuple[TimeDuration, float]]
    normalized_intersection_point: Optional[Tuple[float, float]]
    
    # Intervalos de meseta
    raw_plateau_interval: Optional[Tuple[Tuple[TimeDuration, float], Tuple[TimeDuration, float]]]
    normalized_plateau_interval: Optional[Tuple[Tuple[float, float], Tuple[float, float]]]

    # Metadatos útiles para los gráficos
    quota_value: float
    quota_period: TimeDuration
    exhaustion_threshold: TimeDuration
    

def run_plan_analysis(plan: Plan) -> AnalysisResult:
    """
    Función de alto nivel que ejecuta el análisis y devuelve un objeto estructurado.
    Esta es la función que tu app de Streamlit llamará.
    """
    # 1. Llama a tu función original para obtener el diccionario de datos
    analysis_dict = generate_points_for_curves(plan)

    # 2. Crea y devuelve una instancia de AnalysisResult
    #    mapeando las claves del diccionario a los atributos del objeto.
    result = AnalysisResult(
        raw_load_points=analysis_dict["carga_raw"],
        raw_discharge_points=analysis_dict["descarga_raw"],
        normalized_load_points=analysis_dict["carga_norm"],
        normalized_discharge_points=analysis_dict["descarga_norm"],
        raw_intersection_point=analysis_dict["punto_corte_raw"],
        normalized_intersection_point=analysis_dict["punto_corte_norm"],
        raw_plateau_interval=analysis_dict["intervalo_corte_raw"],
        normalized_plateau_interval=analysis_dict["intervalo_corte_norm"],
        quota_value=analysis_dict["quota_value"],
        quota_period=analysis_dict["quota_period"],
        exhaustion_threshold=analysis_dict["exhaustion_threshold"]
    )
    
    return result
    
    
if __name__ == "__main__":
    plan = Plan("prop plan", bounded_rate=BoundedRate(rate=Rate(100, "1min"), quota=Quota(5000, "1h")), cost=0, overage_cost=0, max_number_of_subscriptions=1, billing_period="1month")
    
    resultado = run_plan_analysis(plan)
    print(resultado)