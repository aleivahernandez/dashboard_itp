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
        # Limpiar espacios extra en los nombres de las columnas
        df.columns = df.columns.str.strip()
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
columna_impacto = "Impacto potencial"
columna_innovacion = "Nivel de innovación"


# Lista de columnas requeridas para que la app funcione
columnas_requeridas = [columna_ejes, columna_region, columna_tematica, columna_necesidad, columna_categorias_tec, columna_impacto, columna_innovacion]
for col in columnas_requeridas:
    if col not in df_necesidades.columns:
        st.error(f"Error: La columna requerida '{col}' no se encontró en la hoja 'db' del archivo Excel.")
        # Mensaje de depuración mejorado: muestra las columnas que SÍ se encontraron
        st.warning(f"Las columnas encontradas en el archivo son: {list(df_necesidades.columns)}")
        st.info("Sugerencia: Verifica que el nombre de la columna en el archivo Excel sea exactamente igual (incluyendo mayúsculas y espacios). Si acabas de subir el archivo, intenta limpiar la caché de la app (Manage app -> Clear cache).")
        st.stop()

# --- Filtros Interactivos ---

st.sidebar.image("logo.png", width=100) # Ajustar el ancho del logo
st.sidebar.header("Filtros")
regiones_seleccionadas = st.sidebar.multiselect(
    "Filtrar por Región:",
    options=df_necesidades[columna_region].unique(),
    default=list(df_necesidades[columna_region].unique()) # Por defecto, todas seleccionadas
)

# Obtener todas las categorías tecnológicas únicas para el nuevo filtro
all_categorias = sorted(df_necesidades[columna_categorias_tec].str.split(',').explode().str.strip().unique())

categorias_seleccionadas = st.sidebar.multiselect(
    "Filtrar por Categoría Tecnológica:",
    options=all_categorias,
    default=[] # Por defecto, ninguna seleccionada
)


# --- Filtrado General de Datos ---
if regiones_seleccionadas:
    df_filtrado_general = df_necesidades[df_necesidades[columna_region].isin(regiones_seleccionadas)]
else:
    df_filtrado_general = df_necesidades.copy()

# Aplicar el segundo filtro de categorías tecnológicas si se ha seleccionado alguna
if categorias_seleccionadas:
    # Se itera sobre cada categoría seleccionada para construir una máscara booleana.
    # Esto asegura que la búsqueda sea por contenido ("contains") y no por coincidencia exacta.
    mask = df_filtrado_general[columna_categorias_tec].apply(
        lambda x: any(cat in str(x) for cat in categorias_seleccionadas)
    )
    df_filtrado_general = df_filtrado_general[mask]


# --- Visualización de Gráficos en Columnas ---

col1, col2, col3 = st.columns(3)

# Definir un mapa de colores personalizado con tonos pastel
color_map = {
    'Maule': '#fbb4ae',      # Rojo Pastel
    'Coquimbo': '#fed9a6',   # Amarillo Pastel
    'Los Lagos': '#b3e2cd',  # Verde Pastel
    'Total': '#b19cd9'       # Morado Pastel
}

with col1:
    with st.container(border=True):
        # --- Visualización del Gráfico de Radar ---
        st.subheader("Frecuencia de Ejes")
        
        if not df_filtrado_general.empty:
            # Procesamiento específico para el gráfico de radar
            df_counts = df_filtrado_general.groupby([columna_region, columna_ejes]).size().reset_index(name='Cantidad')
            all_ejes = df_filtrado_general[columna_ejes].unique()
            all_regiones_filtradas = df_filtrado_general[columna_region].unique()
            full_grid = pd.DataFrame(list(product(all_regiones_filtradas, all_ejes)), columns=[columna_region, columna_ejes])
            df_radar = pd.merge(full_grid, df_counts, on=[columna_region, columna_ejes], how='left').fillna(0)

            # Calcular el total para las regiones seleccionadas
            if not df_radar.empty:
                df_total_raw = df_radar.groupby(columna_ejes, as_index=False)['Cantidad'].sum()
                # Asegurar que el total tenga todos los ejes para una línea continua
                all_ejes_df = pd.DataFrame({columna_ejes: all_ejes})
                df_total = pd.merge(all_ejes_df, df_total_raw, on=columna_ejes, how='left').fillna(0)
                df_total[columna_region] = 'Total'
                # Combinar datos de regiones con el total
                df_para_grafico = pd.concat([df_radar, df_total], ignore_index=True)
            else:
                df_para_grafico = df_radar

            if not df_para_grafico.empty:
                fig_radar = px.line_polar(
                    df_para_grafico, r='Cantidad', theta=columna_ejes, color=columna_region,
                    color_discrete_map=color_map, line_close=True, markers=True,
                    template="streamlit"
                )
                fig_radar.update_traces(fill='toself', opacity=0.5)
                fig_radar.update_layout(height=500, hoverlabel=dict(align='left'))
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.warning("Sin datos para el gráfico de radar con los filtros actuales.")
        else:
            st.warning("Sin datos para mostrar con los filtros seleccionados.")


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
            st.info("Sin datos para el gráfico solar con los filtros actuales.")

with col3:
    with st.container(border=True):
        # --- Visualización del Gráfico de Barras ---
        st.subheader("Frecuencia de Categorías")

        if not df_filtrado_general.empty:
            df_categorias = df_filtrado_general.dropna(subset=[columna_categorias_tec])
            categorias = df_categorias[columna_categorias_tec].str.split(',').explode().str.strip()
            df_bar_counts = categorias.value_counts().reset_index()
            df_bar_counts.columns = ['Categoría', 'Frecuencia']
            
            df_bar_counts['Etiqueta_Truncada'] = df_bar_counts['Categoría'].apply(lambda x: (x[:15] + '...') if len(x) > 15 else x)
            df_bar_counts = df_bar_counts.sort_values('Frecuencia', ascendi
