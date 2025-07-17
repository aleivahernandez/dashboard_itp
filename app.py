# -----------------------------------------------------------------------------
# app.py - Dashboard con Gráfico de Radar
# -----------------------------------------------------------------------------
# Importación de librerías necesarias
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard de Ejes Priorizados",
    page_icon="📊",
    layout="wide"
)

# --- Funciones de Carga de Datos (con caché para mejorar rendimiento) ---

@st.cache_data
def cargar_datos_excel(archivo_excel):
    """Carga los datos desde el archivo Excel especificado."""
    try:
        df = pd.read_excel(archivo_excel, engine='openpyxl')
        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo '{archivo_excel}'. Asegúrate de que esté en el repositorio de GitHub.")
        st.stop()
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
        st.stop()

# --- Carga y Preparación de Datos ---

nombre_archivo_excel = "Consolidado regiones piloto (necesidades tecnológicas).xlsx"
df_necesidades = cargar_datos_excel(nombre_archivo_excel)

# --- Interfaz de Usuario del Dashboard ---

st.title("📊 Dashboard de Ejes Traccionantes por Región")
st.markdown("Este dashboard visualiza la frecuencia de las dimensiones priorizadas en cada región piloto.")

# --- Procesamiento de Datos para el Gráfico de Radar ---

# Validar que las columnas necesarias existan en el DataFrame
columna_ejes = "Ejes traccionantes/dimensiones priorizadas"
columna_region = "Región"

if columna_ejes not in df_necesidades.columns or columna_region not in df_necesidades.columns:
    st.error(f"El archivo Excel debe contener las columnas '{columna_ejes}' y '{columna_region}'.")
    st.stop()

# Agrupar por región y por eje para contar la frecuencia de cada uno
df_radar = df_necesidades.groupby([columna_region, columna_ejes]).size().reset_index(name='Cantidad')

# --- Filtros Interactivos ---

st.sidebar.header("Filtros")
regiones_seleccionadas = st.sidebar.multiselect(
    "Selecciona una o más regiones para visualizar:",
    options=df_radar[columna_region].unique(),
    default=df_radar[columna_region].unique() # Por defecto, todas seleccionadas
)

# Filtrar el dataframe basado en la selección
if regiones_seleccionadas:
    df_filtrado = df_radar[df_radar[columna_region].isin(regiones_seleccionadas)]
else:
    df_filtrado = df_radar # Si no se selecciona nada, mostrar todo (aunque el default lo evita)


# --- Visualización del Gráfico de Radar ---

st.subheader("Gráfico de Radar: Frecuencia de Dimensiones Priorizadas")

if not df_filtrado.empty:
    # Crear el gráfico de radar (line_polar)
    fig = px.line_polar(
        df_filtrado,
        r='Cantidad',  # El valor numérico (radio)
        theta=columna_ejes,  # Las categorías en el perímetro (ejes)
        color=columna_region,  # Una línea de color por cada región
        line_close=True,  # Cierra el polígono para formar el radar
        markers=True, # Muestra puntos en cada eje para mayor claridad
        title="Comparativa de Ejes Priorizados por Región"
    )

    fig.update_layout(
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay datos para mostrar con las regiones seleccionadas. Por favor, elige al menos una región en el filtro de la barra lateral.")


# --- Visualización de la Tabla de Datos ---

with st.expander("Ver datos tabulados"):
    st.write("Datos procesados para la generación del gráfico:")
    # Mostrar la tabla de datos procesados que alimenta el gráfico
    st.dataframe(df_filtrado)

    st.write("Datos originales del archivo Excel:")
    # Mostrar la tabla original completa
    st.dataframe(df_necesidades)

