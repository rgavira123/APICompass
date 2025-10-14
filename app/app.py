import streamlit as st
import plotly.graph_objects as go

# --- Importaciones de tu Librería APICompass ---
# Asegúrate de que tu librería está instalada en modo editable (pip install -e .)
# para que estos imports funcionen.
from APICompass.ancillary.time_unit import TimeUnit
from APICompass.basic.bounded_rate import Rate, Quota, BoundedRate
from APICompass.basic.plan_and_demand import Plan
# Asumimos que has creado estos módulos como discutimos
from APICompass.curves.charge import run_plan_analysis
from APICompass.curves.plotter import plot_consumption_analysis


# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="API Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- FUNCIONES PARA CADA PÁGINA/SECCIÓN ---

def show_interactive_simulator():
    """Muestra el simulador donde el usuario introduce los datos."""
    st.title("🛠️ Simulador Interactivo")
    st.markdown("Define los límites de un plan de API para generar su 'Quota Burn-down Chart' y analizar su sostenibilidad.")

    with st.container(border=True):
        st.subheader("Parámetros del Plan")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            rate_val = st.number_input("Rate (requests)", min_value=1, value=100)
            rate_unit_str = st.text_input("Unidad de Rate", value="1min")
        
        with col2:
            quota_val = st.number_input("Quota (requests)", min_value=1, value=5000)
            quota_unit_str = st.text_input("Unidad de Quota", value="1min")
        
        with col3:
            st.markdown("<br/>", unsafe_allow_html=True) # Spacer for alignment
            generate_btn = st.button("Generar Análisis", type="primary")
        
        with col4:
            st.markdown("<br/>", unsafe_allow_html=True) # Spacer for alignment
            normalized_view = st.toggle("Vista Normalizada", value=True)


    if generate_btn:
        try:
            # 1. Crear el objeto Plan a partir de las entradas del usuario
            rate = Rate(rate_val, rate_unit_str)
            quota = Quota(quota_val, quota_unit_str)
            bounded_rate = BoundedRate(rate=rate, quota=[quota])
            simulated_plan = Plan(
                name="Plan Simulado",
                bounded_rate=bounded_rate,
                cost=0, overage_cost=0, max_number_of_subscriptions=1, billing_period="1month"
            )
            
            # 2. Ejecutar el análisis
            analysis_result = run_plan_analysis(simulated_plan)

            # 3. Generar la figura de Plotly
            target_unit_map = {"1min": TimeUnit.MINUTE, "1h": TimeUnit.HOUR, "1day": TimeUnit.DAY}
            target_unit = target_unit_map.get(quota_unit_str)

            fig = plot_consumption_analysis(analysis_result, normalized=normalized_view, target_unit=target_unit)

            # 4. Mostrar la figura
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Ha ocurrido un error al generar el análisis: {e}")
            st.exception(e)


def show_case_studies():
    """Muestra los ejemplos y casos de estudio guiados."""
    st.title("📚 Casos de Estudio")
    st.markdown("Análisis de diferentes planes de API del mundo real.")

    # --- Caso Zenhub ---
    with st.expander("Caso 1: Zenhub Enterprise", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            **Análisis del Plan:**
            - **Rate:** 100 requests / 1 minuto
            - **Quota:** 5000 requests / 1 hora
            
            **Observaciones:**
            *(Aquí puedes escribir tu análisis. Por ejemplo: Este plan muestra un equilibrio interesante...)*
            """)
        with col2:
            # Lógica para generar la gráfica
            plan_zenhub = Plan("Zenhub Enterprise", BoundedRate(rate=Rate(100, "1min"), quota=[Quota(5000, "1h")]), 0, 0, 1, "1month")
            result_zenhub = run_plan_analysis(plan_zenhub)
            fig_zenhub = plot_consumption_analysis(result_zenhub, normalized=True)
            st.plotly_chart(fig_zenhub, use_container_width=True)

    # --- Caso Github ---
    with st.expander("Caso 2: Github (GET Operations)"):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            **Análisis del Plan:**
            - **Rate:** 900 requests / 1 minuto
            - **Quota:** 5000 requests / 1 hora
            
            **Observaciones:**
            *(Placeholder para tu análisis...)*
            """)
        with col2:
            plan_github = Plan("Github GET", BoundedRate(rate=Rate(900, "1min"), quota=[Quota(5000, "1h")]), 0, 0, 1, "1month")
            result_github = run_plan_analysis(plan_github)
            fig_github = plot_consumption_analysis(result_github, normalized=True)
            st.plotly_chart(fig_github, use_container_width=True)
    
    # --- Caso Google Cloud ---
    with st.expander("Caso 3: Google Cloud Natural Language API"):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            **Análisis del Plan:**
            - **Rate:** 600 requests / 1 minuto
            - **Quota:** 800,000 requests / 1 día
            
            **Observaciones:**
            *(Placeholder para tu análisis...)*
            """)
        with col2:
            plan_gcp = Plan("Google Cloud NL", BoundedRate(rate=Rate(600, "1min"), quota=[Quota(800000, "1day")]), 0, 0, 1, "1month")
            result_gcp = run_plan_analysis(plan_gcp)
            fig_gcp = plot_consumption_analysis(result_gcp, normalized=True)
            st.plotly_chart(fig_gcp, use_container_width=True)
            
    # --- Caso Azure AI ---
    with st.expander("Caso 4: Azure AI Language (Standard)"):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            **Análisis del Plan:**
            - **Rate:** 1000 requests / 1 minuto
            - **Quota:** 2,000,000 requests / 1 hora
            
            **Observaciones:**
            *(Este es un caso interesante donde la tasa de consumo permitida es tan alta que agota la cuota horaria en solo 2000 minutos (más de una hora), lo que significa que el agotamiento ocurre teóricamente en el segundo 0. El modelo lo interpreta como una meseta total.)*
            """)
        with col2:
            plan_azure = Plan("Azure AI", BoundedRate(rate=Rate(1000, "1min"), quota=[Quota(2000000, "1h")]), 0, 0, 1, "1month")
            result_azure = run_plan_analysis(plan_azure)
            fig_azure = plot_consumption_analysis(result_azure, normalized=True)
            st.plotly_chart(fig_azure, use_container_width=True)

    # --- Caso Hardcodeado ---
    with st.expander("Caso 5: Mock API Inalcanzable"):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            **Análisis del Plan:**
            - **Quota Teórica:** 500,000 req/mes
            - **Capacidad Real (por rate limit):** 432,010 req/mes
            
            **Observaciones:**
            *(Este es un ejemplo de una API cuya cuota mensual es teóricamente inalcanzable debido a un rate limit más restrictivo. La curva de carga real (azul) nunca puede llegar al límite teórico (verde), demostrando una discrepancia entre el plan comercial y la limitación técnica.)*
            """)
        with col2:
            T = 720
            rate_value = 10
            quota_month = 500000
            capacity_month = 432010

            fig_mock = go.Figure()
            fig_mock.add_trace(go.Scatter(x=[0, T], y=[rate_value, capacity_month], mode="lines", line=dict(color="royalblue", width=2), name="Carga Real"))
            fig_mock.add_trace(go.Scatter(x=[0, T], y=[capacity_month, 0], mode="lines", line=dict(color="red", width=2, dash="dot"), name="Descarga (Real)"))
            fig_mock.add_trace(go.Scatter(x=[0, T], y=[quota_month, quota_month], mode="lines", line=dict(color="green", dash="dash"), name="Capacidad Teórica"))
            fig_mock.update_layout(title="API con Cuota Inalcanzable", xaxis_title="Tiempo (horas)", yaxis_title="Requests", template="plotly_white", showlegend=True)
            st.plotly_chart(fig_mock, use_container_width=True)


# --- NAVEGACIÓN PRINCIPAL ---
def main():
    """Función principal que renderiza la navegación y la página seleccionada."""
    st.sidebar.title("API Compass 🧭")
    
    page_options = {
        "Simulador Interactivo": show_interactive_simulator,
        "Casos de Estudio": show_case_studies,
    }

    selected_page = st.sidebar.radio("Elige una sección:", list(page_options.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.info("Esta aplicación utiliza el modelo de Carga/Descarga para analizar la sostenibilidad del consumo de APIs.")

    page_options[selected_page]()

if __name__ == "__main__":
    main()
