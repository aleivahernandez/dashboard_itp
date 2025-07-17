# -----------------------------------------------------------------------------
# app.py - Dashboard con Gráfico de Radar y Cross-Filtering
# -----------------------------------------------------------------------------
# Importación de librerías necesarias
import streamlit as st
import pandas as pd
import plotly.express as px
from itertools import product
from streamlit_plotly_events import plotly_events

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
        df = pd.read_excel(archivo_excel, sheet_name="db", engine='openpyxl')
        df.columns = df.columns.str.strip()
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

st.title("📊 Necesidades tecnológicas")
st.markdown("Haz clic en una región en los gráficos para filtrar todo el dashboard. Usa el botón para limpiar la selección.")

# --- Definición de Nombres de Columnas ---
columna_ejes = "Ejes traccionantes/dimensiones priorizadas"
columna_region = "Región"
columna_tematica = "Temática específica"
columna_necesidad = "Necesidad/desafío tecnológico"
columna_categorias_tec = "Categorías Tecnológicas Principales"
columna_impacto = "Impacto potencial"
columna_innovacion = "Nivel de innovación"

# --- Gestión del Estado del Filtro ---
if 'region_seleccionada' not in st.session_state:
    st.session_state.region_seleccionada = None

# Botón para limpiar el filtro
if st.button("Limpiar Filtro de Región"):
    st.session_state.region_seleccionada = None
    st.rerun()

# --- Filtrado General de Datos ---
if st.session_state.region_seleccionada:
    df_filtrado_general = df_necesidades[df_necesidades[columna_region] == st.session_state.region_seleccionada]
    st.info(f"Mostrando datos para: **{st.session_state.region_seleccionada}**")
else:
    df_filtrado_general = df_necesidades.copy()


# --- Visualización de Gráficos en Columnas ---

col1, col2, col3 = st.columns(3)

# Definir un mapa de colores personalizado con tonos pastel
color_map = {
    'Maule': '#fbb4ae',
    'Coquimbo': '#fed9a6',
    'Los Lagos': '#b3e2cd',
    'Total': '#c5b0d5'
}

with col1:
    with st.container(border=True):
        st.subheader("Frecuencia de Ejes")
        
        # Procesamiento para el gráfico de radar
        df_para_grafico_radar = pd.DataFrame()
        if not df_necesidades.empty:
            df_counts_region = df_necesidades.groupby([columna_region, columna_ejes]).size().reset_index(name='Cantidad')
            all_ejes = df_necesidades[columna_ejes].unique()
            all_regiones = df_necesidades[columna_region].unique()
            full_grid_region = pd.DataFrame(list(product(all_regiones, all_ejes)), columns=[columna_region, columna_ejes])
            df_radar_regions = pd.merge(full_grid_region, df_counts_region, on=[columna_region, columna_ejes], how='left').fillna(0)
            df_para_grafico_radar = pd.concat([df_para_grafico_radar, df_radar_regions])

            df_counts_total = df_necesidades.groupby(columna_ejes).size().reset_index(name='Cantidad')
            all_ejes_df = pd.DataFrame({columna_ejes: all_ejes})
            df_total = pd.merge(all_ejes_df, df_counts_total, on=columna_ejes, how='left').fillna(0)
            df_total[columna_region] = 'Total'
            df_para_grafico_radar = pd.concat([df_para_grafico_radar, df_total], ignore_index=True)

        if not df_para_grafico_radar.empty:
            # Filtrar los datos del radar según la selección de estado
            if st.session_state.region_seleccionada:
                # Mostrar solo la región seleccionada y el total
                df_radar_filtrado_display = df_para_grafico_radar[df_para_grafico_radar[columna_region].isin([st.session_state.region_seleccionada, 'Total'])]
            else:
                df_radar_filtrado_display = df_para_grafico_radar

            fig_radar = px.line_polar(
                df_radar_filtrado_display, r='Cantidad', theta=columna_ejes, color=columna_region,
                color_discrete_map=color_map, line_close=True, markers=True, template="streamlit"
            )
            fig_radar.update_traces(fill='toself', opacity=0.5)
            fig_radar.update_layout(height=500, hoverlabel=dict(align='left'))
            
            # Capturar evento de clic en el gráfico de radar
            selected_radar = plotly_events(fig_radar, click_event=True, key="radar_chart")
            if selected_radar:
                clicked_trace_name = fig_radar.data[selected_radar[0]['curveNumber']].name
                if clicked_trace_name != 'Total':
                    st.session_state.region_seleccionada = clicked_trace_name
                    st.rerun()

with col2:
    with st.container(border=True):
        st.subheader("Desglose de Temáticas")
        
        if not df_necesidades.empty:
            fig_sunburst = px.sunburst(
                df_filtrado_general, path=[columna_region, columna_ejes, columna_tematica],
                color=columna_region, color_discrete_map=color_map, template="streamlit"
            )
            fig_sunburst.update_traces(insidetextorientation='radial')
            fig_sunburst.update_layout(height=500, hoverlabel=dict(align='left'))
            
            # Capturar evento de clic en el gráfico solar
            selected_sunburst = plotly_events(fig_sunburst, click_event=True, key="sunburst_chart")
            if selected_sunburst and selected_sunburst[0].get('path'):
                clicked_region = selected_sunburst[0]['path'][0]
                st.session_state.region_seleccionada = clicked_region
                st.rerun()

with col3:
    with st.container(border=True):
        st.subheader("Frecuencia de Categorías")

        if not df_filtrado_general.empty:
            df_categorias = df_filtrado_general.dropna(subset=[columna_categorias_tec])
            if not df_categorias.empty:
                categorias = df_categorias[columna_categorias_tec].str.split(',').explode().str.strip()
                df_bar_counts = categorias.value_counts().reset_index()
                df_bar_counts.columns = ['Categoría', 'Frecuencia']
                
                df_bar_counts['Etiqueta_Truncada'] = df_bar_counts['Categoría'].apply(lambda x: (x[:15] + '...') if len(x) > 15 else x)
                df_bar_counts = df_bar_counts.sort_values('Frecuencia', ascending=True)

                fig_bar = px.bar(
                    df_bar_counts, y='Categoría', x='Frecuencia', orientation='h',
                    color='Frecuencia', color_continuous_scale=px.colors.sequential.GnBu,
                    text='Frecuencia', hover_name='Categoría', template="streamlit"
                )
                fig_bar.update_layout(
                    height=500, hoverlabel=dict(align='left'), coloraxis_showscale=False,
                    yaxis_title=None, xaxis_visible=False
                )
                fig_bar.update_yaxes(ticktext=df_bar_counts['Etiqueta_Truncada'], tickvals=df_bar_counts['Categoría'])
                fig_bar.update_traces(textposition='outside', textfont_size=12)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sin datos de categorías para los filtros actuales.")
        else:
            st.info("Sin datos para el gráfico de barras con los filtros actuales.")

# --- Visualización de la Tabla de Datos ---
with st.expander("Ver datos originales"):
    columnas_a_mostrar = [
        "Región", "Ejes traccionantes/dimensiones priorizadas", "Temática específica",
        "Necesidad/desafío tecnológico", "Impacto potencial", "Nivel de innovación"
    ]
    
    df_display = df_filtrado_general[columnas_a_mostrar].copy()

    impacto_map = { 5: "🔵 Alto", 3: "🔷 Medio", 1: "⚪ Bajo" }
    innovacion_map = { 5: "🟠 Alto", 3: "🔶 Medio", 1: "🔸 Bajo" }

    df_display[columna_impacto] = df_display[columna_impacto].map(impacto_map).fillna("N/A")
    df_display[columna_innovacion] = df_display[columna_innovacion].map(innovacion_map).fillna("N/A")
    
    st.dataframe(df_display)
