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
from html import escape as html_escape

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
    
    /* Tipografía mejorada - Más compacta */
    h1 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
        color: #1a1a2e !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0 !important;
    }
    
    h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
        color: #1a1a2e !important;
        margin-top: 1rem !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0 !important;
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
    
    /* Ocultar botón de toggle del sidebar */
    button[kind="header"] {
        display: none !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    [data-testid="stHeader"] button {
        display: none !important;
    }
    /* Ocultar icono de menú del sidebar */
    [data-testid="stSidebar"] [data-testid="collapsedControl"],
    [data-testid="stSidebar"] button[title*="close"],
    [data-testid="stSidebar"] button[aria-label*="Close"],
    button[title="Close sidebar"],
    button[aria-label="Close sidebar"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* Ocultar keyboard_double_arrow_right y todos los iconos de flecha - MÁS AGRESIVO */
    .keyboard_double_arrow_right,
    .keyboard_arrow_right,
    .keyboard_arrow_down,
    .keyboard_arrow_up,
    [data-testid*="arrow"],
    svg[data-testid*="arrow"],
    svg[class*="arrow"],
    .material-icons[class*="arrow"],
    /* Ocultar cualquier elemento que contenga texto "keyboard" */
    span[class*="keyboard"],
    div[class*="keyboard"],
    p[class*="keyboard"],
    label[class*="keyboard"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        font-size: 0 !important;
        line-height: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        left: -9999px !important;
    }
    /* Ocultar controles de expansión del sidebar */
    section[data-testid="stSidebar"] > div:first-child button {
        display: none !important;
    }
    
    /* Botones del sidebar mejorados - Mejor contraste */
    [data-testid="stSidebar"] .stButton>button {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
        width: 100% !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.3s ease !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255, 255, 255, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.6) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.35) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* Botones secundarios del sidebar - Cerrar sesión, limpiar caché - VISIBLES */
    [data-testid="stSidebar"] .stButton>button[kind="secondary"],
    [data-testid="stSidebar"] button[key="btn_logout_sidebar"],
    [data-testid="stSidebar"] button[key="btn_clear_cache"] {
        background: rgba(231, 76, 60, 0.4) !important;
        color: #ffffff !important;
        border: 2px solid rgba(231, 76, 60, 0.8) !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5) !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        margin: 8px 0 !important;
        width: 100% !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 100 !important;
        position: relative !important;
    }
    [data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover,
    [data-testid="stSidebar"] button[key="btn_logout_sidebar"]:hover,
    [data-testid="stSidebar"] button[key="btn_clear_cache"]:hover {
        background: rgba(231, 76, 60, 0.6) !important;
        border-color: rgba(231, 76, 60, 1) !important;
        color: #ffffff !important;
        text-shadow: 0 2px 5px rgba(0, 0, 0, 0.6) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Botones primarios del sidebar */
    [data-testid="stSidebar"] .stButton>button[type="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stSidebar"] .stButton>button[type="primary"]:hover {
        background: linear-gradient(135deg, #7c8ef0 0%, #8659b2 100%) !important;
    }
    
    /* Inputs del sidebar */
    [data-testid="stSidebar"] .stTextInput>div>div>input,
    [data-testid="stSidebar"] .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] .stTextInput>div>div>input:focus,
    [data-testid="stSidebar"] .stTextArea>div>div>textarea:focus {
        border-color: rgba(255, 255, 255, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Labels del sidebar */
    [data-testid="stSidebar"] label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 500 !important;
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
    
    /* Tarjetas de noticias mejoradas - Más anchas y claras */
    .news-card {
        background: white !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        border-left: 5px solid !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    .news-card:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12) !important;
        transform: translateY(-2px) !important;
    }
    .news-card-positive {
        border-left-color: #27ae60 !important;
        background: linear-gradient(90deg, #ffffff 0%, #f0fdf4 100%) !important;
    }
    .news-card-negative {
        border-left-color: #e74c3c !important;
        background: linear-gradient(90deg, #ffffff 0%, #fef2f2 100%) !important;
    }
    .news-card-neutral {
        border-left-color: #95a5a6 !important;
        background: linear-gradient(90deg, #ffffff 0%, #f8f9fa 100%) !important;
    }
    
    /* Badge de sentimiento */
    .sentiment-badge {
        display: inline-block !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: 0.3px !important;
        margin-bottom: 10px !important;
    }
    .sentiment-badge-positive {
        background: #27ae60 !important;
        color: white !important;
    }
    .sentiment-badge-negative {
        background: #e74c3c !important;
        color: white !important;
    }
    .sentiment-badge-neutral {
        background: #95a5a6 !important;
        color: white !important;
    }
    
    /* Título de noticia */
    .news-title {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #1a1a2e !important;
        margin-bottom: 10px !important;
        line-height: 1.4 !important;
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Cuerpo de noticia */
    .news-body {
        font-size: 15px !important;
        color: #4a5568 !important;
        line-height: 1.6 !important;
        margin-bottom: 12px !important;
    }
    
    /* Explicación IA */
    .news-analysis {
        font-size: 14px !important;
        color: #718096 !important;
        font-style: italic !important;
        padding: 10px !important;
        background: rgba(102, 126, 234, 0.05) !important;
        border-radius: 8px !important;
        border-left: 3px solid #667eea !important;
    }
    
    /* === OCULTAR ICONOS DE EXPANDER Y EVITAR SOLAPAMIENTO === */
    
    /* Ocultar completamente el header del expander */
    .streamlit-expanderHeader {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        left: -9999px !important;
        width: 0 !important;
    }
    
    /* Ocultar específicamente el icono keyboard_arrow_right y cualquier texto relacionado */
    .streamlit-expanderHeader svg,
    .streamlit-expanderHeader [data-testid*="arrow"],
    .streamlit-expanderHeader .keyboard_arrow_right,
    .streamlit-expanderHeader .keyboard_arrow_down,
    .streamlit-expanderHeader .keyboard_arrow_up,
    svg[data-testid*="arrow"],
    .keyboard_arrow_right,
    .keyboard_arrow_down,
    .keyboard_arrow_up,
    /* Ocultar cualquier texto que contenga "keyboard" */
    *:contains("keyboard_arrow_right"),
    *:contains("keyboard_arrow_down"),
    *:contains("keyboard_arrow_up"),
    *:contains("keyboard") {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        font-size: 0 !important;
        line-height: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        left: -9999px !important;
    }
    
    /* Ocultar cualquier texto o icono dentro del expander header - MÁS AGRESIVO */
    .streamlit-expanderHeader *,
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader span,
    .streamlit-expanderHeader div,
    .streamlit-expanderHeader label {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
        line-height: 0 !important;
        height: 0 !important;
        width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        left: -9999px !important;
    }
    
    /* Ocultar específicamente texto que contenga "keyboard" usando selectores de atributo */
    [class*="keyboard"],
    [id*="keyboard"],
    [data-testid*="keyboard"],
    span:contains("keyboard"),
    div:contains("keyboard"),
    p:contains("keyboard"),
    label:contains("keyboard") {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        position: absolute !important;
        left: -9999px !important;
    }
    
    /* Asegurar que el contenido del expander tenga espaciado adecuado */
    .streamlit-expanderContent {
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
        padding: 1rem !important;
    }
    
    /* Asegurar que los botones no se solapen con expanders - COMPACTO */
    .stButton {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        clear: both !important;
        position: relative !important;
        z-index: 10 !important;
    }
    
    /* Espaciado adicional después de expanders */
    .element-container:has(.streamlit-expander) {
        margin-bottom: 1.5rem !important;
    }
    
    /* Asegurar que los botones tengan espacio suficiente y no se solapen - COMPACTO */
    [data-testid="column"] .stButton {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        padding: 0.2rem 0 !important;
    }
    
    /* Asegurar que no haya texto flotante sobre los botones */
    .stButton button {
        position: relative !important;
        z-index: 100 !important;
        overflow: visible !important;
    }
    
    /* Ocultar cualquier elemento que pueda interferir con los botones */
    .stButton::before,
    .stButton::after {
        content: none !important;
    }
    
    /* Asegurar que los expanders no interfieran con elementos siguientes */
    .streamlit-expander {
        margin-bottom: 1.5rem !important;
        clear: both !important;
    }
    
    /* Ocultar cualquier texto o elemento que aparezca como "keyboard_arrow_right" */
    text,
    tspan,
    .material-icons,
    [class*="material"],
    [class*="icon"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Asegurar que el contenido dentro de columnas no se solape */
    [data-testid="column"] {
        padding: 0 0.75rem !important;
        margin-bottom: 1rem !important;
        clear: both !important;
    }
    
    /* Espaciado entre elementos - MUY COMPACTO */
    .element-container {
        margin-bottom: 0.4rem !important;
        clear: both !important;
    }
    
    /* Reducir espaciado en separadores */
    hr {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Métricas más compactas */
    [data-testid="stMetricContainer"] {
        padding: 10px 12px !important;
        margin: 4px 0 !important;
    }
    
    /* Reducir espaciado en columnas */
    [data-testid="column"] {
        padding: 0 0.5rem !important;
    }
    
    /* Espaciado compacto en tabs */
    .stTabs {
        margin-bottom: 0.5rem !important;
    }
    
    /* Reducir padding en tarjetas de noticias */
    .news-card {
        padding: 12px !important;
        margin-bottom: 8px !important;
    }
    
    /* Reducir espaciado en párrafos y texto */
    .stMarkdown p {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en inputs */
    .stTextInput,
    .stTextArea {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en checkboxes y radio buttons */
    .stCheckbox,
    .stRadio {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Reducir espaciado en info boxes */
    .stInfo,
    .stSuccess,
    .stWarning,
    .stError {
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
        padding: 0.6rem 0.8rem !important;
    }
    
    /* Reducir espaciado en dataframes - Asegurar visibilidad COMPLETA */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] *,
    .stDataFrame,
    .stDataFrame * {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 100% !important;
        height: auto !important;
        overflow: visible !important;
    }
    
    /* Asegurar que las tablas dentro de dataframes sean visibles */
    [data-testid="stDataFrame"] table,
    .stDataFrame table {
        display: table !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 100% !important;
    }
    
    /* Asegurar que las celdas de tabla sean visibles */
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] th,
    .stDataFrame td,
    .stDataFrame th {
        display: table-cell !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Reducir espaciado en spinners */
    .stSpinner {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en progress bars */
    .stProgress {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en separadores horizontales (---) */
    hr,
    .stMarkdown hr {
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
        border: none !important;
        border-top: 1px solid #e0e0e0 !important;
    }
    
    /* Reducir espaciado en subheaders y títulos */
    h3, h4, h5, h6 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en contenedores de gráficas */
    [data-testid="stPlotlyChart"] {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en captions */
    .stCaption {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Reducir espaciado en expanders */
    .streamlit-expander {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en file uploader */
    .stFileUploader {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en selectboxes y multiselect */
    .stSelectbox,
    .stMultiselect {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en number input */
    .stNumberInput {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en sliders */
    .stSlider {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en containers */
    .stContainer {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Reducir espaciado en columnas cuando tienen contenido */
    [data-testid="column"] > div {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Reducir altura de saltos de línea <br> */
    br {
        line-height: 0.3 !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
        content: "" !important;
    }
    
    /* Reducir espaciado en todos los elementos markdown */
    .stMarkdown {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Reducir espaciado en divs vacíos o con solo espacios */
    div:empty,
    p:empty {
        margin: 0 !important;
        padding: 0 !important;
        height: 0 !important;
    }
    
    /* Mejorar visualización de noticias - Ancho completo */
    .element-container {
        max-width: 100% !important;
    }
    
    /* Contenedor principal más ancho y compacto */
    .main .block-container {
        max-width: 1200px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    
    /* Tarjetas de noticias con mejor espaciado */
    .news-card {
        margin-bottom: 20px !important;
    }
    
    /* Asegurar que el texto del sidebar sea completamente visible */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Mejorar visibilidad de métricas */
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: rgba(255, 255, 255, 0.95) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Mejorar visibilidad de info/warning/success en sidebar */
    [data-testid="stSidebar"] .stSuccess,
    [data-testid="stSidebar"] .stInfo,
    [data-testid="stSidebar"] .stWarning {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    /* Ocultar todos los iconos de toggle del sidebar */
    button[data-baseweb="button"][aria-label*="Close"],
    button[data-baseweb="button"][aria-label*="close"],
    button[title*="Close"],
    button[title*="close"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }
    </style>
    
    <script>
    // Ocultar dinámicamente cualquier texto que contenga "keyboard"
    function hideKeyboardText() {
        // Buscar todos los elementos de texto
        const allElements = document.querySelectorAll('*');
        allElements.forEach(function(element) {
            // Verificar si el elemento contiene texto "keyboard"
            if (element.children.length === 0 && element.textContent) {
                const text = element.textContent.trim();
                if (text.includes('keyboard_arrow') || 
                    text === 'keyboard_arrow_right' || 
                    text === 'keyboard_arrow_down' || 
                    text === 'keyboard_arrow_up' ||
                    text.includes('keyboard')) {
                    element.style.display = 'none';
                    element.style.visibility = 'hidden';
                    element.style.height = '0';
                    element.style.width = '0';
                    element.style.overflow = 'hidden';
                    element.style.opacity = '0';
                    element.style.position = 'absolute';
                    element.style.left = '-9999px';
                }
            }
        });
    }
    
    // Ejecutar al cargar la página
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', hideKeyboardText);
    } else {
        hideKeyboardText();
    }
    
    // Ejecutar después de cada actualización de Streamlit
    setTimeout(hideKeyboardText, 100);
    setTimeout(hideKeyboardText, 500);
    setTimeout(hideKeyboardText, 1000);
    
    // Observar cambios en el DOM
    const observer = new MutationObserver(hideKeyboardText);
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
    </script>
""", unsafe_allow_html=True)

# Funciones de autenticación
def show_login_page():
    """Muestra la página de login/registro"""
    # Centrar el logo y contenido
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Logo SAVA - CENTRADO
        try:
            st.image(LOGO_URL, width=150, use_container_width=False)
        except:
            try:
                st.image(LOGO_COLIBRI_URL, width=150, use_container_width=False)
            except:
                st.markdown("## 🌱 SAVA")
        
        # Centrar el texto
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("### 🌱 SAVA Agro-Insight PRO")
        st.markdown("**Sistema Inteligente de Análisis de Riesgos Agroindustriales**")
        st.markdown("</div>", unsafe_allow_html=True)
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
    
    # Información del usuario
    if is_authenticated():
        user = get_current_user()
        st.markdown(f"### 👤 {user['username']}")
        st.markdown(f"📧 {user['email']}")
        # Botón Cerrar Sesión - VISIBLE Y FUNCIONAL
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary", key="btn_logout_sidebar"):
            try:
                logout()
                st.session_state['user'] = None
                st.success("✅ Sesión cerrada correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"Error al cerrar sesión: {str(e)}")
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
    try:
        cache_stats = cache_mgr.get_stats()
        if cache_stats is None:
            cache_stats = {'total_entries': 0, 'total_hits': 0}
    except Exception as e:
        cache_stats = {'total_entries': 0, 'total_hits': 0}
    
    with col_cache:
        if cache_stats.get('total_entries', 0) > 0:
            st.info(f"🚀 {cache_stats.get('total_entries', 0)} cached")
        else:
            st.info("📦 Caché vacío")
    
    st.markdown("---")
    
    # Opciones de configuración
    st.markdown("### ⚙️ Configuración")
    use_cache = st.checkbox("Usar caché inteligente", value=use_cache, help="Reduce consumo de API hasta 80%")
    use_smart_batch = st.checkbox("Batch inteligente", value=use_smart_batch, help="Procesa múltiples noticias por prompt")
    
    # Botón Limpiar Caché - VISIBLE Y FUNCIONAL
    if st.button("🗑️ Limpiar caché", use_container_width=True, type="secondary", key="btn_clear_cache"):
        try:
            deleted = cache_mgr.clear_old_entries(max_age_days=30)
            st.success(f"✅ {deleted} entradas eliminadas")
            st.rerun()
        except Exception as e:
            st.error(f"Error al limpiar caché: {str(e)}")
    
    st.markdown("---")
    st.caption("Desarrollado con ❤️ por SAVA Team")
    st.caption("Optimizado para reducir costos de API")
    
    return use_cache, use_smart_batch

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
    user = get_current_user()
    st.title("📊 SAVA Agro-Insight PRO")
    st.markdown(f"*Bienvenido, {user['username'] if user else 'Usuario'}* | Sistema Inteligente de Análisis de Riesgos Agroindustriales")
    
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
                
                # Vista previa mejorada - Usar botón para mostrar datos
                if 'show_preview_data' not in st.session_state:
                    st.session_state['show_preview_data'] = False
                
                if st.button("👁️ Mostrar Vista Previa de Datos", key="btn_show_preview"):
                    st.session_state['show_preview_data'] = True
                
                if st.session_state['show_preview_data']:
                    # Mostrar el dataframe directamente
                    if df is not None and len(df) > 0:
                        if 'titular' in df.columns and 'fecha' in df.columns:
                            preview_df = df[['titular', 'fecha']].head(10)
                        else:
                            preview_df = df.head(10)
                        
                        if len(preview_df) > 0:
                            st.dataframe(preview_df)
                        else:
                            st.info("No hay datos para mostrar")
                    else:
                        st.warning("El dataframe está vacío")
                
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
                    # Mostrar estadísticas de caché de forma segura
                    try:
                        cache_mgr_temp = CacheManager()
                        cache_stats_temp = cache_mgr_temp.get_stats()
                        if cache_stats_temp is None:
                            cache_stats_temp = {'total_entries': 0, 'total_hits': 0, 'cache_hit_rate': '0%', 'distribution': {}}
                    except Exception as e:
                        cache_stats_temp = {'total_entries': 0, 'total_hits': 0, 'cache_hit_rate': '0%', 'distribution': {}}
                    
                    st.markdown("### 📊 Estadísticas de Caché")
                    st.markdown("---")
                    col_stat1, col_stat2 = st.columns(2)
                    with col_stat1:
                        st.metric("Total Entradas", cache_stats_temp.get('total_entries', 0))
                        st.metric("Total Hits", cache_stats_temp.get('total_hits', 0))
                    with col_stat2:
                        hit_rate = cache_stats_temp.get('cache_hit_rate', '0%')
                        st.metric("Hit Rate", hit_rate if isinstance(hit_rate, str) else f"{hit_rate}%")
                    
                    if cache_stats_temp.get('distribution'):
                        st.markdown("---")
                        st.markdown("**📊 Distribución por Sentimiento:**")
                        for sent, count in cache_stats_temp['distribution'].items():
                            st.write(f"- **{sent}:** {count} noticias")
                
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
            
            # Resultados en tarjetas mejoradas - Más anchas y claras
            for index, row in df_res.iterrows():
                sentimiento = row.get('sentimiento_ia', 'Neutro')
                titular = str(row.get('titular', 'Sin título'))
                cuerpo = str(row.get('cuerpo', ''))
                explicacion = str(row.get('explicacion_ia', 'Análisis automático'))
                fecha = str(row.get('fecha', 'N/A'))
                
                # Determinar clase CSS y badge según sentimiento
                if sentimiento == "Positivo":
                    card_class = "news-card-positive"
                    badge_class = "sentiment-badge-positive"
                    emoji = "🟢"
                    label = "POSITIVO"
                elif sentimiento == "Negativo":
                    card_class = "news-card-negative"
                    badge_class = "sentiment-badge-negative"
                    emoji = "🔴"
                    label = "NEGATIVO"
                else:
                    card_class = "news-card-neutral"
                    badge_class = "sentiment-badge-neutral"
                    emoji = "⚪"
                    label = "NEUTRO"
                
                # Crear tarjeta de noticia con HTML personalizado - Mejorada
                # Escapar caracteres HTML especiales
                titular_escaped = html_escape(titular)
                cuerpo_escaped = html_escape(str(cuerpo))
                explicacion_escaped = html_escape(explicacion)
                
                st.markdown(f"""
                <div class="news-card {card_class}" style="width: 100%; margin: 15px 0;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                        <span class="sentiment-badge {badge_class}">{emoji} {label}</span>
                    </div>
                    <div class="news-title" style="font-size: 20px; font-weight: 700; color: #1a1a2e; margin-bottom: 12px; line-height: 1.4;">
                        {titular_escaped}
                    </div>
                    <div class="news-body" style="font-size: 15px; color: #4a5568; line-height: 1.7; margin-bottom: 15px; max-height: none;">
                        {cuerpo_escaped}
                    </div>
                    <div class="news-analysis" style="font-size: 14px; color: #2d3748; font-style: normal; padding: 12px; background: rgba(102, 126, 234, 0.08); border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 12px;">
                        <strong>🤖 Análisis IA:</strong> {explicacion_escaped}
                    </div>
                    <div style="margin-top: 10px; font-size: 12px; color: #718096; display: flex; gap: 15px; align-items: center;">
                        <span>📅 {fecha}</span>
                        <span>🆔 {row.get('id_original', 'N/A')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
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
            
            # Resumen ejecutivo - Compacto
            st.markdown("### 📋 Resumen Ejecutivo")
            st.markdown(trend_analyzer.generate_executive_summary())
            
            # Índices de riesgo y oportunidades - Compacto
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
            
            # Análisis de tendencias más completo - Compacto
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
                            fig_trend.update_layout(
                                height=350,
                                margin=dict(l=50, r=20, t=50, b=40)
                            )
                            st.plotly_chart(fig_trend, use_container_width=True)
                except Exception as e:
                    st.caption(f"⚠️ No se pudo generar gráfico temporal: {e}")
            
            # Palabras clave combinadas en una sola gráfica - Compacto
            st.markdown("### 📊 Palabras Clave por Sentimiento (Top 10)")
            
            keywords_neg = trend_analyzer.extract_keywords('Negativo', top_n=10)
            keywords_pos = trend_analyzer.extract_keywords('Positivo', top_n=10)
            
            if keywords_neg or keywords_pos:
                # Combinar datos
                combined_data = []
                
                if keywords_neg:
                    for word, freq in keywords_neg:
                        combined_data.append({'Palabra': word, 'Frecuencia': freq, 'Sentimiento': 'Negativo'})
                
                if keywords_pos:
                    for word, freq in keywords_pos:
                        combined_data.append({'Palabra': word, 'Frecuencia': freq, 'Sentimiento': 'Positivo'})
                
                if combined_data:
                    df_combined = pd.DataFrame(combined_data)
                    
                    # Crear gráfica combinada
                    fig_combined = px.bar(
                        df_combined,
                        x='Frecuencia',
                        y='Palabra',
                        orientation='h',
                        color='Sentimiento',
                        color_discrete_map={'Negativo': '#e74c3c', 'Positivo': '#2ecc71'},
                        title="Top 10 Palabras Clave: Negativas vs Positivas",
                        labels={'Frecuencia': 'Frecuencia', 'Palabra': 'Palabra Clave'},
                        barmode='group'
                    )
                    
                    fig_combined.update_layout(
                        height=450,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            font=dict(size=12)
                        ),
                        margin=dict(l=100, r=20, t=50, b=30),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(size=11)
                    )
                    
                    fig_combined.update_traces(marker_line_width=0.5, marker_line_color='white')
                    st.plotly_chart(fig_combined, use_container_width=True)
            else:
                st.info("No se detectaron palabras clave")
            
            # Predicción de tendencia mejorada - Compacto
            st.markdown("### 🔮 Predicción de Tendencia")
            prediction = trend_analyzer.predict_sentiment_trend()
            if "No hay" not in prediction and "suficientes" not in prediction:
                st.success(prediction)
            else:
                st.info(prediction)
            
            # Clustering temático mejorado - Usando checkboxes en lugar de expanders
            st.markdown("### 🗂️ Agrupación Temática de Noticias")
            st.caption("Agrupa noticias similares por contenido para identificar temas principales")
            
            # Guardar clusters en session state
            if 'clusters_generated' not in st.session_state:
                st.session_state['clusters_generated'] = False
                st.session_state['df_clustered'] = None
                st.session_state['themes'] = None
            
            if st.button("🔍 Generar Clusters Temáticos", type="primary", key="btn_generate_clusters"):
                with st.spinner("Agrupando noticias por similitud temática..."):
                    try:
                        df_clustered, themes = trend_analyzer.cluster_news(n_clusters=3)
                        st.session_state['clusters_generated'] = True
                        st.session_state['df_clustered'] = df_clustered
                        st.session_state['themes'] = themes
                        st.success("✅ Clusters generados exitosamente")
                    except Exception as e:
                        st.warning(f"No hay suficientes datos para clustering: {str(e)}")
                        st.caption("💡 Se necesitan al menos 5 noticias para generar clusters")
                        st.session_state['clusters_generated'] = False
            
            # Mostrar clusters con checkboxes
            if st.session_state['clusters_generated'] and st.session_state['themes']:
                themes = st.session_state['themes']
                df_clustered = st.session_state['df_clustered']
                
                for i, theme in enumerate(themes):
                    cluster_data = df_clustered[df_clustered['cluster'] == i]
                    cluster_key = f"show_cluster_{i}"
                    
                    show_cluster = st.checkbox(
                        f"📁 **Cluster {i+1}**: {theme} ({len(cluster_data)} noticias)",
                        value=(i==0),
                        key=cluster_key
                    )
                    
                    if show_cluster:
                        st.markdown(f"**Tema principal:** {theme}")
                        st.markdown(f"**Noticias en este cluster:** {len(cluster_data)}")
                        
                        # Mostrar distribución de sentimientos en el cluster
                        sent_dist = cluster_data['sentimiento_ia'].value_counts()
                        st.write("**Distribución de sentimientos:**")
                        for sent, count in sent_dist.items():
                            st.write(f"- {sent}: {count} ({count/len(cluster_data)*100:.1f}%)")
                        
                        st.markdown("---")
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
                        
                        # Mostrar detalles adicionales si existen - Usando checkbox en lugar de expander
                        if 'details' in alert and alert['details']:
                            # Usar un checkbox para mostrar/ocultar detalles sin expander
                            details_key = f"show_details_{i}"
                            show_details = st.checkbox(f"📋 Ver detalles de {alert['title']}", key=details_key, value=False)
                            
                            if show_details:
                                st.markdown("---")
                                if isinstance(alert['details'], dict):
                                    for key, value in alert['details'].items():
                                        if isinstance(value, list):
                                            st.write(f"**{key}:**")
                                            for item in value[:5]:  # Mostrar máximo 5
                                                st.caption(f"  • {item}")
                                        else:
                                            st.write(f"**{key}:** {value}")
                                st.markdown("---")
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
        
        # Guardar historial en session state para que persista
        if 'historial_loaded' not in st.session_state:
            st.session_state['historial_loaded'] = False
            st.session_state['df_hist'] = None
        
        if st.button("🔄 Cargar Historial", key="btn_load_history"):
            with st.spinner("Cargando desde Firebase..."):
                try:
                    hist = fetch_history(limit=100)
                    
                    if hist and len(hist) > 0:
                        df_hist = pd.DataFrame(hist)
                        st.session_state['historial_loaded'] = True
                        st.session_state['df_hist'] = df_hist
                        st.success(f"✅ {len(df_hist)} registros cargados")
                    else:
                        st.warning("No hay historial disponible")
                        st.session_state['historial_loaded'] = False
                        st.session_state['df_hist'] = None
                except Exception as e:
                    st.error(f"Error al cargar historial: {str(e)}")
                    st.session_state['historial_loaded'] = False
                    st.session_state['df_hist'] = None
        
        # Mostrar historial si está cargado - Usar botón para mostrar
        if st.session_state.get('historial_loaded', False) and st.session_state.get('df_hist') is not None:
            df_hist = st.session_state['df_hist']
            
            if df_hist is not None and len(df_hist) > 0:
                # Botón para mostrar historial
                if 'show_history_data' not in st.session_state:
                    st.session_state['show_history_data'] = False
                
                if st.button("📊 Mostrar Historial", key="btn_show_history"):
                    st.session_state['show_history_data'] = True
                
                if st.session_state['show_history_data']:
                    # Filtros
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        filter_sent = st.multiselect(
                            "Filtrar por sentimiento",
                            ['Positivo', 'Negativo', 'Neutro'],
                            default=['Positivo', 'Negativo', 'Neutro'],
                            key="filter_sentiment"
                        )
                    
                    # Filtrar datos
                    if 'sentimiento' in df_hist.columns:
                        df_filtered = df_hist[df_hist['sentimiento'].isin(filter_sent)]
                    else:
                        df_filtered = df_hist
                    
                    # Mostrar dataframe directamente
                    if len(df_filtered) > 0:
                        st.dataframe(df_filtered)
                    else:
                        st.info("No hay registros que coincidan con los filtros")
            else:
                st.warning("El historial está vacío")

if __name__ == "__main__":
    main()
