import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import load_and_validate_csv
from src.gemini_client import AgroSentimentAnalyzer
from src.firebase_manager import save_analysis_results, fetch_history

st.set_page_config(page_title="SAVA Agro-Insight", page_icon="🌱", layout="wide")

st.markdown("""
    <style>
    .stButton>button { background-color: #2ecc71; color: white; border: none; border-radius: 8px; }
    .reportview-container { background: #f0f2f6 }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1094/1094349.png", width=60)
    st.title("🚜 SAVA Software")
    st.caption("Inteligencia Artificial para el Agro")
    st.divider()
    if "firebase_credentials" in st.secrets:
        st.success("☁️ Nube Conectada")
    else:
        st.warning("☁️ Modo Local (Sin BD)")

def main():
    st.title("📊 Monitor de Riesgos Agroindustriales - R9")
    st.markdown("Sistema inteligente de clasificación de noticias para el Valle del Cauca.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📂 Análisis CSV", "🌐 Noticias en Vivo", "📈 Dashboard", "🗄️ Historial"])

    # Inicializamos el analizador
    analyzer = AgroSentimentAnalyzer()

    # --- TAB 1: ANÁLISIS CSV ---
    with tab1:
        uploaded_file = st.file_uploader("Sube tu Dataset (CSV)", type=["csv"])
        
        if uploaded_file:
            df, error = load_and_validate_csv(uploaded_file)
            
            if error:
                st.error(error)
            else:
                st.subheader("Vista Previa")
                st.dataframe(df[['titular', 'fecha']], use_container_width=True, hide_index=True)
                
                if st.button("🧠 Ejecutar Análisis Avanzado", type="primary"):
                    # CORRECCIÓN AQUÍ: Verificamos api_key en lugar de model
                    if analyzer.api_key:
                        with st.spinner('Identificando palabras clave y generando argumentos...'):
                            progress = st.progress(0)
                            sents, expls = analyzer.analyze_batch(df, progress)
                            
                            df['sentimiento_ia'] = sents
                            df['explicacion_ia'] = expls
                            
                            st.session_state['last_analysis'] = df
                            st.success("¡Análisis Inteligente Completado!")
                    else:
                        st.error("Error: No se encontró la API Key de Gemini en los secretos.")

        if 'last_analysis' in st.session_state:
            df_res = st.session_state['last_analysis']
            st.divider()
            
            st.subheader("Resultados Clasificados")
            
            for index, row in df_res.iterrows():
                color = "gray"
                if row['sentimiento_ia'] == 'Positivo': color = "green"
                elif row['sentimiento_ia'] == 'Negativo': color = "red"
                
                with st.expander(f":{color}[{row['sentimiento_ia']}] - {row['titular']}"):
                    st.write(f"**Argumento IA:** {row['explicacion_ia']}")
                    st.caption(f"Fecha: {row['fecha']} | ID: {row['id_original']}")

            if st.button("💾 Guardar Resultados en Firebase", key="btn_save_csv"):
                success, msg = save_analysis_results(df_res)
                if success: st.success(msg)
                else: st.error(msg)

    # --- TAB 2: BÚSQUEDA WEB ---
    with tab2:
        st.header("🔍 Radar de Noticias en Tiempo Real")
        st.markdown("Busca eventos recientes en la web y clasifícalos al instante.")
        
        col_search, col_btn = st.columns([3, 1])
        with col_search:
            query = st.text_input("Tema de búsqueda", value="Sector agroindustria Valle del Cauca")
        with col_btn:
            st.write("") 
            st.write("") 
            search_trigger = st.button("Buscar y Analizar", use_container_width=True)
            
        if search_trigger:
            with st.spinner(f"Buscando '{query}' en la web y analizando con IA..."):
                web_results = analyzer.search_and_analyze_web(query=query)
                
                if web_results:
                    df_web = pd.DataFrame(web_results)
                    st.session_state['web_analysis'] = df_web
                    st.success(f"Se encontraron {len(df_web)} noticias relevantes.")
                else:
                    st.warning("No se encontraron noticias recientes o hubo un error en la búsqueda.")

        if 'web_analysis' in st.session_state:
            df_web = st.session_state['web_analysis']
            
            for index, row in df_web.iterrows():
                s_color = "🟢" if row['sentimiento_ia'] == 'Positivo' else "🔴" if row['sentimiento_ia'] == 'Negativo' else "⚪"
                
                st.markdown(f"""
                <div style="background-color:white; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid {'#2ecc71' if row['sentimiento_ia']=='Positivo' else '#e74c3c' if row['sentimiento_ia']=='Negativo' else '#bdc3c7'}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4>{s_color} {row['titular']}</h4>
                    <p style="font-size:0.9em;">{row['cuerpo'][:200]}...</p>
                    <p><b>🤖 Por qué:</b> {row['explicacion_ia']}</p>
                    <small>Fuente: {row['fuente']} | <a href="{row['url']}" target="_blank">Leer original</a></small>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("💾 Guardar Noticias Web en Firebase", key="btn_save_web"):
                success, msg = save_analysis_results(df_web, collection_name="noticias_web_tiempo_real")
                if success: st.success(msg)

    # --- TAB 3: DASHBOARD ---
    with tab3:
        data_source = None
        if 'last_analysis' in st.session_state:
            data_source = st.session_state['last_analysis']
            st.caption("Mostrando datos del archivo CSV cargado.")
        elif 'web_analysis' in st.session_state:
            data_source = st.session_state['web_analysis']
            st.caption("Mostrando datos de la búsqueda Web reciente.")
            
        if data_source is not None:
            col1, col2, col3 = st.columns(3)
            total = len(data_source)
            pos = len(data_source[data_source['sentimiento_ia'] == 'Positivo'])
            neg = len(data_source[data_source['sentimiento_ia'] == 'Negativo'])
            
            col1.metric("Noticias Analizadas", total)
            col2.metric("Positivas", pos)
            col3.metric("Negativas", neg)
            
            fig = px.pie(data_source, names='sentimiento_ia', 
                         color='sentimiento_ia',
                         color_discrete_map={'Positivo':'#2ecc71', 'Negativo':'#e74c3c', 'Neutro':'#bdc3c7'},
                         hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Realiza un análisis (CSV o Web) para ver el Dashboard.")

    # --- TAB 4: HISTORIAL ---
    with tab4:
        if st.button("🔄 Cargar Historial Completo"):
            hist = fetch_history()
            if hist:
                st.dataframe(pd.DataFrame(hist))
            else:
                st.write("No hay historial disponible.")

if __name__ == "__main__":
    main()
