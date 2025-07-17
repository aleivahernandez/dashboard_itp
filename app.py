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
columna_necesidad = "Necesidad/desafío tecnológico"

if columna_ejes not in df_necesidades.columns or columna_region not in df_necesidades.columns:
    st.error(f"El archivo Excel debe contener las columnas '{columna_ejes}' y '{columna_region}'.")
    st.stop()

# Agrupar por región y por eje para contar la frecuencia de cada uno
df_counts = df_necesidades.groupby([columna_region, columna_ejes]).size().reset_index(name='Cantidad')

# --- CREACIÓN DE DATOS COMPLETOS PARA LÍNEAS CONTINUAS ---
# Obtener todas las categorías únicas para los ejes y las regiones
all_ejes = df_necesidades[columna_ejes].unique()
all_regiones = df_necesidades[columna_region].unique()

# Crear una grilla con todas las combinaciones posibles de región y eje
full_grid = pd.DataFrame(list(product(all_regiones, all_ejes)), columns=[columna_region, columna_ejes])

# Unir la grilla completa con los conteos reales
df_radar = pd.merge(
    full_grid,
    df_counts,
    on=[columna_region, columna_ejes],
    how='left'
)

# Rellenar con 0 las combinaciones que no tenían datos
df_radar['Cantidad'] = df_radar['Cantidad'].fillna(0)


# --- Filtros Interactivos ---

st.sidebar.header("Filtros")
regiones_seleccionadas = st.sidebar.multiselect(
    "Selecciona una o más regiones para visualizar:",
    options=df_radar[columna_region].unique(),
    default=list(df_radar[columna_region].unique()) # Por defecto, todas seleccionadas
)

# Filtrar el dataframe del radar basado en la selección
if regiones_seleccionadas:
    df_filtrado_radar = df_radar[df_radar[columna_region].isin(regiones_seleccionadas)]
else:
    df_filtrado_radar = df_radar.copy()

# --- Visualización de Gráficos en Columnas ---

col1, col2 = st.columns(2)

with col1:
    # --- Visualización del Gráfico de Radar ---
    st.subheader("Frecuencia de Dimensiones")

    if not df_filtrado_radar.empty:
        # Definir un mapa de colores personalizado para mejorar la visibilidad
        color_map = {
            'Maule': '#E45756',      # Rojo
            'Coquimbo': '#4C78A8',   # Azul
            'Los Lagos': '#54A24B'   # Verde
        }

        fig_radar = px.line_polar(
            df_filtrado_radar,
            r='Cantidad',
            theta=columna_ejes,
            color=columna_region,
            color_discrete_map=color_map,
            line_close=True,
            markers=True,
            title="Comparativa de Ejes Priorizados por Región"
        )
        fig_radar.update_traces(fill='toself', opacity=0.4)
        fig_radar.update_layout(height=600)
        st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.warning("Selecciona al menos una región para ver el gráfico de radar.")

with col2:
    # --- Visualización del Gráfico Solar ---
    st.subheader("Desglose de Necesidades")

    if columna_necesidad not in df_necesidades.columns:
        st.warning(f"La columna '{columna_necesidad}' no se encontró.")
    else:
        if regiones_seleccionadas:
            df_sunburst_filtrado = df_necesidades[df_necesidades[columna_region].isin(regiones_seleccionadas)]
        else:
            df_sunburst_filtrado = df_necesidades.copy()
        
        if not df_sunburst_filtrado.empty:
            fig_sunburst = px.sunburst(
                df_sunburst_filtrado,
                path=[columna_region, columna_ejes, columna_necesidad],
                color=columna_region, # Aplicar color por región
                color_discrete_map=color_map, # Usar el mismo mapa de colores
                title="Desglose de Necesidades por Región y Eje"
            )
            # Forzar que todo el texto DENTRO de los sectores se muestre de manera horizontal
            fig_sunburst.update_traces(insidetextorientation='horizontal')
            fig_sunburst.update_layout(height=600)
            st.plotly_chart(fig_sunburst, use_container_width=True)
        else:
            st.info("No hay datos para mostrar en el gráfico solar con los filtros seleccionados.")

# --- Visualización de la Tabla de Datos ---

with st.expander("Ver datos originales"):
    columnas_a_mostrar = [
        "Región",
        "Ejes traccionantes/dimensiones priorizadas",
        "Necesidad/desafío tecnológico",
        "Contexto tecnológico preliminar"
    ]
    
    columnas_existentes = [col for col in columnas_a_mostrar if col in df_necesidades.columns]
    
    if len(columnas_existentes) < len(columnas_a_mostrar):
        st.warning("Algunas de las columnas solicitadas no se encontraron en el archivo Excel.")
    
    if regiones_seleccionadas:
        df_tabla_filtrada = df_necesidades[df_necesidades[columna_region].isin(regiones_seleccionadas)]
    else:
        df_tabla_filtrada = df_necesidades

    st.dataframe(df_tabla_filtrada[columnas_existentes])
