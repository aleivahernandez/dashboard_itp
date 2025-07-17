# -----------------------------------------------------------------------------
# app.py - Dashboard Interactivo de Regiones de Chile
# -----------------------------------------------------------------------------
# Importación de librerías necesarias
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

# --- Configuración de la Página ---
# Esto debe ser el primer comando de Streamlit en tu script.
st.set_page_config(
    page_title="Dashboard de Necesidades Tecnológicas",
    page_icon="🇨�",
    layout="wide"
)

# --- Funciones de Carga de Datos (con caché para mejorar rendimiento) ---

@st.cache_data # Streamlit guardará en caché los datos para no recargarlos cada vez
def cargar_datos_excel(archivo_excel):
    """Carga los datos desde el archivo Excel especificado."""
    try:
        # Lee el archivo Excel. 'openpyxl' es necesario para archivos .xlsx
        df = pd.read_excel(archivo_excel, engine='openpyxl')
        return df
    except FileNotFoundError:
        # Si el archivo no se encuentra, muestra un error y detiene la app.
        st.error(f"Error: No se encontró el archivo '{archivo_excel}'. Asegúrate de que esté en el repositorio de GitHub.")
        st.stop()
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
        st.stop()

@st.cache_data
def cargar_mapa_chile():
    """
    Carga el archivo GeoJSON con las geometrías de las regiones de Chile
    directamente desde una URL para evitar errores de archivo no encontrado.
    """
    # URL directa y estable al archivo GeoJSON en un repositorio de GitHub.
    url_mapa = "https://raw.githubusercontent.com/M-L-P/chile_geojson/master/regiones/regiones.geojson"
    try:
        # Lee el archivo GeoJSON desde la URL
        gdf = gpd.read_file(url_mapa)
        # Estandarizar el nombre de la columna de la región para que coincida con el merge
        gdf.rename(columns={'nombre': 'Region'}, inplace=True)
        return gdf
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el mapa desde la URL: {e}")
        st.stop()

# --- Carga y Preparación de Datos ---

# Nombre del archivo Excel del usuario
nombre_archivo_excel = "Consolidado regiones piloto (necesidades tecnológicas).xlsx"

# Carga los datos
df_necesidades = cargar_datos_excel(nombre_archivo_excel)
gdf_mapa_chile = cargar_mapa_chile()

# Hacemos un 'left merge' para asegurarnos de que TODAS las regiones del mapa
# estén presentes, incluso si no tienen datos en el Excel.
# Las regiones sin datos en el Excel tendrán valores NaN (nulos) en las columnas correspondientes.
datos_completos_mapa = gdf_mapa_chile.merge(
    df_necesidades,
    left_on='Region',  # Nombre de la columna de región en el GeoJSON (ahora estandarizado)
    right_on='Región', # Nombre de la columna de región en tu Excel
    how='left'
)

# --- Interfaz de Usuario del Dashboard ---

st.title("🗺️ Dashboard de Necesidades Tecnológicas por Región")
st.markdown("Utiliza el mapa o el menú desplegable para filtrar la información por región.")

# --- Creación del Mapa Interactivo y el Selector ---

# Creamos dos columnas para poner el selector al lado del mapa
col1, col2 = st.columns([1, 3]) # La columna del mapa será 3 veces más ancha

with col1:
    st.subheader("Filtro")
    # Creamos un selector con todas las regiones del mapa
    region_seleccionada = st.selectbox(
        label="Selecciona una Región:",
        options=sorted(gdf_mapa_chile["Region"].unique()), # Opciones son todas las regiones del mapa, ordenadas alfabéticamente
        index=None, # Para que no haya ninguna seleccionada por defecto
        placeholder="Elige una región..."
    )

with col2:
    st.subheader("Mapa de Chile")
    # Creamos la figura del mapa coroplético con Plotly
    fig = px.choropleth_mapbox(
        datos_completos_mapa,
        geojson=datos_completos_mapa.geometry,
        locations=datos_completos_mapa.index,
        color="Region",  # Colorea cada región de un color distinto
        hover_name="Region", # Muestra el nombre de la región al pasar el mouse
        mapbox_style="carto-positron", # Estilo del mapa base
        center={"lat": -38.4161, "lon": -72.3432}, # Centro aproximado de Chile
        zoom=3.5,
        opacity=0.6,
        height=600
    )
    # Ajustamos el layout para que no tenga márgenes innecesarios
    fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    st.plotly_chart(fig, use_container_width=True)

# --- Visualización de la Tabla de Datos Filtrada ---

st.subheader("Detalle de Datos")

# Si el usuario ha seleccionado una región...
if region_seleccionada:
    # Filtramos el DataFrame original (el de tu Excel)
    df_filtrado = df_necesidades[df_necesidades['Región'] == region_seleccionada]

    # Verificamos si hay datos para la región seleccionada
    if not df_filtrado.empty:
        st.write(f"Mostrando datos para la región de **{region_seleccionada}**:")
        # Mostramos la tabla con los datos filtrados
        st.dataframe(df_filtrado)
    else:
        # Si no hay filas para esa región, mostramos un mensaje informativo
        st.info(f"No hay datos disponibles en el archivo para la región de **{region_seleccionada}**.")
else:
    # Si no se ha seleccionado ninguna región, mostramos la tabla completa
    st.write("Mostrando todos los datos disponibles. Selecciona una región para filtrar.")
    st.dataframe(df_necesidades)
