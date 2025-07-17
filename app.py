# -----------------------------------------------------------------------------
# app.py - Dashboard Interactivo de Regiones de Chile (Versión Silueta)
# -----------------------------------------------------------------------------
# Importación de librerías necesarias
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
from streamlit_plotly_events import plotly_events # Librería para capturar eventos del mapa

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard de Necesidades Tecnológicas",
    page_icon="c🇱",
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

@st.cache_data
def cargar_mapa_chile():
    """Carga el archivo GeoJSON con las geometrías de las regiones de Chile."""
    nombre_archivo_mapa = "regiones_chile.geojson"
    try:
        gdf = gpd.read_file(nombre_archivo_mapa)
        if 'nombre' in gdf.columns:
            gdf.rename(columns={'nombre': 'Region'}, inplace=True)
        # Se necesita reproyectar para que px.choropleth lo muestre correctamente
        gdf = gdf.to_crs(epsg=4326)
        return gdf
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo del mapa '{nombre_archivo_mapa}'.")
        st.error("Por favor, asegúrate de que el archivo esté en tu repositorio de GitHub y que el nombre sea correcto.")
        st.stop()
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo del mapa: {e}")
        st.stop()

# --- Carga y Preparación de Datos ---

nombre_archivo_excel = "Consolidado regiones piloto (necesidades tecnológicas).xlsx"
df_necesidades = cargar_datos_excel(nombre_archivo_excel)
gdf_mapa_chile = cargar_mapa_chile()

datos_completos_mapa = gdf_mapa_chile.merge(
    df_necesidades,
    left_on='Region',
    right_on='Región',
    how='left'
)

# --- Interfaz de Usuario del Dashboard ---

st.title("🗺️ Dashboard de Necesidades Tecnológicas por Región")
st.markdown("Haz clic sobre una región en el mapa para filtrar la información.")

# --- Mapa de Silueta como Filtro ---

st.subheader("Mapa de Chile")
# Usamos px.choropleth en lugar de px.choropleth_mapbox para crear la silueta
fig = px.choropleth(
    datos_completos_mapa,
    geojson=datos_completos_mapa.geometry,
    locations=datos_completos_mapa.index,
    color="Region",
    hover_name="Region",
    projection="mercator" # Proyección para visualizar correctamente
)

# Ajustes para que se vea como una silueta y no como un mapa geográfico
fig.update_geos(
    fitbounds="locations", # Centra el mapa en las geometrías de Chile
    visible=False # Oculta el mapa base, los ejes y las fronteras
)
fig.update_layout(
    height=700,
    margin={"r":0, "t":0, "l":0, "b":0},
    coloraxis_showscale=False # Oculta la leyenda de colores
)

# Usamos plotly_events para capturar los clics en el mapa
selected_points = plotly_events(fig, click_event=True, key="map_click_silhouette")

# --- Lógica de Filtro y Visualización de la Tabla ---

# Inicializamos el estado de la sesión para guardar la selección
if 'region_seleccionada' not in st.session_state:
    st.session_state.region_seleccionada = None

# Si el usuario hace clic en el mapa, actualizamos el estado
if selected_points:
    clicked_index = selected_points[0]['pointNumber']
    st.session_state.region_seleccionada = datos_completos_mapa.iloc[clicked_index]['Region']

# Botón para limpiar la selección y mostrar todos los datos
if st.button("Limpiar filtro y mostrar todas las regiones"):
    st.session_state.region_seleccionada = None
    st.rerun()

st.subheader("Detalle de Datos")

# Si hay una región seleccionada en el estado de la sesión...
if st.session_state.region_seleccionada:
    region = st.session_state.region_seleccionada
    df_filtrado = df_necesidades[df_necesidades['Región'] == region]

    if not df_filtrado.empty:
        st.write(f"Mostrando datos para la región de **{region}**:")
        st.dataframe(df_filtrado)
    else:
        st.info(f"No hay datos disponibles en el archivo para la región de **{region}**.")
else:
    # Si no se ha seleccionado ninguna región, mostramos la tabla completa
    st.write("Mostrando todos los datos disponibles. Haz clic en una región para filtrar.")
    st.dataframe(df_necesidades)
