import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
# st.set_page_config() debe ser el primer comando de Streamlit en tu script.
st.set_page_config(
    page_title="API Compass",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODELO DE DATOS Y LÓGICA (Aquí irían los imports de tus módulos) ---
# from plan import Plan
# from charge_model import generate_charge_curves
# Por ahora, usamos funciones placeholder.

# --- FUNCIONES PARA CADA PÁGINA/SECCIÓN ---
# Encapsular el contenido de cada sección en una función hace el código más limpio.

def show_home_page():
    """Muestra la página de bienvenida e introducción."""
    st.title("🏡 Bienvenida al Modelador de Consumo de APIs")
    st.markdown("""
    Esta herramienta te ayuda a visualizar y entender los límites de consumo de una API
    utilizando una analogía de **carga y descarga**, similar a una batería.
    
    **Navega por las diferentes secciones usando el menú de la izquierda.**
    
    ### ¿Qué puedes hacer aquí?
    - **Simulador Interactivo:** Introduce los límites de una API y tu tasa de consumo para generar un `Quota Burn-down Chart` y analizar su sostenibilidad.
    - **Casos de Estudio:** Explora ejemplos pre-configurados que ilustran escenarios comunes (consumo ideal, 'bursts' insostenibles, etc.).
    - **Sobre el Modelo:** Aprende más sobre la teoría detrás de este análisis.
    """)

def show_interactive_simulator():
    """Muestra el simulador donde el usuario introduce los datos."""
    st.title("🛠️ Simulador Interactivo")
    st.markdown("Introduce los parámetros de la API y tu tasa de consumo esperada para generar el análisis.")
    
    # --- Columna de Entradas (Inputs) ---
    with st.container(border=True):
        st.subheader("Parámetros de la API")
        col1, col2, col3 = st.columns(3)
        with col1:
            quota = st.number_input("Cuota Total (requests)", min_value=1, value=5000)
        with col2:
            window = st.number_input("Ventana de Tiempo (minutos)", min_value=1, value=60)
        with col3:
            rate = st.number_input("Tasa de Consumo (requests/minuto)", min_value=1, value=100)
    
    # --- Columna de Salidas (Outputs) ---
    if st.button("Generar Análisis", type="primary"):
        st.subheader("Resultados del Análisis")
        st.info("Aquí es donde llamarías a tu lógica de `charge_model.py` y mostrarías el gráfico de Plotly.")
        
        # Placeholder para la gráfica
        st.markdown("> *Gráfica de `Quota Burn-down` aparecerá aquí...*")
        
        # Placeholder para el diagnóstico
        st.success("Diagnóstico: **Consumo Sostenible**. Tienes suficiente margen (`headroom`).")

def show_case_studies():
    """Muestra los ejemplos y casos de estudio guiados."""
    st.title("📚 Casos de Estudio")
    st.markdown("Aquí analizarás y explicarás diferentes escenarios con configuraciones fijas.")

    with st.expander("Caso A: Consumo Ideal y Sostenible", expanded=True):
        st.markdown("""
        **Escenario:** Una API con una cuota generosa y un cliente que consume a una tasa constante y moderada.
        
        **Análisis:** El punto de equilibrio (`equilibrium point`) se encuentra muy por encima del umbral de seguridad, indicando un uso saludable y con margen para picos de demanda.
        
        *Aquí iría la gráfica de Plotly para este caso.*
        """)

    with st.expander("Caso B: Consumo Insostenible por Ráfagas ('Bursts')"):
        st.markdown("""
        **Escenario:** Un script que, al iniciarse, intenta sincronizar muchos datos, consumiendo la cuota de forma muy agresiva al principio.
        
        **Análisis:** El `headroom` se agota rápidamente. Este patrón de consumo llevará inevitablemente a errores `429 Too Many Requests` si no se implementa una estrategia de `backoff`.
        
        *Aquí iría la gráfica de Plotly para este caso.*
        """)

def show_about_page():
    """Muestra la explicación teórica del modelo."""
    st.title("📖 Sobre el Modelo")
    st.markdown("""
    ### El Concepto de Carga y Descarga
    El modelo se basa en una analogía simple:
    
    - La **Cuota Total** de la API es la **capacidad máxima de una batería**.
    - La **Curva de Carga (Azul)** representa la **energía consumida** a lo largo del tiempo.
    - La **Curva de Descarga (Roja)** representa la **energía restante** o capacidad residual (`headroom`).
    
    ### Sostenibilidad
    Un patrón de consumo se considera **sostenible** si la capacidad residual no se agota antes de que la ventana de tiempo se reinicie. El punto donde ambas curvas se cruzan nos da una indicación clave de la "salud" de nuestra estrategia de consumo.
    """)
    st.image("https://i.imgur.com/8StBwTj.png", caption="Analogía visual del modelo de consumo.")


# --- NAVEGACIÓN PRINCIPAL EN LA BARRA LATERAL ---
# Usamos un st.radio para crear el menú de navegación.
st.sidebar.title("Navegación")
page_options = {
    "Bienvenida": show_home_page,
    "Simulador Interactivo": show_interactive_simulator,
    "Casos de Estudio": show_case_studies,
    "Sobre el Modelo": show_about_page
}

selected_page = st.sidebar.radio("Elige una sección:", list(page_options.keys()))

# --- RENDERIZADO DE LA PÁGINA SELECCIONADA ---
# Llama a la función correspondiente a la opción elegida en el menú.
page_options[selected_page]()

# Añade un pie de página a la barra lateral
st.sidebar.markdown("---")
st.sidebar.info("Desarrollado por [Tu Nombre].")
