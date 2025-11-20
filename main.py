"""
SAVA Agro-Insight V2.0 - Sistema Profesional de Análisis de Sentimiento
Interfaz optimizada: Diseño compacto, profesional y funcional.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import altair as alt
from datetime import datetime
from html import escape as html_escape
import time

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

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SAVA Agro-Insight Pro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URLs de recursos
LOGO_URL = "https://raw.githubusercontent.com/GIUSEPPESAN21/LOGO-SAVA/main/LOGO.jpg"
LOGO_COLIBRI_URL = "https://raw.githubusercontent.com/GIUSEPPESAN21/LOGO-SAVA/main/LOGO%20COLIBRI.png"

# --- ESTILOS CSS PROFESIONALES Y COMPACTOS ---
st.markdown("""
    <style>
    /* Importar fuentes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* === ESTRUCTURA GENERAL Y ESPACIADO === */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 100% !important;
    }
    
    body {
        font-family: 'Inter', sans-serif;
        background-color: #f8f9fa;
    }

    /* Reducción de espacios en encabezados */
    h1 { margin-top: 0 !important; padding-top: 0 !important; font-size: 2.2rem !important; }
    h2 { margin-top: 1rem !important; padding-top: 0 !important; font-size: 1.8rem !important; margin-bottom: 0.5rem !important; }
    h3 { margin-top: 0.8rem !important; font-size: 1.4rem !important; margin-bottom: 0.5rem !important; }
    
    /* Espaciado compacto entre elementos */
    .stElementContainer {
        margin-bottom: 0.8rem !important;
    }
    
    /* === COMPONENTES DE UI === */
    
    /* Botones Primarios - Gradiente Sutil */
    .stButton > button[type="primary"] {
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
        color: white;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton > button[type="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    /* Tarjetas de Métricas Compactas */
    [data-testid="stMetric"] {
        background-color: white;
        padding: 15px 20px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #6c757d; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #212529; }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
    }
    
    /* Botones del Sidebar */
    .sidebar-btn {
        width: 100%;
        margin-top: 10px;
    }

    /* === TARJETAS DE NOTICIAS (Resultados) === */
    .news-card-container {
        margin-bottom: 15px;
    }
    
    /* Estilo de Tabs más limpio */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: white;
        border-radius: 5px 5px 0 0;
        border: 1px solid #e9ecef;
        border-bottom: none;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #f1f8e9;
        border-top: 2px solid #2e7d32;
        color: #2e7d32;
        font-weight: 600;
    }

    /* Mensajes de Chat */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
    .bot-message { background-color: #f5f5f5; border-left: 4px solid #2e7d32; }

    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE AUTENTICACIÓN ---

def show_login_page():
    """Muestra la página de login/registro con diseño centrado y limpio"""
    col_spacer1, col_content, col_spacer2 = st.columns([1, 1.5, 1])
    
    with col_content:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Logo centrado
        try:
            st.image(LOGO_URL, width=180)
        except:
            st.markdown("## 🌱 SAVA Agro-Insight")
        
        st.markdown("### Bienvenido al Sistema Pro")
        st.markdown("Gestión inteligente de riesgos agroindustriales.")
        
        tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
        
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Usuario o Email")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
                if submit:
                    if username and password:
                        success, user_data, message = authenticate_user(username, password)
                        if success:
                            st.session_state['user'] = user_data
                            st.success(message)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Por favor completa los campos.")

        with tab_register:
            with st.form("register_form"):
                new_user = st.text_input("Nuevo Usuario")
                new_email = st.text_input("Email")
                new_pass = st.text_input("Contraseña", type="password", help="Mínimo 6 caracteres")
                new_pass_conf = st.text_input("Confirmar Contraseña", type="password")
                submit_reg = st.form_submit_button("Crear Cuenta", use_container_width=True)
                
                if submit_reg:
                    if new_pass != new_pass_conf:
                        st.error("Las contraseñas no coinciden")
                    elif len(new_pass) < 6:
                        st.error("Mínimo 6 caracteres requeridos")
                    elif new_user and new_email:
                        success, msg = register_user(new_user, new_email, new_pass)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Completa todos los campos.")

# --- SIDEBAR OPTIMIZADO ---

def render_sidebar(use_cache=True, use_smart_batch=False):
    """Renderiza sidebar organizado por secciones lógicas"""
    
    # 1. Header / Logo
    with st.sidebar:
        try:
            st.image(LOGO_URL, use_container_width=True)
        except:
            st.markdown("## 🌱 **SAVA Pro**")
        
        st.markdown("---")

        # 2. Sección de Usuario
        if is_authenticated():
            user = get_current_user()
            st.markdown("#### 👤 Perfil")
            st.markdown(f"**{user.get('username', 'Usuario')}**")
            st.caption(f"{user.get('email', '')}")
            
            # Botón Cerrar Sesión - Restaurado y funcional
            if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
                logout()
                st.session_state.clear()
                st.rerun()
        else:
            st.info("Modo Invitado (Local)")
            if st.button("🔐 Iniciar Sesión"):
                st.session_state['show_login'] = True
                st.rerun()
        
        st.markdown("---")

        # 3. Configuración de Análisis
        st.markdown("#### ⚙️ Configuración")
        
        # Toggle caché
        new_use_cache = st.checkbox(
            "Activado Caché", 
            value=use_cache, 
            help="Ahorra costos de API guardando resultados."
        )
        
        # Toggle Batch
        new_use_smart = st.checkbox(
            "Modo Batch Smart", 
            value=use_smart_batch,
            help="Procesa múltiples noticias en una sola llamada."
        )
        
        # Estado de conexión
        st.markdown("<br>", unsafe_allow_html=True)
        cols_status = st.columns(2)
        with cols_status[0]:
            if "firebase_credentials" in st.secrets:
                st.caption("☁️ Online")
            else:
                st.caption("💻 Local")
        
        with cols_status[1]:
            # Stats caché compactas
            try:
                cm = CacheManager()
                stats = cm.get_stats()
                count = stats.get('total_entries', 0)
                st.caption(f"📦 {count} items")
            except:
                st.caption("📦 0 items")

        st.markdown("---")

        # 4. Acciones de Sistema (Zona de Peligro/Mantenimiento)
        with st.expander("🛠️ Mantenimiento", expanded=False):
            st.caption("Acciones administrativas")
            
            # Botón Limpiar Caché - Restaurado y funcional
            if st.button("🗑️ Limpiar Caché", use_container_width=True, help="Elimina datos antiguos (>30 días)"):
                try:
                    cm = CacheManager()
                    deleted = cm.clear_old_entries(30)
                    st.toast(f"✅ Caché optimizado: {deleted} registros eliminados.", icon="🧹")
                    time.sleep(1) # Dar tiempo para leer
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    return new_use_cache, new_use_smart

# --- APLICACIÓN PRINCIPAL ---

def main():
    # Gestión de Estado Inicial
    if 'show_login' not in st.session_state:
        firebase_configured = "firebase_credentials" in st.secrets or "firebase" in st.secrets
        st.session_state['show_login'] = firebase_configured
    
    if 'user' not in st.session_state:
        st.session_state['user'] = None

    # Verificación Auth (Si hay firebase)
    firebase_configured = "firebase_credentials" in st.secrets or "firebase" in st.secrets
    
    if firebase_configured:
        if not is_authenticated() and st.session_state.get('show_login', True):
            show_login_page()
            return
        if is_authenticated():
            st.session_state['show_login'] = False
    else:
        # Modo Local Dummy
        if not st.session_state['user']:
            st.session_state['user'] = {'username': 'Admin Local', 'email': 'local@admin.com', 'role': 'admin'}

    # Renderizar Sidebar
    use_cache, use_smart_batch = render_sidebar(
        st.session_state.get('use_cache', True),
        st.session_state.get('use_smart_batch', True)
    )
    st.session_state['use_cache'] = use_cache
    st.session_state['use_smart_batch'] = use_smart_batch

    # --- HEADER PRINCIPAL ---
    user = get_current_user()
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title("📊 SAVA Agro-Insight Pro")
        st.caption(f"Bienvenido, **{user.get('username')}**. Sistema de inteligencia agroindustrial v2.1")
    with col_head2:
        # Botón de ayuda discreto
        with st.popover("ℹ️ Ayuda"):
            st.markdown("""
            **Guía Rápida:**
            1. **Carga CSV** o busca **Noticias en Vivo**.
            2. Analiza con IA.
            3. Explora **Mapas**, **Tendencias** y **Alertas**.
            4. Exporta tu reporte.
            """)

    # --- NAVEGACIÓN ---
    tabs = st.tabs([
        "📂 Análisis", 
        "🌐 Radar Vivo", 
        "🗺️ Mapas", 
        "🤖 Chatbot", 
        "📈 Tendencias", 
        "🔔 Alertas", 
        "📊 Dashboard", 
        "📄 Exportar",
        "🗄️ Historial"
    ])

    # Inicialización de módulos
    analyzer = AgroSentimentAnalyzer()
    geo_mapper = NewsGeoMapper()
    trend_analyzer = TrendAnalyzer()
    alert_system = AlertSystem()
    exporter = ReportExporter()
    chatbot = AgriNewsBot(analyzer.api_key) if analyzer.api_key else None

    # === TAB 1: ANÁLISIS CSV ===
    with tabs[0]:
        col_up, col_act = st.columns([2, 1])
        with col_up:
            uploaded_file = st.file_uploader("Cargar Dataset (CSV)", type=["csv"])
        
        with col_act:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"🚀 Modo Optimizado: {'Activo' if use_cache else 'Inactivo'}")

        if uploaded_file:
            df, error = load_and_validate_csv(uploaded_file)
            if error:
                st.error(error)
            else:
                with st.expander(f"👁️ Vista Previa ({len(df)} registros)", expanded=False):
                    st.dataframe(df.head(), use_container_width=True)
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("🧠 Iniciar Análisis IA", type="primary", use_container_width=True):
                        if analyzer.api_key:
                            with st.spinner("Procesando noticias..."):
                                prog_bar = st.progress(0)
                                sents, expls = analyzer.analyze_batch(df, prog_bar, use_smart_batch=use_smart_batch)
                                df['sentimiento_ia'] = sents
                                df['explicacion_ia'] = expls
                                st.session_state['last_analysis'] = df
                                st.success("¡Análisis completado!")
                        else:
                            st.error("Falta API Key en secrets.toml")
                
                with col_b2:
                    if 'last_analysis' in st.session_state:
                        if st.button("💾 Guardar Resultados", use_container_width=True):
                            ok, msg = save_analysis_results(st.session_state['last_analysis'])
                            if ok: st.toast(msg, icon="✅")
                            else: st.error(msg)

        # Mostrar Resultados
        if 'last_analysis' in st.session_state:
            df_res = st.session_state['last_analysis']
            st.markdown("### Resultados Recientes")
            
            # Métricas Compactas
            c1, c2, c3, c4 = st.columns(4)
            tot = len(df_res)
            pos = len(df_res[df_res['sentimiento_ia'] == 'Positivo'])
            neg = len(df_res[df_res['sentimiento_ia'] == 'Negativo'])
            neu = len(df_res[df_res['sentimiento_ia'] == 'Neutro'])
            
            c1.metric("Total", tot)
            c2.metric("Positivas", pos, f"{pos/tot*100:.1f}%")
            c3.metric("Negativas", neg, f"{neg/tot*100:.1f}%", delta_color="inverse")
            c4.metric("Neutras", neu, f"{neu/tot*100:.1f}%", delta_color="off")

            st.markdown("---")
            # Lista Compacta de Noticias
            for idx, row in df_res.iterrows():
                color = {"Positivo":"green", "Negativo":"red", "Neutro":"grey"}.get(row.get('sentimiento_ia'), "grey")
                with st.expander(f":{color}[{row.get('sentimiento_ia')}] {row.get('titular', 'Sin Titular')}"):
                    c_txt, c_meta = st.columns([3,1])
                    with c_txt:
                        st.markdown(f"**Análisis:** {row.get('explicacion_ia')}")
                        st.text(row.get('cuerpo')[:300] + "...")
                    with c_meta:
                        st.caption(f"Fecha: {row.get('fecha')}")
                        st.caption(f"ID: {row.get('id_original')}")

    # === TAB 2: RADAR VIVO ===
    with tabs[1]:
        c_search, c_num = st.columns([3, 1])
        with c_search:
            query = st.text_input("Buscar en web", value="agroindustria Valle del Cauca")
        with c_num:
            limit = st.number_input("Límite", 3, 15, 5)
        
        if st.button("📡 Escanear Web", type="primary"):
            with st.spinner("Buscando y analizando..."):
                res = analyzer.search_and_analyze_web(query, limit)
                if res:
                    st.session_state['web_analysis'] = pd.DataFrame(res)
                    st.rerun()
                else:
                    st.warning("No se encontraron resultados.")

        if 'web_analysis' in st.session_state:
            df_web = st.session_state['web_analysis']
            st.success(f"Se encontraron {len(df_web)} noticias.")
            for i, row in df_web.iterrows():
                color = {"Positivo":"green", "Negativo":"red", "Neutro":"grey"}.get(row['sentimiento_ia'], "grey")
                st.markdown(f"""
                <div style="padding:10px; border-radius:5px; border-left:5px solid {color}; background:white; margin-bottom:10px; box-shadow:0 1px 2px rgba(0,0,0,0.1);">
                    <h5 style="margin:0;">{row['titular']}</h5>
                    <small style="color:#666;">{row['fecha']} | {row['fuente']}</small>
                    <p style="margin:5px 0;">{row['explicacion_ia']}</p>
                    <a href="{row['url']}" target="_blank" style="font-size:0.8rem;">Leer original</a>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("💾 Guardar Radar"):
                ok, msg = save_analysis_results(df_web, "noticias_web")
                if ok: st.toast(msg)

    # === TAB 3: MAPAS ===
    with tabs[2]:
        data = st.session_state.get('last_analysis')
        if data is None: data = st.session_state.get('web_analysis')
        
        if data is not None and not data.empty:
            c_opt, c_gen = st.columns([3,1])
            with c_opt:
                tipo_mapa = st.radio("Visualización", ["📍 Marcadores", "🔥 Calor (Riesgos)"], horizontal=True)
            with c_gen:
                st.markdown("<br>", unsafe_allow_html=True)
                gen_map = st.button("Actualizar Mapa", use_container_width=True)
            
            if gen_map or 'current_map' not in st.session_state:
                try:
                    if "Calor" in tipo_mapa:
                        m = geo_mapper.create_heatmap(data)
                    else:
                        m = geo_mapper.create_news_map(data)
                    st.session_state['current_map'] = m
                except Exception as e:
                    st.error(f"Error mapa: {e}")

            if 'current_map' in st.session_state:
                st_folium(st.session_state['current_map'], width="100%", height=500)
        else:
            st.info("Realiza un análisis primero para ver el mapa.")

    # === TAB 4: CHATBOT ===
    with tabs[3]:
        if not chatbot:
            st.error("Configura la API Key para usar el chat.")
        else:
            data = st.session_state.get('last_analysis')
            if data is None: data = st.session_state.get('web_analysis')
            
            if data is not None:
                chatbot.load_news_database(data)
                
                # Historial de chat visual
                for msg in st.session_state.get('chat_history', []):
                    role_class = "user-message" if msg['role'] == 'user' else "bot-message"
                    st.markdown(f"""
                    <div class="chat-message {role_class}">
                        <b>{'👤 Tú' if msg['role']=='user' else '🤖 IA'}:</b>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Input Area
                with st.form("chat_form", clear_on_submit=True):
                    u_in = st.text_input("Pregunta sobre las noticias...")
                    enviar = st.form_submit_button("Enviar")
                
                if enviar and u_in:
                    # Guardar usuario
                    hist = st.session_state.get('chat_history', [])
                    hist.append({'role': 'user', 'content': u_in})
                    
                    # Respuesta IA
                    with st.spinner("Pensando..."):
                        resp = chatbot.chat(u_in)
                        hist.append({'role': 'assistant', 'content': resp['response']})
                    
                    st.session_state['chat_history'] = hist
                    st.rerun()
                
                if st.button("Borrar Chat", type="secondary"):
                    st.session_state['chat_history'] = []
                    chatbot.reset_conversation()
                    st.rerun()
            else:
                st.warning("Carga datos para hablar con ellos.")

    # === TAB 5: TENDENCIAS ===
    with tabs[4]:
        data = st.session_state.get('last_analysis') or st.session_state.get('web_analysis')
        if data is not None:
            trend_analyzer.load_data(data)
            
            st.markdown("#### Resumen Ejecutivo")
            st.info(trend_analyzer.generate_executive_summary())
            
            c_risk, c_opp = st.columns(2)
            risk = trend_analyzer.get_risk_score()
            opp = trend_analyzer.get_opportunities_score()
            
            c_risk.metric("Nivel de Riesgo", f"{risk['score']}%", risk['level'])
            c_opp.metric("Oportunidades", f"{opp['score']}%", opp['level'])
            
            st.markdown("#### Palabras Clave")
            ck1, ck2 = st.columns(2)
            with ck1:
                kw_neg = pd.DataFrame(trend_analyzer.extract_keywords('Negativo', 8), columns=['Term', 'Freq'])
                if not kw_neg.empty:
                    fig = px.bar(kw_neg, x='Freq', y='Term', orientation='h', title="Top Riesgos", color_discrete_sequence=['#e53935'])
                    st.plotly_chart(fig, use_container_width=True)
            with ck2:
                kw_pos = pd.DataFrame(trend_analyzer.extract_keywords('Positivo', 8), columns=['Term', 'Freq'])
                if not kw_pos.empty:
                    fig = px.bar(kw_pos, x='Freq', y='Term', orientation='h', title="Top Oportunidades", color_discrete_sequence=['#43a047'])
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos para tendencias.")

    # === TAB 6: ALERTAS ===
    with tabs[5]:
        data = st.session_state.get('last_analysis') or st.session_state.get('web_analysis')
        if data is not None:
            if st.button("🔍 Escanear Alertas", use_container_width=True):
                alerts = alert_system.analyze_and_generate_alerts(data)
                st.session_state['alerts'] = alerts
            
            if 'alerts' in st.session_state:
                alerts = st.session_state['alerts']
                if not alerts:
                    st.success("✅ No se detectaron alertas críticas.")
                else:
                    for alert in alerts:
                        color = "#e53935" if alert['severity'] == 'critical' else "#fb8c00" if alert['severity'] == 'high' else "#1e88e5"
                        icon = "🚨" if alert['severity'] == 'critical' else "⚠️"
                        st.markdown(f"""
                        <div style="border-left: 4px solid {color}; background: white; padding: 15px; margin-bottom: 10px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <h4 style="margin:0; color:{color};">{icon} {alert['title']}</h4>
                            <p style="margin:5px 0;">{alert['message']}</p>
                            <small><b>Recomendación:</b> {alert['recommendation']}</small>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("Sin datos para alertas.")

    # === TAB 7: DASHBOARD ===
    with tabs[6]:
        data = st.session_state.get('last_analysis') or st.session_state.get('web_analysis')
        if data is not None:
            c_pie, c_bar = st.columns(2)
            
            # Pie Chart
            fig_pie = px.pie(data, names='sentimiento_ia', title='Distribución Global',
                             color='sentimiento_ia',
                             color_discrete_map={'Positivo':'#43a047', 'Negativo':'#e53935', 'Neutro':'#757575'})
            c_pie.plotly_chart(fig_pie, use_container_width=True)
            
            # Timeline (si hay fechas)
            try:
                if 'fecha' in data.columns:
                    # Simple conversion attempt
                    data['dt'] = pd.to_datetime(data['fecha'], errors='coerce')
                    df_time = data.dropna(subset=['dt']).sort_values('dt')
                    if not df_time.empty:
                        fig_line = px.histogram(df_time, x='dt', color='sentimiento_ia', title='Evolución Temporal',
                                                color_discrete_map={'Positivo':'#43a047', 'Negativo':'#e53935', 'Neutro':'#757575'})
                        c_bar.plotly_chart(fig_line, use_container_width=True)
            except:
                st.caption("No se pudieron procesar las fechas para la línea de tiempo.")
        else:
            st.info("Sin datos para dashboard.")

    # === TAB 8: EXPORTAR ===
    with tabs[7]:
        data = st.session_state.get('last_analysis') or st.session_state.get('web_analysis')
        if data is not None:
            st.markdown("#### Selecciona Formato")
            c_pdf, c_xls, c_csv = st.columns(3)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            with c_pdf:
                if st.button("📕 PDF Ejecutivo", use_container_width=True):
                    pdf = exporter.export_to_pdf(data)
                    st.download_button("Descargar PDF", pdf, f"Reporte_{timestamp}.pdf", "application/pdf", use_container_width=True)
            
            with c_xls:
                if st.button("📗 Excel Completo", use_container_width=True):
                    xls = exporter.export_to_excel(data)
                    st.download_button("Descargar Excel", xls, f"Data_{timestamp}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            
            with c_csv:
                csv = data.to_csv(index=False).encode('utf-8')
                st.download_button("📄 CSV Simple", csv, f"Raw_{timestamp}.csv", "text/csv", use_container_width=True)
        else:
            st.info("Sin datos para exportar.")

    # === TAB 9: HISTORIAL ===
    with tabs[8]:
        if st.button("🔄 Cargar Historial Cloud", use_container_width=True):
            h_data = fetch_history(limit=50)
            if h_data:
                df_h = pd.DataFrame(h_data)
                st.dataframe(df_h, use_container_width=True)
            else:
                st.warning("No se encontró historial o no hay conexión.")

if __name__ == "__main__":
    main()
