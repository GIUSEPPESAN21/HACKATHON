import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import load_and_validate_csv
from src.gemini_client import AgroSentimentAnalyzer
from src.firebase_manager import save_analysis_results, fetch_history

# --- Configuración de Página ---
st.set_page_config(
    page_title="SAVA Agro-Insight",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS personalizados para Agro-tech ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f6;
    }
    .stButton>button {
        background-color: #2ecc71;
        color: white;
        border-radius: 10px;
        border: none;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1094/1094349.png", width=80) # Icono genérico de agricultura
    st.title("SAVA Software")
    st.caption("Hackathon Talento Tech R9")
    st.divider()
    st.info("Sistema de Inteligencia de Datos para el Agro")
    st.markdown("---")
    st.write("**Estado del Sistema:**")
    if "firebase" in st.secrets:
        st.success("🔥 Firebase: Configurado")
    else:
        st.error("🔥 Firebase: Sin Configuración")
        
    if "gemini" in st.secrets:
        st.success("🤖 Gemini AI: Configurado")
    else:
        st.error("🤖 Gemini AI: Sin Configuración")

# --- Lógica Principal ---
def main():
    st.title("📊 Panel de Control - Análisis de Sentimiento Agro")
    st.markdown("Cargue noticias del sector para identificar riesgos y oportunidades en el Valle del Cauca.")

    tab1, tab2, tab3 = st.tabs(["📤 Carga y Análisis", "📈 Dashboard", "🗄️ Historial Cloud"])

    # --- TAB 1: Carga ---
    with tab1:
        uploaded_file = st.file_uploader("Subir archivo CSV (Dataset R9)", type=["csv"])
        
        if uploaded_file is not None:
            df, error = load_and_validate_csv(uploaded_file)
            
            if error:
                st.error(error)
            else:
                st.subheader("Vista Previa de Datos")
                st.dataframe(df.head(5), use_container_width=True)
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    analyze_btn = st.button("🚀 Analizar con IA", use_container_width=True)
                
                if analyze_btn:
                    analyzer = AgroSentimentAnalyzer()
                    
                    if not analyzer.model:
                        st.error("No se puede iniciar el análisis: API Key faltante.")
                    else:
                        with st.spinner('Gemini está leyendo las noticias... (Esto puede tardar unos segundos)'):
                            # Barra de progreso
                            progress_bar = st.progress(0)
                            
                            # Ejecutar Análisis
                            results = analyzer.analyze_batch(df, progress_bar)
                            df['sentimiento_ia'] = results
                            
                            st.success("✅ Análisis Completado")
                            
                            # Guardar en Session State para no perder al recargar
                            st.session_state['last_analysis'] = df
                            
                            # Mostrar resultados
                            st.dataframe(df[['titular', 'sentimiento_ia', 'fecha']], use_container_width=True)
                            
                            # Botón de guardado en base de datos
                            if st.button("💾 Guardar Resultados en Firebase"):
                                success, msg = save_analysis_results(df)
                                if success:
                                    st.balloons()
                                    st.success(msg)
                                else:
                                    st.error(msg)

    # --- TAB 2: Dashboard ---
    with tab2:
        if 'last_analysis' in st.session_state:
            df_viz = st.session_state['last_analysis']
            
            col_a, col_b, col_c = st.columns(3)
            total = len(df_viz)
            pos = len(df_viz[df_viz['sentimiento_ia'] == 'Positivo'])
            neg = len(df_viz[df_viz['sentimiento_ia'] == 'Negativo'])
            
            col_a.metric("Total Noticias", total)
            col_b.metric("Oportunidades (Pos)", pos, delta_color="normal")
            col_c.metric("Riesgos (Neg)", neg, delta_color="inverse")
            
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Distribución de Sentimientos")
                fig = px.pie(df_viz, names='sentimiento_ia', 
                             color='sentimiento_ia',
                             color_discrete_map={'Positivo':'#2ecc71', 'Negativo':'#e74c3c', 'Neutro':'#95a5a6'},
                             hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                st.subheader("Cronología de Noticias")
                # Asegurar formato fecha para gráfico
                try:
                    df_viz['fecha_dt'] = pd.to_datetime(df_viz['fecha'], dayfirst=True, errors='coerce')
                    df_viz = df_viz.dropna(subset=['fecha_dt'])
                    df_count = df_viz.groupby(['fecha_dt', 'sentimiento_ia']).size().reset_index(name='conteo')
                    
                    fig2 = px.bar(df_count, x='fecha_dt', y='conteo', color='sentimiento_ia',
                                  color_discrete_map={'Positivo':'#2ecc71', 'Negativo':'#e74c3c', 'Neutro':'#95a5a6'})
                    st.plotly_chart(fig2, use_container_width=True)
                except:
                    st.warning("No se pudo procesar las fechas para el gráfico temporal.")
                    
        else:
            st.info("Ejecuta un análisis primero para ver el Dashboard.")

    # --- TAB 3: Historial ---
    with tab3:
        st.subheader("Registros en la Nube (Firestore)")
        if st.button("🔄 Actualizar Historial"):
            history_data = fetch_history()
            if history_data:
                df_hist = pd.DataFrame(history_data)
                st.dataframe(df_hist, use_container_width=True)
            else:
                st.warning("No hay datos o no hay conexión.")

if __name__ == "__main__":
    main()
