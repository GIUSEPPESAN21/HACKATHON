# Estructura base sugerida para el archivo principal de Streamlit
# Esto acelera el inicio del Sprint 0

import streamlit as st
import pandas as pd
import plotly.express as px
# import firebase_admin (Configurar después)

# Configuración de página
st.set_page_config(
    page_title="SAVA Agro-Insight",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MÓDULO 1: INGESTA DE DATOS (Jaime) ---
@st.cache_data
def load_data():
    # Cargar el dataset proporcionado
    df = pd.read_csv("IAR_Dataset_H4_R9.csv", sep=";")
    
    # Limpieza básica para Ing. Industrial (Estandarización)
    df['Fecha Publicación'] = pd.to_datetime(df['Fecha Publicación'], dayfirst=True, errors='coerce')
    return df

# Cargar datos
try:
    df = load_data()
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# --- SIDEBAR: FILTROS ESTRATÉGICOS (Joseph/Jaime) ---
st.sidebar.image("image_fb3b4a.png", use_column_width=True) # Logo SAVA
st.sidebar.header("Panel de Control")

# Filtro de Fecha
min_date = df['Fecha Publicación'].min()
max_date = df['Fecha Publicación'].max()
date_range = st.sidebar.date_input("Rango de Análisis", [min_date, max_date])

# Filtro de Sentimiento (Clave para detectar riesgos)
sentiment_filter = st.sidebar.multiselect(
    "Filtro de Sentimiento",
    options=df['Sentimiento'].unique(),
    default=df['Sentimiento'].unique()
)

# Filtrar DataFrame
mask = (
    (df['Fecha Publicación'].dt.date >= date_range[0]) &
    (df['Fecha Publicación'].dt.date <= date_range[1]) &
    (df['Sentimiento'].isin(sentiment_filter))
)
df_filtered = df[mask]

# --- DASHBOARD PRINCIPAL ---
st.title("🌱 SAVA Agro-Insight: Inteligencia Estratégica")
st.markdown("""
> **Visión de Ingeniería:** Transformando datos no estructurados en decisiones logísticas y operativas para el agro.
""")

# KPI Cards
c1, c2, c3 = st.columns(3)
c1.metric("Noticias Analizadas", len(df_filtered))
c2.metric("Alertas de Riesgo (Negativo)", len(df_filtered[df_filtered['Sentimiento'] == 'Negativo']))
sources_count = df_filtered['Fuente'].nunique()
c3.metric("Fuentes de Información", sources_count)

# Visualización de Tendencias
st.subheader("📉 Tendencia de Sentimiento en el Tiempo")
if not df_filtered.empty:
    fig_trend = px.histogram(
        df_filtered, 
        x="Fecha Publicación", 
        color="Sentimiento", 
        barmode="group",
        color_discrete_map={"Positivo": "green", "Negativo": "red", "Neutro": "gray"},
        title="Evolución Temporal de Noticias"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.warning("No hay datos para los filtros seleccionados")

# --- MÓDULO AI (Placeholder para Sprint 2) ---
st.divider()
st.subheader("🤖 Análisis de IA Generativa")

if st.button("Generar Resumen Estratégico"):
    with st.spinner("Consultando motor de IA SAVA..."):
        # Aquí iría la llamada a la API (Gemini/OpenAI)
        # prompt = f"Analiza estos titulares: {df_filtered['Titular de la Noticia'].tolist()}"
        st.success("Análisis Completado")
        st.info("**Recomendación Operativa:** Se detecta un aumento en noticias sobre plagas y sequía. Se recomienda activar protocolos de contingencia en la cadena de suministro y revisar stock de insumos fitosanitarios.")

# --- TABLA DE DATOS ---
st.subheader("📋 Detalle de Noticias")
st.dataframe(
    df_filtered[['Fecha Publicación', 'Titular de la Noticia', 'Fuente', 'Sentimiento']],
    hide_index=True,
    use_container_width=True
)
