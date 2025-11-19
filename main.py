import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import load_and_validate_csv
from src.gemini_client import AgroSentimentAnalyzer
from src.firebase_manager import save_analysis_results, fetch_history

st.set_page_config(page_title="SAVA Agro-Insight", page_icon="🌱", layout="wide")

# CSS Limpio
st.markdown("""
    <style>
    .stButton>button { background-color: #2ecc71; color: white; border: none; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🚜 SAVA Software")
    st.info("Sistema de Alertas Agroindustriales")
    if "firebase_credentials" in st.secrets:
        st.success("Conexión Cloud: Activa")
    else:
        st.warning("Conexión Cloud: Pendiente")

def main():
    st.title("📊 Monitor de Sentimiento Agro - Valle del Cauca")
    
    tab1, tab2, tab3 = st.tabs(["📂 Cargar y Analizar", "📈 Dashboard", "☁️ Base de Datos"])

    # --- TAB 1: ANÁLISIS ---
    with tab1:
        uploaded_file = st.file_uploader("Sube el archivo CSV (Dataset R9)", type=["csv"])
        
        if uploaded_file:
            df, error = load_and_validate_csv(uploaded_file)
            
            if error:
                st.error(error)
            else:
                # Mostrar dataframe limpio, ocultando el índice de Pandas para evitar confusión
                st.subheader("1. Datos Detectados")
                st.dataframe(
                    df[['id_original', 'titular', 'fecha']], 
                    use_container_width=True,
                    hide_index=True
                )
                
                if st.button("🤖 Iniciar Análisis IA", type="primary"):
                    analyzer = AgroSentimentAnalyzer()
                    
                    if analyzer.model:
                        with st.spinner('Analizando riesgos y oportunidades...'):
                            progress = st.progress(0)
                            results = analyzer.analyze_batch(df, progress)
                            df['sentimiento_ia'] = results
                            st.session_state['last_analysis'] = df
                            st.success("¡Análisis finalizado!")
                    else:
                        st.error("Error de configuración de API Key")

        # Mostrar resultados si existen en memoria
        if 'last_analysis' in st.session_state:
            df_res = st.session_state['last_analysis']
            st.divider()
            st.subheader("2. Resultados del Análisis")
            
            # Tabla interactiva con colores según sentimiento
            st.dataframe(
                df_res[['id_original', 'sentimiento_ia', 'titular']],
                use_container_width=True,
                hide_index=True
            )
            
            # Botón Guardar en Firebase
            col_btn, _ = st.columns([1, 3])
            with col_btn:
                if st.button("💾 Guardar en Base de Datos"):
                    with st.spinner("Sincronizando con Firebase..."):
                        success, msg = save_analysis_results(df_res)
                        if success:
                            st.balloons()
                            st.success(msg)
                        else:
                            st.error(msg)

    # --- TAB 2: DASHBOARD ---
    with tab2:
        if 'last_analysis' in st.session_state:
            df_viz = st.session_state['last_analysis']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Noticias", len(df_viz))
            c2.metric("Positivas", len(df_viz[df_viz['sentimiento_ia'] == 'Positivo']))
            c3.metric("Negativas", len(df_viz[df_viz['sentimiento_ia'] == 'Negativo']))
            
            fig = px.pie(df_viz, names='sentimiento_ia', title="Distribución de Sentimiento",
                         color='sentimiento_ia',
                         color_discrete_map={'Positivo':'#2ecc71', 'Negativo':'#e74c3c', 'Neutro':'#bdc3c7'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Realiza un análisis primero para ver las métricas.")

    # --- TAB 3: HISTORIAL ---
    with tab3:
        if st.button("🔄 Refrescar Historial"):
            data = fetch_history()
            if data:
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.info("No hay datos históricos aún.")

if __name__ == "__main__":
    main()
