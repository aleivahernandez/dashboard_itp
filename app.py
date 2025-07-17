# -----------------------------------------------------------------------------
# app.py - Dashboard con Gráfico de Radar
# -----------------------------------------------------------------------------
# Importación de librerías necesarias
import streamlit as st
import pandas as pd
import plotly.express as px
from itertools import product

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard de Necesidades Tecnológicas",
    page_icon="📊",
    layout="wide"
)

# --- Funciones de Carga de Datos (con caché para mejorar rendimiento) ---

@st.cache_data
def cargar_datos_excel(archivo_excel):
    """Carga los datos desde la hoja 'db' del archivo Excel especificado."""
    try:
        # Leer la hoja específica "db" del archivo
        df = pd.read_excel(archivo_excel, sheet_name="db", engine='openpyxl')
        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo '{archivo_excel}'. Asegúrate de que esté en el repositorio de GitHub.")
        st.stop()
    except ValueError as e:
        if "Worksheet named 'db' not found" in str(e):
            st.error("Error: No se encontró la hoja 'db' en el archivo Excel. Por favor, verifica el nombre de la hoja.")
            st.stop()
        else:
            st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
            st.stop()
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
        st.stop()

# --- Carga y Preparación de Datos ---

nombre_archivo_excel = "Consolidado regiones piloto (necesidades tecnológicas).xlsx"
df_necesidades = cargar_datos_excel(nombre_archivo_excel)

# --- Interfaz de Usuario del Dashboard ---

st.title("📊 Necesidades tecnológicas")
st.markdown("Este dashboard visualiza la frecuencia de las dimensiones priorizadas en cada región piloto.")

# --- Definición de Nombres de Columnas ---
columna_ejes = "Ejes traccionantes/dimensiones priorizadas"
columna_region = "Región"
columna_tematica = "Temática específica"
columna_necesidad = "Necesidad/desafío tecnológico"
columna_categorias_tec = "Categorías Tecnológicas Principales"

# Lista de columnas requeridas para que la app funcione
columnas_requeridas = [columna_ejes, columna_region, columna_tematica, columna_necesidad, columna_categorias_tec]
for col in columnas_requeridas:
    if col not in df_necesidades.columns:
        st.error(f"Error: La columna requerida '{col}' no se encontró en la hoja 'db' del archivo Excel.")
        st.stop()

# --- Filtros Interactivos ---

st.sidebar.header("Filtros")
regiones_seleccionadas = st.sidebar.multiselect(
    "Selecciona una o más regiones para visualizar:",
    options=df_necesidades[columna_region].unique(),
    default=list(df_necesidades[columna_region].unique()) # Por defecto, todas seleccionadas
)

# --- Filtrado General de Datos ---
if regiones_seleccionadas:
    df_filtrado_general = df_necesidades[df_necesidades[columna_region].isin(regiones_seleccionadas)]
else:
    df_filtrado_general = df_necesidades.copy()

# --- Visualización de Gráficos en Columnas ---

col1, col2, col3 = st.columns(3)

# Definir un mapa de colores personalizado para mejorar la visibilidad
color_map = {
    'Maule': '#E45756',      # Rojo
    'Coquimbo': '#F0E442',   # Amarillo
    'Los Lagos': '#54A24B'   # Verde
}

with col1:
    with st.container(border=True):
        # --- Visualización del Gráfico de Radar ---
        st.subheader("Frecuencia de Ejes")
        
        # Procesamiento específico para el gráfico de radar
        df_counts = df_filtrado_general.groupby([columna_region, columna_ejes]).size().reset_index(name='Cantidad')
        all_ejes = df_filtrado_general[columna_ejes].unique()
        all_regiones_filtradas = df_filtrado_general[columna_region].unique()
        full_grid = pd.DataFrame(list(product(all_regiones_filtradas, all_ejes)), columns=[columna_region, columna_ejes])
        df_radar = pd.merge(full_grid, df_counts, on=[columna_region, columna_ejes], how='left').fillna(0)

        if not df_radar.empty:
            fig_radar = px.line_polar(
                df_radar, r='Cantidad', theta=columna_ejes, color=columna_region,
                color_discrete_map=color_map, line_close=True, markers=True,
                template="streamlit"
            )
            fig_radar.update_traces(fill='toself', opacity=0.4)
            fig_radar.update_layout(height=500, hoverlabel=dict(align='left'))
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.warning("Sin datos para el gráfico de radar.")

with col2:
    with st.container(border=True):
        # --- Visualización del Gráfico Solar ---
        st.subheader("Desglose de Temáticas")
        
        if not df_filtrado_general.empty:
            fig_sunburst = px.sunburst(
                df_filtrado_general, path=[columna_region, columna_ejes, columna_tematica],
                color=columna_region, color_discrete_map=color_map,
                template="streamlit"
            )
            fig_sunburst.update_traces(insidetextorientation='radial')
            fig_sunburst.update_layout(height=500, hoverlabel=dict(align='left'))
            st.plotly_chart(fig_sunburst, use_container_width=True)
        else:
            st.info("Sin datos para el gráfico solar.")

with col3:
    with st.container(border=True):
        # --- Visualización del Gráfico de Barras ---
        st.subheader("Frecuencia de Categorías")

        # Procesamiento para el gráfico de barras
        df_categorias = df_filtrado_general.dropna(subset=[columna_categorias_tec])
        if not df_categorias.empty:
            categorias = df_categorias[columna_categorias_tec].str.split(',').explode().str.strip()
            df_bar_counts = categorias.value_counts().reset_index()
            df_bar_counts.columns = ['Categoría', 'Frecuencia']
            
            # Crear una columna con etiquetas truncadas para el eje Y
            df_bar_counts['Etiqueta_Truncada'] = df_bar_counts['Categoría'].apply(lambda x: (x[:15] + '...') if len(x) > 15 else x)
            
            # Ordenar los datos para una mejor visualización horizontal
            df_bar_counts = df_bar_counts.sort_values('Frecuencia', ascending=True)

            fig_bar = px.bar(
                df_bar_counts, 
                y='Etiqueta_Truncada', # Usar etiquetas truncadas en el eje
                x='Frecuencia',
                orientation='h',
                color='Categoría', # Asignar un color por cada barra
                hover_name='Categoría', # Mostrar nombre completo al pasar el mouse
                template="streamlit"
            )
            # Ocultar la leyenda de colores (redundante) y ajustar layout
            fig_bar.update_layout(
                height=500, 
                hoverlabel=dict(align='left'),
                showlegend=False,
                yaxis_title=None # Ocultar el título del eje Y
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin datos para el gráfico de barras.")


# --- Visualización de la Tabla de Datos ---
with st.expander("Ver datos originales"):
    columnas_a_mostrar = [
        "Región",
        "Ejes traccionantes/dimensiones priorizadas",
        "Temática específica",
        "Necesidad/desafío tecnológico"
    ]
    
    columnas_existentes = [col for col in columnas_a_mostrar if col in df_filtrado_general.columns]
    
    if len(columnas_existentes) < len(columnas_a_mostrar):
        st.warning("Algunas de las columnas solicitadas no se encontraron en el archivo Excel.")
    
    st.dataframe(df_filtrado_general[columnas_existentes])
