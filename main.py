"""
SAVA Agro-Insight V2.0 - Sistema Profesional de Análisis de Sentimiento
Interfaz mejorada con todas las funcionalidades avanzadas
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import folium_static
import altair as alt

# Imports de módulos propios
from src.utils import load_and_validate_csv
from src.gemini_client import AgroSentimentAnalyzer
from src.firebase_manager import save_analysis_results, fetch_history
from src.cache_manager import CacheManager
from src.geo_mapper import NewsGeoMapper
from src.chatbot_rag import AgriNewsBot
from src.trend_analyzer import TrendAnalyzer
from src.alert_system import AlertSystem
from src.export_manager import ReportExporter

# Configuración de página MEJORADA
st.set_page_config(
    page_title="SAVA Agro-Insight Pro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS PROFESIONAL MEJORADO
st.markdown("""
    <style>
    /* Tema general */
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    
    /* Botones premium */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Métricas mejoradas */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
        color: #2c3e50;
    }
    
    /* Tarjetas con sombra */
    .css-1r6slb0 {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    
    /* Sidebar premium */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
        color: white;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: white;
        border-radius: 10px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Alerts personalizadas */
    .alert-critical {
        background-color: #fee;
        border-left: 5px solid #e74c3c;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .alert-high {
        background-color: #fff3cd;
        border-left: 5px solid #f39c12;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .alert-medium {
        background-color: #e7f3ff;
        border-left: 5px solid #3498db;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        animation: fadeIn 0.3s;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }
    .bot-message {
        background: white;
        border: 1px solid #e0e0e0;
        margin-right: 20%;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Progress bar mejorado */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar MEJORADO
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1094/1094349.png", width=80)
    st.title("🌱 SAVA Software")
    st.markdown("### *Agro-Insight Pro v2.0*")
    st.markdown("---")
    
    # Estado de conexión
    col_firebase, col_cache = st.columns(2)
    with col_firebase:
        if "firebase_credentials" in st.secrets:
            st.success("☁️ Cloud")
        else:
            st.warning("💾 Local")
    
    # Estadísticas de caché
    cache_mgr = CacheManager()
    cache_stats = cache_mgr.get_stats()
    
    with col_cache:
        if cache_stats['total_entries'] > 0:
            st.info(f"🚀 {cache_stats['total_entries']} cached")
        else:
            st.info("📦 Caché vacío")
    
    st.markdown("---")
    
    # Opciones de configuración
    st.markdown("### ⚙️ Configuración")
    use_cache = st.checkbox("Usar caché inteligente", value=True, help="Reduce consumo de API hasta 80%")
    use_smart_batch = st.checkbox("Batch inteligente", value=False, help="Procesa múltiples noticias por prompt")
    
    if st.button("🗑️ Limpiar caché"):
        deleted = cache_mgr.clear_old_entries(max_age_days=30)
        st.success(f"✅ {deleted} entradas eliminadas")
    
    st.markdown("---")
    st.caption("Desarrollado con ❤️ por SAVA Team")
    st.caption("Optimizado para reducir costos de API")

def main():
    # Header profesional
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
    with col_h1:
        st.title("📊 SAVA Agro-Insight PRO")
        st.markdown("*Sistema Inteligente de Análisis de Riesgos Agroindustriales*")
    with col_h2:
        st.metric("Versión", "2.0 Pro", delta="Optimizado")
    with col_h3:
        if st.button("ℹ️ Ayuda"):
            st.info("""
            **Funcionalidades Principales:**
            - 📂 Análisis CSV con caché
            - 🌐 Noticias en vivo
            - 🗺️ Mapa geográfico
            - 🤖 Chatbot inteligente
            - 📈 Análisis de tendencias
            - 🔔 Sistema de alertas
            - 📄 Exportación PDF/Excel
            """)
    
    st.markdown("---")
    
    # Tabs MEJORADOS con más funcionalidades
    tabs = st.tabs([
        "📂 Análisis CSV",
        "🌐 Noticias en Vivo",
        "🗺️ Mapa Geográfico",
        "🤖 Chatbot IA",
        "📈 Tendencias",
        "🔔 Alertas",
        "📊 Dashboard",
        "📄 Exportar",
        "🗄️ Historial"
    ])
    
    # Inicializar componentes
    analyzer = AgroSentimentAnalyzer()
    geo_mapper = NewsGeoMapper()
    trend_analyzer = TrendAnalyzer()
    alert_system = AlertSystem()
    exporter = ReportExporter()
    
    # Inicializar chatbot si hay API key
    chatbot = None
    if analyzer.api_key:
        chatbot = AgriNewsBot(analyzer.api_key)
    
    # TAB 1: ANÁLISIS CSV (OPTIMIZADO)
    with tabs[0]:
        st.header("📂 Análisis Inteligente de CSV")
        
        col_upload, col_info = st.columns([3, 1])
        
        with col_upload:
            uploaded_file = st.file_uploader(
                "Sube tu dataset de noticias",
                type=["csv"],
                help="Archivo CSV con columnas: Titular, Cuerpo, Fecha"
            )
        
        with col_info:
            st.info(f"""
            **Optimizaciones activas:**
            - ✅ Caché: {use_cache}
            - ✅ Batch: {use_smart_batch}
            - ⚡ Ahorro: ~70%
            """)
        
        if uploaded_file:
            df, error = load_and_validate_csv(uploaded_file)
            
            if error:
                st.error(error)
            else:
                st.success(f"✅ Archivo cargado: {len(df)} noticias")
                
                # Vista previa mejorada
                with st.expander("👁️ Vista Previa de Datos", expanded=False):
                    st.dataframe(
                        df[['titular', 'fecha']].head(10),
                        use_container_width=True,
                        hide_index=True
                    )
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    analyze_btn = st.button("🧠 Analizar con IA", type="primary", use_container_width=True)
                
                with col_btn2:
                    if use_smart_batch:
                        batch_btn = st.button("⚡ Análisis Batch Rápido", use_container_width=True)
                    else:
                        batch_btn = False
                
                with col_btn3:
                    cache_info = st.button("📊 Info de Caché", use_container_width=True)
                
                if cache_info:
                    st.json(cache_stats)
                
                # Análisis normal
                if analyze_btn:
                    if analyzer.api_key:
                        with st.spinner('🤖 Analizando con IA...'):
                            progress = st.progress(0)
                            status_text = st.empty()
                            
                            sents, expls = analyzer.analyze_batch(df, progress, use_smart_batch=use_cache)
                            
                            df['sentimiento_ia'] = sents
                            df['explicacion_ia'] = expls
                            
                            st.session_state['last_analysis'] = df
                            
                            # Mostrar estadísticas de optimización
                            cache_hits = sum(1 for e in expls if 'cache' in str(e).lower())
                            st.success(f"""
                            ✅ **Análisis completado!**
                            - 📊 {len(df)} noticias procesadas
                            - 🚀 {cache_hits} del caché ({cache_hits/len(df)*100:.1f}%)
                            - 💰 Ahorro estimado: {cache_hits * 0.002:.4f} USD
                            """)
                    else:
                        st.error("⚠️ API Key de Gemini no configurada")
                
                # Análisis batch inteligente
                if batch_btn:
                    with st.spinner('⚡ Análisis batch ultra-rápido...'):
                        texts_list = [f"{row['titular']}. {row['cuerpo']}" for _, row in df.iterrows()]
                        results = analyzer.analyze_batch_smart(texts_list, max_per_batch=5)
                        
                        df['sentimiento_ia'] = [r['sentimiento'] for r in results]
                        df['explicacion_ia'] = [r['explicacion'] for r in results]
                        
                        st.session_state['last_analysis'] = df
                        st.success(f"⚡ Análisis batch completado en tiempo récord!")
        
        # Mostrar resultados si existen
        if 'last_analysis' in st.session_state:
            df_res = st.session_state['last_analysis']
            st.markdown("---")
            st.subheader("📊 Resultados del Análisis")
            
            # Métricas en tarjetas
            col1, col2, col3, col4 = st.columns(4)
            total_res = len(df_res)
            pos_res = len(df_res[df_res['sentimiento_ia'] == 'Positivo'])
            neg_res = len(df_res[df_res['sentimiento_ia'] == 'Negativo'])
            neu_res = len(df_res[df_res['sentimiento_ia'] == 'Neutro'])
            
            col1.metric("Total", total_res, help="Noticias analizadas")
            col2.metric("🟢 Positivas", pos_res, delta=f"{pos_res/total_res*100:.1f}%")
            col3.metric("🔴 Negativas", neg_res, delta=f"{neg_res/total_res*100:.1f}%")
            col4.metric("⚪ Neutras", neu_res, delta=f"{neu_res/total_res*100:.1f}%")
            
            # Resultados en tarjetas expandibles
            for index, row in df_res.iterrows():
                color_map = {"Positivo": "green", "Negativo": "red", "Neutro": "gray"}
                color = color_map.get(row['sentimiento_ia'], "gray")
                
                with st.expander(f":{color}[{row['sentimiento_ia']}] - {row['titular']}", expanded=False):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"**🤖 Análisis:**{row['explicacion_ia']}")
                    with col_b:
                        st.caption(f"📅 {row['fecha']}")
                        st.caption(f"🆔 {row['id_original']}")
            
            # Botón de guardado
            if st.button("💾 Guardar en Firebase"):
                success, msg = save_analysis_results(df_res)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
    
    # TAB 2: NOTICIAS EN VIVO
    with tabs[1]:
        st.header("🌐 Radar de Noticias en Tiempo Real")
        
        col_search, col_max = st.columns([3, 1])
        with col_search:
            query = st.text_input(
                "🔍 Buscar noticias sobre...",
                value="agroindustria Valle del Cauca",
                placeholder="Ej: cultivo de caña de azúcar"
            )
        with col_max:
            max_results = st.number_input("Máx resultados", min_value=3, max_value=10, value=5)
        
        if st.button("🚀 Buscar y Analizar", type="primary"):
            with st.spinner(f"🔍 Buscando '{query}' en la web..."):
                web_results = analyzer.search_and_analyze_web(query=query, max_results=max_results)
                
                if web_results:
                    df_web = pd.DataFrame(web_results)
                    st.session_state['web_analysis'] = df_web
                    st.success(f"✅ {len(df_web)} noticias encontradas y analizadas")
                else:
                    st.warning("No se encontraron noticias")
        
        if 'web_analysis' in st.session_state:
            df_web = st.session_state['web_analysis']
            
            for index, row in df_web.iterrows():
                color_map = {"Positivo": "#2ecc71", "Negativo": "#e74c3c", "Neutro": "#bdc3c7"}
                emoji_map = {"Positivo": "🟢", "Negativo": "🔴", "Neutro": "⚪"}
                
                st.markdown(f"""
                <div style="background:white; padding:20px; border-radius:15px; margin:15px 0; 
                            border-left:5px solid {color_map[row['sentimiento_ia']]}; 
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h3>{emoji_map[row['sentimiento_ia']]} {row['titular']}</h3>
                    <p>{row['cuerpo'][:300]}...</p>
                    <p><b>🤖 Análisis:</b> {row['explicacion_ia']}</p>
                    <hr>
                    <small>📰 {row['fuente']} | 📅 {row['fecha']} | 
                    <a href="{row['url']}" target="_blank">🔗 Leer original</a></small>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("💾 Guardar Noticias Web"):
                success, msg = save_analysis_results(df_web, collection_name="noticias_web")
                st.success(msg) if success else st.error(msg)
    
    # TAB 3: MAPA GEOGRÁFICO
    with tabs[2]:
        st.header("🗺️ Mapa Geográfico de Noticias")
        
        data_source = None
        if 'last_analysis' in st.session_state:
            data_source = st.session_state['last_analysis']
        elif 'web_analysis' in st.session_state:
            data_source = st.session_state['web_analysis']
        
        if data_source is not None and len(data_source) > 0:
            col_map_type, col_map_action = st.columns([3, 1])
            
            with col_map_type:
                map_type = st.radio(
                    "Tipo de mapa",
                    ["🗺️ Mapa Interactivo", "🔥 Mapa de Calor (Riesgos)"],
                    horizontal=True
                )
            
            with col_map_action:
                if st.button("🔄 Generar Mapa", type="primary"):
                    with st.spinner("🗺️ Generando mapa..."):
                        if "Calor" in map_type:
                            news_map = geo_mapper.create_heatmap(data_source)
                        else:
                            news_map = geo_mapper.create_news_map(data_source)
                        
                        st.session_state['current_map'] = news_map
            
            if 'current_map' in st.session_state:
                folium_static(st.session_state['current_map'], width=1200, height=600)
        else:
            st.info("⬅️ Realiza primero un análisis para visualizar el mapa")
    
    # TAB 4: CHATBOT IA
    with tabs[3]:
        st.header("🤖 Asistente IA - Pregunta sobre las Noticias")
        
        if chatbot is None:
            st.error("⚠️ Chatbot no disponible. Verifica la API Key.")
        else:
            # Cargar base de conocimiento
            data_source = None
            if 'last_analysis' in st.session_state:
                data_source = st.session_state['last_analysis']
                chatbot.load_news_database(data_source)
            elif 'web_analysis' in st.session_state:
                data_source = st.session_state['web_analysis']
                chatbot.load_news_database(data_source)
            
            if data_source is not None:
                # Estadísticas
                st.info(chatbot.get_quick_stats())
                
                # Sugerencias
                st.markdown("**💡 Preguntas sugeridas:**")
                suggestions = chatbot.get_suggested_questions()
                cols = st.columns(len(suggestions))
                for i, suggestion in enumerate(suggestions):
                    if cols[i].button(f"💬 {suggestion[:30]}...", key=f"sug_{i}"):
                        st.session_state['chat_input'] = suggestion
                
                st.markdown("---")
                
                # Input del usuario
                user_input = st.text_input(
                    "Tu pregunta:",
                    key="chat_input",
                    placeholder="Ej: ¿Cuáles son los principales riesgos detectados?"
                )
                
                col_send, col_reset = st.columns([4, 1])
                with col_send:
                    send_btn = st.button("📤 Enviar", type="primary", use_container_width=True)
                with col_reset:
                    if st.button("🔄 Reiniciar", use_container_width=True):
                        chatbot.reset_conversation()
                        st.success("Conversación reiniciada")
                
                if send_btn and user_input:
                    with st.spinner("🤖 Pensando..."):
                        response = chatbot.chat(user_input)
                        
                        # Mensaje del usuario
                        st.markdown(f"""
                        <div class="chat-message user-message">
                            <b>👤 Tú:</b> {user_input}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Respuesta del bot
                        st.markdown(f"""
                        <div class="chat-message bot-message">
                            <b>🤖 Asistente:</b><br>{response['response']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Noticias relevantes
                        if response['relevant_news']:
                            with st.expander(f"📰 {len(response['relevant_news'])} Noticias Relevantes"):
                                for news in response['relevant_news']:
                                    st.markdown(f"**{news['titular']}** ({news['sentimiento']})")
                                    st.caption(f"Similitud: {news['similarity']:.2%}")
            else:
                st.warning("⬅️ Primero carga noticias para interactuar con el chatbot")
    
    # TAB 5: ANÁLISIS DE TENDENCIAS
    with tabs[4]:
        st.header("📈 Análisis de Tendencias y Predicciones")
        
        data_source = st.session_state.get('last_analysis') or st.session_state.get('web_analysis')
        
        if data_source is not None:
            trend_analyzer.load_data(data_source)
            
            # Resumen ejecutivo
            st.markdown("## 📋 Resumen Ejecutivo")
            st.markdown(trend_analyzer.generate_executive_summary())
            
            st.markdown("---")
            
            # Índices de riesgo y oportunidades
            col_risk, col_opp = st.columns(2)
            
            with col_risk:
                risk = trend_analyzer.get_risk_score()
                st.metric(
                    "🚨 Índice de Riesgo",
                    f"{risk['score']}%",
                    delta=risk['level'],
                    delta_color="inverse"
                )
                st.progress(risk['score']/100)
            
            with col_opp:
                opp = trend_analyzer.get_opportunities_score()
                st.metric(
                    "✅ Índice de Oportunidades",
                    f"{opp['score']}%",
                    delta=opp['level']
                )
                st.progress(opp['score']/100)
            
            st.markdown("---")
            
            # Palabras clave
            col_kw1, col_kw2 = st.columns(2)
            
            with col_kw1:
                st.markdown("### 🔴 Palabras Clave Negativas")
                keywords_neg = trend_analyzer.extract_keywords('Negativo', top_n=10)
                keywords_neg_df = pd.DataFrame(keywords_neg, columns=['Palabra', 'Frecuencia'])
                st.bar_chart(keywords_neg_df.set_index('Palabra'))
            
            with col_kw2:
                st.markdown("### 🟢 Palabras Clave Positivas")
                keywords_pos = trend_analyzer.extract_keywords('Positivo', top_n=10)
                keywords_pos_df = pd.DataFrame(keywords_pos, columns=['Palabra', 'Frecuencia'])
                st.bar_chart(keywords_pos_df.set_index('Palabra'))
            
            st.markdown("---")
            
            # Predicción de tendencia
            st.markdown("### 🔮 Predicción de Tendencia")
            prediction = trend_analyzer.predict_sentiment_trend()
            st.info(prediction)
            
            # Clustering temático
            st.markdown("### 🗂️ Agrupación Temática")
            if st.button("Generar Clusters"):
                with st.spinner("Agrupando noticias..."):
                    try:
                        df_clustered, themes = trend_analyzer.cluster_news(n_clusters=3)
                        
                        for i, theme in enumerate(themes):
                            st.markdown(f"**Cluster {i+1}:** {theme}")
                            cluster_data = df_clustered[df_clustered['cluster'] == i]
                            st.caption(f"{len(cluster_data)} noticias")
                    except:
                        st.warning("No hay suficientes datos para clustering")
        else:
            st.info("⬅️ Primero realiza un análisis")
    
    # TAB 6: ALERTAS
    with tabs[5]:
        st.header("🔔 Sistema de Alertas Inteligentes")
        
        data_source = st.session_state.get('last_analysis') or st.session_state.get('web_analysis')
        
        if data_source is not None:
            if st.button("🔍 Generar Alertas", type="primary"):
                with st.spinner("Analizando riesgos..."):
                    alerts = alert_system.analyze_and_generate_alerts(data_source)
                    st.session_state['alerts'] = alerts
            
            if 'alerts' in st.session_state:
                alerts = st.session_state['alerts']
                
                # Resumen
                st.markdown(alert_system.get_alert_summary())
                st.markdown("---")
                
                # Mostrar alertas
                if alerts:
                    for alert in alerts:
                        severity_class = f"alert-{alert['severity']}"
                        
                        st.markdown(f"""
                        <div class="{severity_class}">
                            <h4>{alert['title']}</h4>
                            <p>{alert['message']}</p>
                            <p><b>💡 Recomendación:</b> {alert['recommendation']}</p>
                            <small>🕒 {alert['timestamp']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No se detectaron alertas críticas")
        else:
            st.info("⬅️ Primero realiza un análisis")
    
    # TAB 7: DASHBOARD
    with tabs[6]:
        st.header("📊 Dashboard Ejecutivo")
        
        data_source = st.session_state.get('last_analysis') or st.session_state.get('web_analysis')
        
        if data_source is not None:
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            total = len(data_source)
            pos = len(data_source[data_source['sentimiento_ia'] == 'Positivo'])
            neg = len(data_source[data_source['sentimiento_ia'] == 'Negativo'])
            neu = len(data_source[data_source['sentimiento_ia'] == 'Neutro'])
            
            col1.metric("Total", total)
            col2.metric("🟢 Positivas", pos, f"{pos/total*100:.1f}%")
            col3.metric("🔴 Negativas", neg, f"{neg/total*100:.1f}%")
            col4.metric("⚪ Neutras", neu, f"{neu/total*100:.1f}%")
            
            st.markdown("---")
            
            # Gráficos
            col_pie, col_bar = st.columns(2)
            
            with col_pie:
                fig_pie = px.pie(
                    data_source,
                    names='sentimiento_ia',
                    color='sentimiento_ia',
                    color_discrete_map={'Positivo': '#2ecc71', 'Negativo': '#e74c3c', 'Neutro': '#95a5a6'},
                    hole=0.4,
                    title="Distribución de Sentimientos"
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_bar:
                sentiment_counts = data_source['sentimiento_ia'].value_counts()
                fig_bar = go.Figure(data=[
                    go.Bar(
                        x=sentiment_counts.index,
                        y=sentiment_counts.values,
                        marker_color=['#2ecc71', '#e74c3c', '#95a5a6']
                    )
                ])
                fig_bar.update_layout(
                    title="Conteo por Sentimiento",
                    xaxis_title="Sentimiento",
                    yaxis_title="Cantidad",
                    height=400
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("⬅️ Primero realiza un análisis")
    
    # TAB 8: EXPORTAR
    with tabs[7]:
        st.header("📄 Exportación de Reportes")
        
        data_source = st.session_state.get('last_analysis') or st.session_state.get('web_analysis')
        
        if data_source is not None:
            st.info(f"📊 {len(data_source)} noticias listas para exportar")
            
            col_pdf, col_excel = st.columns(2)
            
            with col_pdf:
                st.markdown("### 📕 Reporte PDF")
                st.write("Genera un reporte profesional en PDF con gráficos y análisis")
                
                if st.button("📄 Generar PDF", type="primary", use_container_width=True):
                    with st.spinner("Generando PDF..."):
                        try:
                            pdf_buffer = exporter.export_to_pdf(data_source, include_stats=True)
                            st.download_button(
                                label="⬇️ Descargar PDF",
                                data=pdf_buffer,
                                file_name=f"reporte_sava_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("✅ PDF generado!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            with col_excel:
                st.markdown("### 📗 Reporte Excel")
                st.write("Exporta a Excel con múltiples hojas, gráficos y formato profesional")
                
                if st.button("📊 Generar Excel", type="primary", use_container_width=True):
                    with st.spinner("Generando Excel..."):
                        try:
                            excel_buffer = exporter.export_to_excel(data_source, include_charts=True)
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=excel_buffer,
                                file_name=f"reporte_sava_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            st.success("✅ Excel generado!")
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            st.markdown("---")
            
            # Exportación CSV simple
            st.markdown("### 📄 Exportación CSV")
            csv = data_source.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Descargar CSV",
                data=csv,
                file_name=f"analisis_sava_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("⬅️ Primero realiza un análisis")
    
    # TAB 9: HISTORIAL
    with tabs[8]:
        st.header("🗄️ Historial de Análisis")
        
        if st.button("🔄 Cargar Historial"):
            with st.spinner("Cargando desde Firebase..."):
                hist = fetch_history(limit=100)
                
                if hist:
                    df_hist = pd.DataFrame(hist)
                    st.success(f"✅ {len(df_hist)} registros cargados")
                    
                    # Filtros
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        filter_sent = st.multiselect(
                            "Filtrar por sentimiento",
                            ['Positivo', 'Negativo', 'Neutro'],
                            default=['Positivo', 'Negativo', 'Neutro']
                        )
                    
                    df_filtered = df_hist[df_hist['sentimiento'].isin(filter_sent)]
                    
                    st.dataframe(df_filtered, use_container_width=True, height=400)
                else:
                    st.warning("No hay historial disponible")

if __name__ == "__main__":
    main()
