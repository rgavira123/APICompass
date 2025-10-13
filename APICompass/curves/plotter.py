import plotly.graph_objects as go
from typing import Optional
from APICompass.curves.charge import AnalysisResult
from APICompass.ancillary.time_unit import TimeUnit


def _prepare_raw_data(points, target_unit, quota_period_unit):
    """Helper function to convert raw time data to the target unit."""
    if target_unit is None:
        target_unit = quota_period_unit

    converted_points = [
        (p[0].unit.to(target_unit, p[0].value), p[1]) for p in points
    ]
    return zip(*converted_points)

def _add_intersection_markers(fig, result, normalized=True, target_unit=None):
    """Helper function to add intersection or plateau markers to a figure."""
    if result.normalized_plateau_interval and normalized:
        (x_start, y_start), (x_end, y_end) = result.normalized_plateau_interval
        fig.add_shape(
            type="rect", xref="x", yref="y",
            x0=x_start, y0=0, x1=x_end, y1=y_start,
            fillcolor="LightGreen", opacity=0.3, layer="below", line_width=0,
        )
        fig.add_annotation(x=(x_start+x_end)/2, y=y_start-0.1, text="Meseta de Sostenibilidad", showarrow=False)
    
    elif result.raw_plateau_interval and not normalized:
        target_unit = target_unit or result.quota_period.unit
        (p_start, p_end) = result.raw_plateau_interval
        x_start = p_start[0].unit.to(target_unit, p_start[0].value)
        x_end = p_end[0].unit.to(target_unit, p_end[0].value)
        y_val = p_start[1]
        fig.add_shape(
            type="rect", xref="x", yref="y",
            x0=x_start, y0=0, x1=x_end, y1=y_val,
            fillcolor="LightGreen", opacity=0.3, layer="below", line_width=0,
        )

    elif result.normalized_intersection_point and normalized:
        fig.add_trace(go.Scatter(
            x=[result.normalized_intersection_point[0]], y=[result.normalized_intersection_point[1]], mode='markers+text', name='Punto de Equilibrio',
            marker=dict(color='green', size=12, symbol='x'),
            text=[f"Corte ({result.normalized_intersection_point[0]:.2f}, {result.normalized_intersection_point[1]:.2f})"], textposition="top center"
        ))
        
    elif result.raw_intersection_point and not normalized:
        target_unit = target_unit or result.quota_period.unit
        x_cut_raw, y_cut_raw = result.raw_intersection_point
        x_cut = x_cut_raw.unit.to(target_unit, x_cut_raw.value)
        fig.add_trace(go.Scatter(
            x=[x_cut], y=[y_cut_raw], mode='markers+text', name='Punto de Equilibrio',
            marker=dict(color='green', size=12, symbol='x'),
            text=[f"Corte ({x_cut:.2f}, {y_cut_raw:.2f})"], textposition="top center"
        ))

def plot_consumption_analysis(result: AnalysisResult, normalized: bool = True, target_unit: Optional[TimeUnit] = None) -> go.Figure:
    """
    Crea una figura de Plotly completa con las curvas de carga, descarga y sus anotaciones.
    Esta es la función principal y más completa.
    """
    fig = go.Figure()
    
    if normalized:
        load_x, load_y = zip(*result.normalized_load_points)
        discharge_x, discharge_y = zip(*result.normalized_discharge_points)
        x_label, y_label = "Tiempo Normalizado", "Cuota Normalizada"
        title = "Análisis de Consumo Normalizado"
    else:
        load_x, load_y = _prepare_raw_data(result.raw_load_points, target_unit, result.quota_period.unit)
        discharge_x, discharge_y = _prepare_raw_data(result.raw_discharge_points, target_unit, result.quota_period.unit)
        time_unit_str = (target_unit or result.quota_period.unit).value
        x_label, y_label = f"Tiempo ({time_unit_str})", "Requests"
        title = "Análisis de Consumo (Valores Reales)"

    # Añadir Trazas (Curvas)
    fig.add_trace(go.Scatter(
        x=list(load_x), y=list(load_y), mode='lines+markers', name='Carga (Consumo)', line=dict(color='blue')
    ))
    fig.add_trace(go.Scatter(
        x=list(discharge_x), y=list(discharge_y), mode='lines+markers', name='Descarga (Capacidad Residual)', line=dict(color='red')
    ))

    # Añadir el Punto de Corte o la Meseta
    _add_intersection_markers(fig, result, normalized, target_unit)

    # Estilizar la Gráfica
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
    )
    if normalized:
        fig.update_layout(xaxis_range=[0, 1], yaxis_range=[0, 1.1])
    
    return fig

def plot_single_curve(result: AnalysisResult, curve_type: str, normalized: bool = True, target_unit: Optional[TimeUnit] = None) -> go.Figure:
    """
    Crea una figura de Plotly con una única curva especificada.
    
    Args:
        result: El objeto AnalysisResult.
        curve_type: El tipo de curva a graficar ('load', 'discharge', o 'window').
        normalized: Si se deben usar los datos normalizados.
        target_unit: La unidad de tiempo para los datos raw.
    """
    fig = go.Figure()

    curve_map = {
        'load': ('normalized_load_points', 'raw_load_points', 'Carga (Consumo)', 'blue'),
        'discharge': ('normalized_discharge_points', 'raw_discharge_points', 'Descarga (Capacidad Residual)', 'red'),
        # Asumiendo que 'ventana' se añadirá a AnalysisResult
        # 'window': ('normalized_window_points', 'raw_window_points', 'Ventana de Consumo', 'purple'),
    }

    if curve_type not in curve_map:
        raise ValueError("curve_type debe ser 'load', 'discharge', o 'window'")

    norm_key, raw_key, name, color = curve_map[curve_type]

    if normalized:
        points = getattr(result, norm_key)
        x_data, y_data = zip(*points)
        x_label, y_label = "Tiempo Normalizado", "Cuota Normalizada"
        title = f"Curva de {name} Normalizada"
    else:
        points = getattr(result, raw_key)
        x_data, y_data = _prepare_raw_data(points, target_unit, result.quota_period.unit)
        time_unit_str = (target_unit or result.quota_period.unit).value
        x_label, y_label = f"Tiempo ({time_unit_str})", "Requests"
        title = f"Curva de {name} (Valores Reales)"

    fig.add_trace(go.Scatter(
        x=list(x_data), y=list(y_data), mode='lines+markers', name=name, line=dict(color=color)
    ))
    
    fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label)
    if normalized:
        fig.update_layout(xaxis_range=[0, 1], yaxis_range=[0, 1.1])
        
    return fig

# --- BLOQUE DE PRUEBA ---
if __name__ == '__main__':
    # Este bloque solo se ejecuta cuando corres el script directamente
    # (ej: python APICompass/visualization/plotter.py)
    # Es útil para probar las funciones de visualización sin necesidad de Streamlit.

    # 1. Crear un objeto AnalysisResult de prueba (mock)
    # Asumimos que estas clases están disponibles en tu proyecto
    from APICompass.curves.charge import AnalysisResult
    from APICompass.ancillary.time_unit import TimeDuration, TimeUnit

    # Datos de prueba para un caso con punto de corte
    mock_result_corte = AnalysisResult(
        raw_load_points=[(TimeDuration(0, TimeUnit.HOUR), 100), (TimeDuration(0.8167, TimeUnit.HOUR), 5000), (TimeDuration(1, TimeUnit.HOUR), 5000)],
        raw_discharge_points=[(TimeDuration(0, TimeUnit.HOUR), 5000), (TimeDuration(0.1833, TimeUnit.HOUR), 5000), (TimeDuration(1, TimeUnit.HOUR), 100)],
        normalized_load_points=[(0.0, 0.02), (0.8167, 1.0), (1.0, 1.0)],
        normalized_discharge_points=[(0.0, 1.0), (0.1833, 1.0), (1.0, 0.02)],
        raw_intersection_point=(TimeDuration(0.5, TimeUnit.HOUR), 3100.0),
        normalized_intersection_point=(0.5, 0.62),
        raw_plateau_interval=None,
        normalized_plateau_interval=None,
        quota_value=5000.0,
        quota_period=TimeDuration(1, TimeUnit.HOUR),
        exhaustion_threshold=TimeDuration(49, TimeUnit.MINUTE)
    )

    # 2. Probar las funciones de ploteo
    print("Mostrando gráfica de análisis conjunto (normalizado)...")
    fig1 = plot_consumption_analysis(mock_result_corte, normalized=True)
    fig1.show()

    print("Mostrando gráfica de análisis conjunto (valores reales en minutos)...")
    fig2 = plot_consumption_analysis(mock_result_corte, normalized=False, target_unit=TimeUnit.MINUTE)
    fig2.show()

    print("Mostrando gráfica de una sola curva (Carga)...")
    fig3 = plot_single_curve(mock_result_corte, curve_type='load', normalized=False, target_unit=TimeUnit.MINUTE)
    fig3.show()

