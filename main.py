"""
SAVA Agro-Insight V2.0 - Sistema Profesional de Análisis de Sentimiento
Interfaz mejorada con todas las funcionalidades avanzadas
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import altair as alt
from datetime import datetime

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
from src.auth_manager import (
    register_user, authenticate_user, get_current_user,
    is_authenticated, logout
)

# Configuración de página MEJORADA
st.set_page_config(
    page_title="SAVA Agro-Insight Pro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URLs de logos SAVA
LOGO_URL = "https://raw.githubusercontent.com/GIUSEPPESAN21/LOGO-SAVA/main/LOGO.jpg"
LOGO_COLIBRI_URL = "https://raw.githubusercontent.com/GIUSEPPESAN21/LOGO-SAVA/main/LOGO%20COLIBRI.png"

# CSS PROFESIONAL MEJORADO CON MEJOR TIPOGRAFÍA
st.markdown("""
    <style>
    /* Importar fuentes de Google */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Tema general mejorado */
    .main { 
        background: linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 50%, #c3cfe2 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Tipografía mejorada */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
        color: #1a1a2e !important;
    }
    
    /* Texto general */
    body, .stMarkdown, p, div, span {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }
    
    /* Botones premium mejorados */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Botones secundarios */
    .stButton>button[kind="secondary"] {
        background: white !important;
        color: #667eea !important;
        border: 2px solid #667eea !important;
    }
    
    /* Métricas mejoradas */
    div[data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif !important;
        color: #1a1a2e !important;
        letter-spacing: -0.5px !important;
    }
    
    /* Inputs mejorados */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        border-radius: 10px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 10px 15px !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Tarjetas con sombra */
    .css-1r6slb0 {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    
    /* Sidebar premium mejorado */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
        color: white !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-family: 'Poppins', sans-serif !important;
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

# Funciones de autenticación
def show_login_page():
    """Muestra la página de login/registro"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Logo SAVA
        try:
            st.image(LOGO_URL, width=200, use_container_width=True)
        except:
            st.image(LOGO_COLIBRI_URL, width=200, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🌱 SAVA Agro-Insight PRO")
        st.markdown("**Sistema Inteligente de Análisis de Riesgos Agroindustriales**")
        st.markdown("---")
        
        # Tabs de Login/Registro
        tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
        
        # TAB 1: LOGIN
        with tab1:
            st.markdown("### Inicia Sesión")
            with st.form("login_form"):
                username = st.text_input("👤 Usuario o Email", placeholder="Ingresa tu usuario o email")
                password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
                
                login_button = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
                
                if login_button:
                    if username and password:
                        success, user_data, message = authenticate_user(username, password)
                        if success:
                            st.session_state['user'] = user_data
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("⚠️ Por favor completa todos los campos")
        
        # TAB 2: REGISTRO
        with tab2:
            st.markdown("### Crea tu Cuenta")
            with st.form("register_form"):
                new_username = st.text_input("👤 Nombre de Usuario", placeholder="Elige un nombre de usuario único")
                new_email = st.text_input("📧 Email", placeholder="tu@email.com")
                new_password = st.text_input("🔒 Contraseña", type="password", placeholder="Mínimo 6 caracteres", help="La contraseña debe tener al menos 6 caracteres")
                confirm_password = st.text_input("🔒 Confirmar Contraseña", type="password", placeholder="Repite tu contraseña")
                
                register_button = st.form_submit_button("✨ Crear Cuenta", use_container_width=True)
                
                if register_button:
                    if new_username and new_email and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("❌ Las contraseñas no coinciden")
                        elif len(new_password) < 6:
                            st.error("❌ La contraseña debe tener al menos 6 caracteres")
                        else:
                            success, message = register_user(new_username, new_email, new_password)
                            if success:
                                st.success(message)
                                st.info("🔄 Puedes iniciar sesión ahora")
                            else:
                                st.error(message)
                    else:
                        st.warning("⚠️ Por favor completa todos los campos")
        
        st.markdown("---")
        st.caption("💡 **Nota:** Necesitas Firebase configurado para usar autenticación")

# Sidebar MEJORADO con logo y autenticación
def render_sidebar(use_cache=True, use_smart_batch=False):
    """Renderiza el sidebar con logo y autenticación"""
    # Logo SAVA
    try:
        st.image(LOGO_URL, width=120, use_container_width=True)
    except:
        try:
            st.image(LOGO_COLIBRI_URL, width=120, use_container_width=True)
        except:
            st.image("https://cdn-icons-png.flaticon.com/512/1094/1094349.png", width=80)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Información del usuario
    if is_authenticated():
        user = get_current_user()
        st.markdown(f"### 👤 {user['username']}")
        st.markdown(f"📧 {user['email']}")
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            logout()
        st.markdown("---")
    else:
        st.info("🔒 No has iniciado sesión")
        if st.button("🔐 Iniciar Sesión", use_container_width=True):
            st.session_state['show_login'] = True
            st.rerun()
        st.markdown("---")
    
    st.markdown("### 🌱 SAVA Software")
    st.markdown("**Agro-Insight Pro v2.1**")
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
    use_cache = st.checkbox("Usar caché inteligente", value=use_cache, help="Reduce consumo de API hasta 80%")
    use_smart_batch = st.checkbox("Batch inteligente", value=use_smart_batch, help="Procesa múltiples noticias por prompt")
    
    if st.button("🗑️ Limpiar caché"):
        deleted = cache_mgr.clear_old_entries(max_age_days=30)
        st.success(f"✅ {deleted} entradas eliminadas")
    
    st.markdown("---")
    st.caption("Desarrollado con ❤️ por SAVA Team")
    st.caption("Optimizado para reducir costos de API")
    
    return use_cache, use_smart_batch
    
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
    # Inicializar estado de sesión
    if 'show_login' not in st.session_state:
        # Verificar si Firebase está configurado
        firebase_configured = "firebase_credentials" in st.secrets or "firebase" in st.secrets
        st.session_state['show_login'] = firebase_configured
    if 'user' not in st.session_state:
        st.session_state['user'] = None
    
    # Verificar autenticación (solo si Firebase está configurado)
    firebase_configured = "firebase_credentials" in st.secrets or "firebase" in st.secrets
    
    if firebase_configured:
        # Si Firebase está configurado, requerir autenticación
        if not is_authenticated() and st.session_state.get('show_login', True):
            show_login_page()
            return
        
        # Si está autenticado, ocultar el flag de login
        if is_authenticated():
            st.session_state['show_login'] = False
    else:
        # Modo local: crear usuario temporal
        if 'user' not in st.session_state or st.session_state['user'] is None:
            st.session_state['user'] = {
                'username': 'Usuario Local',
                'email': 'local@sava.local',
                'role': 'user'
            }
    
    # Renderizar sidebar con autenticación y obtener configuración
    with st.sidebar:
        use_cache, use_smart_batch = render_sidebar(
            use_cache=st.session_state.get('use_cache', True),
            use_smart_batch=st.session_state.get('use_smart_batch', False)
        )
        # Guardar configuración en sesión
        st.session_state['use_cache'] = use_cache
        st.session_state['use_smart_batch'] = use_smart_batch
    
    # Header profesional mejorado
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
    with col_h1:
        user = get_current_user()
        st.title("📊 SAVA Agro-Insight PRO")
        st.markdown(f"*Bienvenido, {user['username'] if user else 'Usuario'}* | Sistema Inteligente de Análisis de Riesgos Agroindustriales")
    with col_h2:
        st.metric("Versión", "2.1 Pro", delta="Optimizado")
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
                        width='stretch',
                        hide_index=True
                    )
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    analyze_btn = st.button("🧠 Analizar con IA", type="primary", width='stretch')
                
                with col_btn2:
                    if use_smart_batch:
                        batch_btn = st.button("⚡ Análisis Batch Rápido", width='stretch')
                    else:
                        batch_btn = False
                
                with col_btn3:
                    cache_info = st.button("📊 Info de Caché", width='stretch')
                
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
                
                # Análisis batch inteligente - CORREGIDO: método no existe, usar batch normal
                if batch_btn:
                    with st.spinner('⚡ Análisis batch rápido...'):
                        progress = st.progress(0)
                        sents, expls = analyzer.analyze_batch(df, progress, use_smart_batch=True)
                        
                        df['sentimiento_ia'] = sents
                        df['explicacion_ia'] = expls
                        
                        st.session_state['last_analysis'] = df
                        st.success(f"⚡ Análisis batch completado!")
        
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
        
        # CORREGIDO: DataFrame no puede usar comparación directa
        data_source = st.session_state.get('last_analysis')
        if data_source is None:
            data_source = st.session_state.get('web_analysis')
        
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
                        try:
                            if "Calor" in map_type:
                                news_map = geo_mapper.create_heatmap(data_source)
                                # Verificar si hay noticias negativas
                                negativas = len(data_source[data_source['sentimiento_ia'] == 'Negativo'])
                                if negativas == 0:
                                    st.warning("⚠️ No hay noticias negativas para mostrar en el mapa de calor")
                                else:
                                    st.success(f"✅ Mapa de calor generado con {negativas} noticias negativas")
                            else:
                                news_map = geo_mapper.create_news_map(data_source)
                                st.success("✅ Mapa interactivo generado correctamente")
                            
                            st.session_state['current_map'] = news_map
                        except Exception as e:
                            st.error(f"❌ Error generando mapa: {str(e)}")
                            st.caption("💡 Verifica que las noticias tengan ubicaciones detectables")
            
            if 'current_map' in st.session_state:
                # CORREGIDO: Solución robusta para que el mapa no desaparezca
                try:
                    # Opción 1: st_folium (preferido)
                    map_data = st_folium(
                        st.session_state['current_map'], 
                        width=1200, 
                        height=600,
                        returned_objects=[],
                        key=f"map_{hash(str(st.session_state.get('current_map', '')))}"
                    )
                    
                    # Si el mapa se renderizó correctamente, mostrar info
                    if map_data:
                        st.caption("🗺️ Mapa interactivo - Usa los controles para zoom y navegación")
                except Exception as e:
                    # Opción 2: Fallback con HTML directo
                    try:
                        st.warning("⚠️ Usando modo de visualización alternativo")
                        map_html = st.session_state['current_map']._repr_html_()
                        st.components.v1.html(map_html, width=1200, height=600, scrolling=False)
                        st.caption("💡 Si el mapa no se ve, recarga la página")
                    except Exception as e2:
                        st.error(f"❌ Error mostrando mapa: {str(e2)}")
                        st.caption("💡 Intenta generar el mapa nuevamente")
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
                    send_btn = st.button("📤 Enviar", type="primary", width='stretch')
                with col_reset:
                    if st.button("🔄 Reiniciar", width='stretch'):
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
        
        # CORREGIDO: DataFrame no puede usar 'or' directamente
        data_source = st.session_state.get('last_analysis')
        if data_source is None:
            data_source = st.session_state.get('web_analysis')
        
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
            
            # MEJORADO: Análisis de tendencias más completo
            st.markdown("### 📊 Análisis Detallado")
            
            # Gráfico de evolución temporal si hay fechas
            if 'fecha' in data_source.columns:
                try:
                    data_source['fecha_parsed'] = pd.to_datetime(data_source['fecha'], errors='coerce')
                    df_with_dates = data_source[data_source['fecha_parsed'].notna()].copy()
                    
                    if len(df_with_dates) > 0:
                        df_with_dates['fecha_only'] = df_with_dates['fecha_parsed'].dt.date
                        trend_over_time = df_with_dates.groupby(['fecha_only', 'sentimiento_ia']).size().unstack(fill_value=0)
                        
                        if len(trend_over_time) > 0:
                            st.markdown("#### 📅 Evolución Temporal del Sentimiento")
                            fig_trend = px.line(
                                trend_over_time.reset_index(),
                                x='fecha_only',
                                y=['Positivo', 'Negativo', 'Neutro'],
                                title="Tendencia del Sentimiento en el Tiempo",
                                labels={'fecha_only': 'Fecha', 'value': 'Cantidad de Noticias'},
                                color_discrete_map={'Positivo': '#2ecc71', 'Negativo': '#e74c3c', 'Neutro': '#95a5a6'}
                            )
                            st.plotly_chart(fig_trend, width='stretch')
                except Exception as e:
                    st.caption(f"⚠️ No se pudo generar gráfico temporal: {e}")
            
            st.markdown("---")
            
            # Palabras clave mejoradas
            col_kw1, col_kw2 = st.columns(2)
            
            with col_kw1:
                st.markdown("### 🔴 Palabras Clave Negativas (Top 10)")
                keywords_neg = trend_analyzer.extract_keywords('Negativo', top_n=10)
                if keywords_neg:
                    keywords_neg_df = pd.DataFrame(keywords_neg, columns=['Palabra', 'Frecuencia'])
                    fig_neg = px.bar(
                        keywords_neg_df,
                        x='Frecuencia',
                        y='Palabra',
                        orientation='h',
                        color='Frecuencia',
                        color_continuous_scale='Reds',
                        title="Palabras más frecuentes en noticias negativas"
                    )
                    fig_neg.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_neg, width='stretch')
                else:
                    st.info("No hay palabras clave negativas detectadas")
            
            with col_kw2:
                st.markdown("### 🟢 Palabras Clave Positivas (Top 10)")
                keywords_pos = trend_analyzer.extract_keywords('Positivo', top_n=10)
                if keywords_pos:
                    keywords_pos_df = pd.DataFrame(keywords_pos, columns=['Palabra', 'Frecuencia'])
                    fig_pos = px.bar(
                        keywords_pos_df,
                        x='Frecuencia',
                        y='Palabra',
                        orientation='h',
                        color='Frecuencia',
                        color_continuous_scale='Greens',
                        title="Palabras más frecuentes en noticias positivas"
                    )
                    fig_pos.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig_pos, width='stretch')
                else:
                    st.info("No hay palabras clave positivas detectadas")
            
            st.markdown("---")
            
            # Predicción de tendencia mejorada
            st.markdown("### 🔮 Predicción de Tendencia")
            prediction = trend_analyzer.predict_sentiment_trend()
            if "No hay" not in prediction and "suficientes" not in prediction:
                st.success(prediction)
            else:
                st.info(prediction)
            
            # Clustering temático mejorado
            st.markdown("### 🗂️ Agrupación Temática de Noticias")
            st.caption("Agrupa noticias similares por contenido para identificar temas principales")
            if st.button("🔍 Generar Clusters Temáticos", type="primary"):
                with st.spinner("Agrupando noticias por similitud temática..."):
                    try:
                        df_clustered, themes = trend_analyzer.cluster_news(n_clusters=3)
                        
                        if themes:
                            for i, theme in enumerate(themes):
                                cluster_data = df_clustered[df_clustered['cluster'] == i]
                                with st.expander(f"📁 **Cluster {i+1}**: {theme} ({len(cluster_data)} noticias)", expanded=(i==0)):
                                    st.caption(f"**Tema principal:** {theme}")
                                    st.caption(f"**Noticias en este cluster:** {len(cluster_data)}")
                                    
                                    # Mostrar distribución de sentimientos en el cluster
                                    sent_dist = cluster_data['sentimiento_ia'].value_counts()
                                    st.write("Distribución de sentimientos:")
                                    for sent, count in sent_dist.items():
                                        st.write(f"- {sent}: {count} ({count/len(cluster_data)*100:.1f}%)")
                        else:
                            st.warning("No se pudieron generar temas. Intenta con más noticias.")
                    except Exception as e:
                        st.warning(f"No hay suficientes datos para clustering: {str(e)}")
                        st.caption("💡 Se necesitan al menos 5 noticias para generar clusters")
        else:
            st.info("⬅️ Primero realiza un análisis")
    
    # TAB 6: ALERTAS - MEJORADO
    with tabs[5]:
        st.header("🔔 Sistema de Alertas Inteligentes")
        st.markdown("""
        **¿Qué hace este sistema?**
        
        El sistema de alertas analiza automáticamente tus noticias y detecta:
        - 🚨 **Alertas Críticas**: Situaciones que requieren atención inmediata
        - ⚠️ **Alertas Altas**: Problemas importantes que deben monitorearse
        - ⚡ **Alertas Medias**: Situaciones que requieren seguimiento
        
        **Tipos de alertas detectadas:**
        - Alta proporción de noticias negativas (>40%)
        - Palabras clave críticas (sequía, plaga, crisis, pérdida, conflicto, paro)
        - Baja proporción de noticias positivas (<15%)
        - Concentración geográfica de riesgos en zonas específicas
        """)
        
        st.markdown("---")
        
        data_source = st.session_state.get('last_analysis')
        if data_source is None:
            data_source = st.session_state.get('web_analysis')
        
        if data_source is not None:
            col_info, col_btn = st.columns([3, 1])
            
            with col_info:
                total = len(data_source)
                negativas = len(data_source[data_source['sentimiento_ia'] == 'Negativo'])
                positivas = len(data_source[data_source['sentimiento_ia'] == 'Positivo'])
                st.caption(f"📊 Analizando {total} noticias ({negativas} negativas, {positivas} positivas)")
            
            with col_btn:
                if st.button("🔍 Generar Alertas", type="primary", width='stretch'):
                    with st.spinner("🔍 Analizando riesgos y generando alertas..."):
                        alerts = alert_system.analyze_and_generate_alerts(data_source)
                        st.session_state['alerts'] = alerts
                        st.success(f"✅ Análisis completado: {len(alerts)} alertas generadas")
            
            if 'alerts' in st.session_state:
                alerts = st.session_state['alerts']
                
                # MEJORADO: Resumen visual mejorado
                st.markdown("### 📊 Resumen de Alertas")
                
                if alerts:
                    critical = sum(1 for a in alerts if a['severity'] == 'critical')
                    high = sum(1 for a in alerts if a['severity'] == 'high')
                    medium = sum(1 for a in alerts if a['severity'] == 'medium')
                    
                    col_crit, col_high, col_med, col_total = st.columns(4)
                    
                    with col_crit:
                        st.metric("🚨 Críticas", critical, delta="Atención inmediata" if critical > 0 else None, delta_color="inverse")
                    with col_high:
                        st.metric("⚠️ Altas", high, delta="Monitorear" if high > 0 else None)
                    with col_med:
                        st.metric("⚡ Medias", medium, delta="Seguimiento" if medium > 0 else None)
                    with col_total:
                        st.metric("📋 Total", len(alerts))
                    
                    st.markdown("---")
                    
                    # MEJORADO: Mostrar alertas de forma más clara
                    st.markdown("### 🔔 Alertas Detectadas")
                    
                    # Ordenar por severidad
                    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
                    alerts_sorted = sorted(alerts, key=lambda x: severity_order.get(x['severity'], 3))
                    
                    for i, alert in enumerate(alerts_sorted, 1):
                        # Iconos según severidad
                        if alert['severity'] == 'critical':
                            icon = "🚨"
                            color = "#e74c3c"
                            border = "5px solid #e74c3c"
                        elif alert['severity'] == 'high':
                            icon = "⚠️"
                            color = "#f39c12"
                            border = "5px solid #f39c12"
                        else:
                            icon = "⚡"
                            color = "#3498db"
                            border = "5px solid #3498db"
                        
                        with st.container():
                            st.markdown(f"""
                            <div style="background-color: white; padding: 20px; border-radius: 10px; 
                                        border-left: {border}; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                <h3 style="color: {color}; margin-top: 0;">{icon} {alert['title']}</h3>
                                <p style="font-size: 1.1em; margin-bottom: 10px;"><b>Descripción:</b> {alert['message']}</p>
                                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
                                    <p style="margin: 0;"><b>💡 Recomendación:</b> {alert['recommendation']}</p>
                                </div>
                                <small style="color: #6c757d;">🕒 Generada: {alert.get('timestamp', 'N/A')}</small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Mostrar detalles adicionales si existen
                        if 'details' in alert and alert['details']:
                            with st.expander(f"📋 Ver detalles de {alert['title']}"):
                                if isinstance(alert['details'], dict):
                                    for key, value in alert['details'].items():
                                        if isinstance(value, list):
                                            st.write(f"**{key}:**")
                                            for item in value[:5]:  # Mostrar máximo 5
                                                st.caption(f"  • {item}")
                                        else:
                                            st.write(f"**{key}:** {value}")
                else:
                    st.success("""
                    ✅ **¡Excelente! No se detectaron alertas críticas.**
                    
                    Esto significa que:
                    - La proporción de noticias negativas está en niveles normales
                    - No se detectaron palabras clave críticas peligrosas
                    - El sector muestra un panorama estable
                    - No hay concentraciones anormales de riesgos
                    """)
        else:
            st.info("""
            ⬅️ **Primero realiza un análisis**
            
            Para generar alertas:
            1. Ve a la pestaña "📂 Análisis CSV" o "🌐 Noticias en Vivo"
            2. Analiza tus noticias
            3. Regresa aquí y haz click en "🔍 Generar Alertas"
            """)
    
    # TAB 7: DASHBOARD
    with tabs[6]:
        st.header("📊 Dashboard Ejecutivo")
        
        data_source = st.session_state.get('last_analysis')
        if data_source is None:
            data_source = st.session_state.get('web_analysis')
        
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
                st.plotly_chart(fig_pie, width='stretch')
            
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
                st.plotly_chart(fig_bar, width='stretch')
        else:
            st.info("⬅️ Primero realiza un análisis")
    
    # TAB 8: EXPORTAR - MEJORADO
    with tabs[7]:
        st.header("📄 Exportación de Reportes")
        st.markdown("""
        **Exporta tus análisis en diferentes formatos:**
        - 📕 **PDF**: Reporte ejecutivo profesional con gráficos
        - 📗 **Excel**: Múltiples hojas con datos, estadísticas y gráficos
        - 📄 **CSV**: Datos simples para análisis externo
        """)
        
        st.markdown("---")
        
        data_source = st.session_state.get('last_analysis')
        if data_source is None:
            data_source = st.session_state.get('web_analysis')
        
        if data_source is not None:
            # CORREGIDO: Asegurar que datetime esté disponible
            try:
                from datetime import datetime as dt
                fecha_str = dt.now().strftime('%Y%m%d')
            except:
                import time
                fecha_str = time.strftime('%Y%m%d')
            
            st.info(f"📊 **{len(data_source)} noticias** listas para exportar")
            
            col_pdf, col_excel = st.columns(2)
            
            with col_pdf:
                st.markdown("### 📕 Reporte PDF Profesional")
                st.caption("Incluye: Resumen ejecutivo, estadísticas, gráficos y análisis detallado")
                
                if st.button("📄 Generar PDF", type="primary", width='stretch', key="btn_pdf"):
                    with st.spinner("📄 Generando reporte PDF profesional..."):
                        try:
                            pdf_buffer = exporter.export_to_pdf(data_source, include_stats=True)
                            st.download_button(
                                label="⬇️ Descargar PDF",
                                data=pdf_buffer,
                                file_name=f"reporte_sava_{fecha_str}.pdf",
                                mime="application/pdf",
                                width='stretch',
                                key="dl_pdf"
                            )
                            st.success("✅ PDF generado exitosamente!")
                        except Exception as e:
                            st.error(f"❌ Error generando PDF: {str(e)}")
                            st.caption("💡 Verifica que reportlab esté instalado: pip install reportlab")
            
            with col_excel:
                st.markdown("### 📗 Reporte Excel Avanzado")
                st.caption("Incluye: Datos completos, estadísticas, gráficos interactivos y palabras clave")
                
                if st.button("📊 Generar Excel", type="primary", width='stretch', key="btn_excel"):
                    with st.spinner("📊 Generando reporte Excel avanzado..."):
                        try:
                            excel_buffer = exporter.export_to_excel(data_source, include_charts=True)
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=excel_buffer,
                                file_name=f"reporte_sava_{fecha_str}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                width='stretch',
                                key="dl_excel"
                            )
                            st.success("✅ Excel generado exitosamente!")
                        except Exception as e:
                            st.error(f"❌ Error generando Excel: {str(e)}")
                            st.caption("💡 Verifica que openpyxl y xlsxwriter estén instalados")
            
            st.markdown("---")
            
            # Exportación CSV simple - CORREGIDO
            st.markdown("### 📄 Exportación CSV Simple")
            st.caption("Formato simple para análisis en Excel, Python, R u otras herramientas")
            
            try:
                csv = data_source.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Descargar CSV",
                    data=csv,
                    file_name=f"analisis_sava_{fecha_str}.csv",
                    mime="text/csv",
                    width='stretch',
                    key="dl_csv"
                )
                st.caption(f"✅ CSV listo: {len(data_source)} filas, {len(data_source.columns)} columnas")
            except Exception as e:
                st.error(f"❌ Error generando CSV: {str(e)}")
        else:
            st.info("""
            ⬅️ **Primero realiza un análisis**
            
            Para exportar reportes:
            1. Ve a "📂 Análisis CSV" o "🌐 Noticias en Vivo"
            2. Analiza tus noticias
            3. Regresa aquí y elige el formato de exportación
            """)
    
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
                    
                    st.dataframe(df_filtered, width='stretch', height=400)
                else:
                    st.warning("No hay historial disponible")

if __name__ == "__main__":
    main()

