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

# Definir un mapa de colores personalizado con tonos pastel
color_map = {
    'Maule': '#fbb4ae',      # Rojo Pastel
    'Coquimbo': '#fed9a6',   # Amarillo Pastel
    'Los Lagos': '#b3e2cd'   # Verde Pastel
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
            fig_radar.update_traces(fill='toself', opacity=0.5) # Aumentar un poco la opacidad para pasteles
            fig_radar.update_layout(height=400, hoverlabel=dict(align='left'))
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
            fig_sunburst.update_layout(height=400, hoverlabel=dict(align='left'))
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
                y='Categoría', # Usar la categoría original y única para el eje Y para evitar superposiciones
                x='Frecuencia',
                orientation='h',
                color='Frecuencia', # Asignar color según la frecuencia
                color_continuous_scale=px.colors.sequential.GnBu, # Paleta monocromática con buen contraste
                text='Frecuencia', # Añadir el valor numérico a cada barra
                hover_name='Categoría', # Mostrar nombre completo al pasar el mouse
                template="streamlit"
            )
            # Ocultar la leyenda de colores (redundante) y ajustar layout
            fig_bar.update_layout(
                height=400, 
                hoverlabel=dict(align='left'),
                coloraxis_showscale=False, # Ocultar la barra de escala de colores
                yaxis_title=None, # Ocultar el título del eje Y
                xaxis_visible=False # Ocultar el eje X (Frecuencia)
            )
            # Usar las etiquetas truncadas solo para la visualización del eje Y
            fig_bar.update_yaxes(ticktext=df_bar_counts['Etiqueta_Truncada'], tickvals=df_bar_counts['Categoría'])
            # Ajustar la posición y estilo del texto en las barras
            fig_bar.update_traces(textposition='outside', textfont_size=12)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin datos para el gráfico de barras.")


# --- Visualización de la Tabla de Datos ---
with st.expander("Ver datos originales"):
    columnas_a_mostrar = [
        "Región",
        "Ejes traccionantes/dimensiones priorizadas",
        "Temática específica",
        "Necesidad/desafío tecnológico",
        "Impacto potencial",
        "Nivel de innovación"
    ]
    
    df_display = df_filtrado_general[columnas_a_mostrar].copy()

    # Mapeo para Impacto Potencial (Azules)
    impacto_map = {
        5: "🔵 Alto",
        3: "🔷 Medio",
        1: "⚪ Bajo"
    }
    # Mapeo para Nivel de Innovación (Naranjos)
    innovacion_map = {
        5: "🟠 Alto",
        3: "🔶 Medio",
        1: "🔸 Bajo"
    }

    df_display[columna_impacto] = df_display[columna_impacto].map(impacto_map).fillna("N/A")
    df_display[columna_innovacion] = df_display[columna_innovacion].map(innovacion_map).fillna("N/A")
    
    st.dataframe(df_display)
