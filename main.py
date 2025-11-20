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
    
    /* Tipografía mejorada */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
        color: #1a1a2e !important;
    }
    
    /* Texto general mejorado - Evitar solapamiento */
    body, .stMarkdown, p, div, span {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        line-height: 1.7 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Evitar texto superpuesto en métricas */
    [data-testid="stMetricContainer"] {
        padding: 15px !important;
        margin: 10px 0 !important;
        min-height: 80px !important;
    }
    
    [data-testid="stMetricValue"] {
        margin-bottom: 5px !important;
        padding-bottom: 5px !important;
    }
    
    [data-testid="stMetricDelta"] {
        margin-top: 5px !important;
        padding-top: 5px !important;
    }
    
    /* Evitar solapamiento en columnas */
    .stColumn {
        padding: 0 10px !important;
    }
    
    /* Mejorar espaciado en tarjetas - OPTIMIZADO */
    .element-container {
        margin-bottom: 1rem !important;
    }
    
    /* Espaciado optimizado para columnas */
    [data-testid="column"] {
        padding: 0 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Espaciado entre elementos de formulario */
    .stForm {
        margin-bottom: 1.5rem !important;
    }
    
    /* Optimizar espaciado en tabs */
    .stTabs {
        margin-bottom: 1.5rem !important;
    }
    
    /* Espaciado en expanders */
    .streamlit-expander {
        margin-bottom: 1rem !important;
    }
    
    /* Botones premium mejorados - PROFESIONAL Y COMPACTO */
    .stButton>button:not([data-testid="stSidebar"] button) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.625rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
        font-family: 'Inter', sans-serif !important;
        margin: 0.25rem 0 !important;
    }
    
    .stButton>button:not([data-testid="stSidebar"] button):hover {
        transform: translateY(-1px) scale(1.01) !important;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Botones secundarios */
    .stButton>button[kind="secondary"] {
        background: white !important;
        color: #667eea !important;
        border: 2px solid #667eea !important;
    }
    
    /* Métricas mejoradas - PROFESIONAL Y COMPACTO */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif !important;
        color: #1a1a2e !important;
        letter-spacing: -0.5px !important;
    }
    
    [data-testid="stMetricContainer"] {
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    
    /* Inputs mejorados - PROFESIONAL Y COMPACTO */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea {
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        border-radius: 8px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 0.625rem 0.875rem !important;
        transition: all 0.3s ease !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Labels más compactos */
    .stTextInput label,
    .stTextArea label {
        font-size: 14px !important;
        margin-bottom: 0.375rem !important;
    }
    
    /* Tarjetas con sombra */
    .css-1r6slb0 {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    
    /* Sidebar premium mejorado - PROFESIONAL Y COMPACTO */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
        color: white !important;
        padding: 1.5rem 1rem !important;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        font-family: 'Poppins', sans-serif !important;
        color: white !important;
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Optimizar espaciado en sidebar */
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.75rem !important;
    }
    
    [data-testid="stSidebar"] hr {
        margin: 1rem 0 !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        margin-bottom: 0.5rem !important;
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
    /* Ocultar keyboard_double_arrow_right */
    .keyboard_double_arrow_right,
    [data-testid*="arrow"],
    svg[data-testid*="arrow"] {
        display: none !important;
    }
    /* Ocultar controles de expansión del sidebar */
    section[data-testid="stSidebar"] > div:first-child button {
        display: none !important;
    }
    
    /* Botones del sidebar mejorados - PROFESIONAL Y COMPACTO */
    [data-testid="stSidebar"] .stButton>button:not([key="btn_clear_cache"]):not([key="btn_logout_sidebar"]) {
        background: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
        padding: 0.625rem 1rem !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
        width: 100% !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
        margin: 0.375rem 0 !important;
        min-height: 40px !important;
    }
    
    [data-testid="stSidebar"] .stButton>button:not([key="btn_clear_cache"]):not([key="btn_logout_sidebar"]):hover {
        background: rgba(255, 255, 255, 0.25) !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3) !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* Botones secundarios del sidebar - Cerrar sesión, limpiar caché */
    [data-testid="stSidebar"] .stButton>button[kind="secondary"] {
        background: rgba(231, 76, 60, 0.25) !important;
        color: #ffffff !important;
        border: 2px solid rgba(231, 76, 60, 0.5) !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
    }
    [data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover {
        background: rgba(231, 76, 60, 0.4) !important;
        border-color: rgba(231, 76, 60, 0.7) !important;
        color: #ffffff !important;
        text-shadow: 0 2px 5px rgba(0, 0, 0, 0.5) !important;
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
    
    /* Tabs mejorados - PROFESIONAL Y COMPACTO */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: white;
        border-radius: 10px;
        padding: 0.375rem;
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.625rem 1.25rem;
        font-weight: 500;
        font-size: 14px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Alerts personalizadas - PROFESIONAL Y COMPACTO */
    .alert-critical {
        background-color: #fee;
        border-left: 4px solid #e74c3c;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.75rem 0;
    }
    
    .alert-high {
        background-color: #fff3cd;
        border-left: 4px solid #f39c12;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.75rem 0;
    }
    
    .alert-medium {
        background-color: #e7f3ff;
        border-left: 4px solid #3498db;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.75rem 0;
    }
    
    /* Streamlit alerts mejorados */
    .stAlert,
    .stSuccess,
    .stInfo,
    .stWarning,
    .stError {
        padding: 0.875rem 1rem !important;
        margin: 0.75rem 0 !important;
        border-radius: 8px !important;
    }
    
    /* Chat messages - MEJORADO: Sin solapamiento */
    .chat-message {
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
        animation: fadeIn 0.3s;
        clear: both !important;
        display: block !important;
        width: 100% !important;
        box-sizing: border-box !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        line-height: 1.7 !important;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 15%;
        margin-right: 0;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .user-message p,
    .user-message div,
    .user-message span {
        margin-bottom: 8px !important;
        line-height: 1.7 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    .bot-message {
        background: white;
        border: 1px solid #e0e0e0;
        margin-right: 15%;
        margin-left: 0;
        margin-top: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .bot-message p,
    .bot-message div,
    .bot-message span {
        margin-bottom: 8px !important;
        line-height: 1.7 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
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
        padding: 25px !important;
        margin-bottom: 20px !important;
        margin-top: 10px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08) !important;
        border-left: 5px solid !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        clear: both !important;
        display: block !important;
        overflow: visible !important;
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
    
    /* Badge de sentimiento - Mejorado para evitar solapamiento */
    .sentiment-badge {
        display: inline-block !important;
        padding: 8px 16px !important;
        border-radius: 20px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 15px !important;
        margin-right: 10px !important;
        white-space: nowrap !important;
        vertical-align: middle !important;
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
    
    /* Título de noticia - Mejorado para evitar solapamiento */
    .news-title {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: #1a1a2e !important;
        margin-bottom: 15px !important;
        margin-top: 5px !important;
        line-height: 1.5 !important;
        font-family: 'Poppins', sans-serif !important;
        clear: both !important;
        display: block !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Cuerpo de noticia - Mejorado */
    .news-body {
        font-size: 15px !important;
        color: #4a5568 !important;
        line-height: 1.8 !important;
        margin-bottom: 15px !important;
        margin-top: 10px !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        display: block !important;
        clear: both !important;
    }
    
    /* Explicación IA - Mejorado */
    .news-analysis {
        font-size: 14px !important;
        color: #2d3748 !important;
        font-style: normal !important;
        padding: 12px 15px !important;
        background: rgba(102, 126, 234, 0.08) !important;
        border-radius: 8px !important;
        border-left: 4px solid #667eea !important;
        margin-top: 12px !important;
        margin-bottom: 12px !important;
        display: block !important;
        clear: both !important;
        line-height: 1.6 !important;
        word-wrap: break-word !important;
    }
    
    /* Ocultar iconos de expander */
    .streamlit-expanderHeader {
        display: none !important;
    }
    
    /* Mejorar visualización de noticias - Ancho completo */
    .element-container {
        max-width: 100% !important;
    }
    
    /* Contenedor principal más ancho */
    .main .block-container {
        max-width: 1200px !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Tarjetas de noticias con mejor espaciado - Sin solapamiento */
    .news-card {
        margin-bottom: 25px !important;
        margin-top: 15px !important;
        clear: both !important;
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Evitar solapamiento en expanders */
    .streamlit-expander {
        margin-bottom: 20px !important;
        clear: both !important;
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Mejorar espaciado en tabs */
    .stTabs {
        margin-bottom: 25px !important;
        clear: both !important;
    }
    
    /* Mejorar espaciado en columnas para evitar solapamiento */
    [data-testid="column"] {
        padding: 0 10px !important;
        margin-bottom: 15px !important;
        clear: both !important;
        position: relative !important;
    }
    
    /* Evitar solapamiento de texto en métricas */
    [data-testid="stMetric"] {
        padding: 15px !important;
        margin: 10px 0 !important;
        min-height: 100px !important;
        clear: both !important;
        position: relative !important;
    }
    
    /* Mejorar espaciado en subheaders */
    h2, h3, h4 {
        margin-top: 30px !important;
        margin-bottom: 20px !important;
        clear: both !important;
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Evitar solapamiento en párrafos y divs */
    p, div {
        margin-bottom: 10px !important;
        clear: both !important;
    }
    
    /* Mejorar espaciado en secciones */
    section {
        margin-bottom: 25px !important;
        clear: both !important;
    }
    
    /* Evitar solapamiento de elementos inline */
    span, label, small {
        display: inline-block !important;
        white-space: normal !important;
        word-wrap: break-word !important;
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
    
    /* Ocultar todos los iconos de toggle del sidebar y flechas */
    button[data-baseweb="button"][aria-label*="Close"],
    button[data-baseweb="button"][aria-label*="close"],
    button[title*="Close"],
    button[title*="close"],
    button[aria-label*="Close sidebar"],
    button[title*="Close sidebar"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Ocultar icono keyboard_double_arrow_right específicamente */
    svg[data-testid*="keyboard"],
    svg[data-testid*="arrow"],
    svg[data-testid*="Keyboard"],
    [data-testid*="keyboard"],
    [data-testid*="Keyboard"],
    button[aria-label*="Close sidebar"],
    button[aria-label*="Close side panel"],
    button[kind="header"][aria-label*="Close"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        width: 0 !important;
        height: 0 !important;
        position: absolute !important;
        left: -9999px !important;
    }
    
    /* Evitar solapamiento de texto en todos los elementos */
    * {
        box-sizing: border-box !important;
    }
    
    /* Mejorar espaciado vertical para evitar montado de texto */
    .stMarkdown {
        margin-bottom: 15px !important;
        padding: 0 !important;
        clear: both !important;
        display: block !important;
        line-height: 1.7 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Asegurar que todos los elementos de texto tengan espaciado adecuado */
    .stMarkdown p,
    .stMarkdown div,
    .stMarkdown span {
        margin-bottom: 12px !important;
        line-height: 1.7 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        display: block !important;
        clear: both !important;
    }
    
    /* Evitar solapamiento en elementos inline */
    .stMarkdown strong,
    .stMarkdown b,
    .stMarkdown em,
    .stMarkdown i {
        display: inline !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Evitar solapamiento en captions y textos pequeños */
    .stCaption,
    caption,
    small {
        display: block !important;
        clear: both !important;
        margin-bottom: 8px !important;
        line-height: 1.6 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Evitar solapamiento en info/warning/success/error */
    .stAlert,
    .stSuccess,
    .stInfo,
    .stWarning,
    .stError {
        margin: 15px 0 !important;
        clear: both !important;
        display: block !important;
        position: relative !important;
        z-index: 10 !important;
        padding: 15px !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        line-height: 1.6 !important;
    }
    
    /* Mejorar espaciado en expanders */
    .streamlit-expander {
        margin: 20px 0 !important;
        clear: both !important;
    }
    
    .streamlit-expanderContent {
        padding: 15px !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Mejorar espaciado en inputs y textareas */
    .stTextInput,
    .stTextArea {
        margin-bottom: 15px !important;
        clear: both !important;
    }
    
    /* Mejorar espaciado en botones */
    .stButton {
        margin: 10px 0 !important;
        clear: both !important;
    }
    
    /* Mejorar expanders - PROFESIONAL Y COMPACTO */
    .streamlit-expanderHeader {
        padding: 0.75rem 1rem !important;
        margin-bottom: 0.25rem !important;
        font-weight: 600 !important;
        line-height: 1.5 !important;
        border-radius: 8px !important;
    }
    
    .streamlit-expanderContent {
        padding: 1rem !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.75rem !important;
        clear: both !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        line-height: 1.7 !important;
    }
    
    /* Asegurar que los elementos dentro de expanders no se solapen */
    .streamlit-expanderContent > * {
        margin-bottom: 0.75rem !important;
        clear: both !important;
    }
    
    .streamlit-expanderContent > *:last-child {
        margin-bottom: 0 !important;
    }
    
    /* Mejorar espaciado en contenedores de alertas */
    [data-testid="stExpander"] {
        margin-bottom: 1rem !important;
        clear: both !important;
    }
    
    /* Asegurar que las columnas dentro de expanders no se solapen */
    .streamlit-expanderContent [data-testid="column"] {
        padding: 0 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem !important;
        }
        
        [data-testid="stSidebar"] {
            padding: 1rem 0.75rem !important;
        }
        
        [data-testid="column"] {
            padding: 0 0.25rem !important;
        }
    }
    
    /* Mejorar espaciado en listas */
    ul, ol, li {
        margin-bottom: 8px !important;
        clear: both !important;
        line-height: 1.6 !important;
    }
    
    /* Asegurar que las tarjetas de noticias no se solapen */
    .news-card-positive,
    .news-card-negative,
    .news-card-neutral {
        display: block !important;
        width: 100% !important;
        margin: 0 auto 30px auto !important;
        padding: 30px !important;
        clear: both !important;
        position: relative !important;
        overflow: visible !important;
        min-height: 200px !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        z-index: 1 !important;
    }
    
    /* Espaciado adicional entre elementos para evitar solapamiento */
    .news-card-positive + .news-card-positive,
    .news-card-negative + .news-card-negative,
    .news-card-neutral + .news-card-neutral,
    .news-card-positive + .news-card-negative,
    .news-card-positive + .news-card-neutral,
    .news-card-negative + .news-card-positive,
    .news-card-negative + .news-card-neutral,
    .news-card-neutral + .news-card-positive,
    .news-card-neutral + .news-card-negative {
        margin-top: 30px !important;
    }
    
    /* Asegurar que los elementos dentro de las tarjetas no se solapen */
    .news-card-positive > *,
    .news-card-negative > *,
    .news-card-neutral > * {
        margin-bottom: 15px !important;
        margin-top: 0 !important;
        clear: both !important;
        display: block !important;
        position: relative !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Espaciado específico para elementos dentro de tarjetas */
    .news-card-positive h3,
    .news-card-negative h3,
    .news-card-neutral h3 {
        margin-top: 0 !important;
        margin-bottom: 18px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    .news-card-positive p,
    .news-card-negative p,
    .news-card-neutral p {
        margin-top: 0 !important;
        margin-bottom: 15px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Mejorar el badge para que no se solape con el título */
    .sentiment-badge {
        display: inline-block !important;
        margin-bottom: 12px !important;
        margin-right: 10px !important;
        vertical-align: top !important;
        clear: both !important;
    }
    
    /* Mejorar título de noticia para que no se solape */
    .news-title {
        clear: both !important;
        display: block !important;
        margin-top: 12px !important;
        margin-bottom: 12px !important;
        padding: 0 !important;
        line-height: 1.5 !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        hyphens: auto !important;
    }
    
    /* Mejorar cuerpo de noticia */
    .news-body {
        clear: both !important;
        display: block !important;
        margin-top: 8px !important;
        margin-bottom: 12px !important;
        padding: 0 !important;
        line-height: 1.7 !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }
    
    /* Mejorar análisis IA */
    .news-analysis {
        clear: both !important;
        display: block !important;
        margin-top: 12px !important;
        margin-bottom: 12px !important;
        padding: 12px 15px !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }
    
    /* Ocultar controles de sidebar */
    [data-testid="stSidebar"][data-testid*="Collapse"],
    [data-testid="stSidebar"] button[aria-label*="close" i],
    [data-testid="stSidebar"] button[title*="close" i] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }
    
    /* Mejorar botón de limpiar caché y cerrar sesión en sidebar - PROFESIONAL */
    [data-testid="stSidebar"] button[key="btn_clear_cache"],
    [data-testid="stSidebar"] button[key="btn_logout_sidebar"] {
        background: rgba(231, 76, 60, 0.4) !important;
        color: #ffffff !important;
        border: 2px solid rgba(231, 76, 60, 0.8) !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5) !important;
        padding: 0.75rem 1.25rem !important;
        margin: 0.5rem 0 !important;
        width: 100% !important;
        display: block !important;
        clear: both !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 2px 8px rgba(231, 76, 60, 0.35) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    
    [data-testid="stSidebar"] button[key="btn_clear_cache"]:hover,
    [data-testid="stSidebar"] button[key="btn_logout_sidebar"]:hover {
        background: rgba(231, 76, 60, 0.6) !important;
        border-color: rgba(231, 76, 60, 1) !important;
        color: #ffffff !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.6) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(231, 76, 60, 0.5) !important;
    }
    
    /* Asegurar que los botones sean siempre visibles y funcionales */
    [data-testid="stSidebar"] button[key="btn_logout_sidebar"],
    [data-testid="stSidebar"] button[key="btn_clear_cache"] {
        position: relative !important;
        z-index: 100 !important;
        visibility: visible !important;
        opacity: 1 !important;
        min-height: 44px !important;
    }
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
            
            # MEJORADO: Usar expanders para noticias web - Sin solapamiento
            for index, row in df_web.iterrows():
                color_map = {"Positivo": "green", "Negativo": "red", "Neutro": "gray"}
                emoji_map = {"Positivo": "🟢", "Negativo": "🔴", "Neutro": "⚪"}
                color = color_map.get(row['sentimiento_ia'], "gray")
                emoji = emoji_map.get(row['sentimiento_ia'], "⚪")
                titular_web = str(row.get('titular', 'Sin título'))
                titular_short = titular_web[:80] + ('...' if len(titular_web) > 80 else '')
                
                with st.expander(f":{color}[{row['sentimiento_ia']}] {emoji} {titular_short}", expanded=False):
                    col_web1, col_web2 = st.columns([3, 1])
                    
                    with col_web1:
                        st.markdown(f"**📰 Contenido:**")
                        cuerpo_web = str(row.get('cuerpo', ''))
                        st.write(cuerpo_web[:500] + ('...' if len(cuerpo_web) > 500 else ''))
                        st.markdown("---")
                        st.markdown(f"**🤖 Análisis IA:**")
                        st.write(str(row.get('explicacion_ia', 'Sin análisis')))
                    
                    with col_web2:
                        st.caption(f"📰 **Fuente:**\n{row.get('fuente', 'N/A')}")
                        st.caption(f"📅 **Fecha:**\n{row.get('fecha', 'N/A')}")
                        url_web = row.get('url', '#')
                        if url_web and url_web != '#':
                            st.markdown(f"[🔗 Leer original]({url_web})")
            
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
                        
                        # Mensaje del usuario - MEJORADO: Sin solapamiento
                        user_input_escaped = html_escape(str(user_input))
                        st.markdown(f"""
                        <div class="chat-message user-message" style="clear: both; display: block; margin: 20px 0; padding: 20px; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.7;">
                            <strong style="display: block; margin-bottom: 10px;">👤 Tú:</strong>
                            <div style="display: block; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.7;">{user_input_escaped}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Respuesta del bot - MEJORADO: Sin solapamiento
                        response_text = html_escape(str(response.get('response', 'Sin respuesta')))
                        st.markdown(f"""
                        <div class="chat-message bot-message" style="clear: both; display: block; margin: 20px 0; padding: 20px; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.7;">
                            <strong style="display: block; margin-bottom: 10px;">🤖 Asistente:</strong>
                            <div style="display: block; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.7; margin-top: 10px;">{response_text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Noticias relevantes - MEJORADO: Sin solapamiento, más limpio
                        if response.get('relevant_news'):
                            with st.expander(f"📰 {len(response['relevant_news'])} Noticias Relevantes"):
                                for idx, news in enumerate(response['relevant_news']):
                                    titular_news = str(news.get('titular', 'Sin título'))
                                    sentimiento_news = str(news.get('sentimiento', 'N/A'))
                                    similarity = news.get('similarity', 0)
                                    
                                    st.markdown(f"**{titular_news}**")
                                    st.caption(f"Sentimiento: {sentimiento_news} | Similitud: {similarity:.2%}")
                                    if idx < len(response['relevant_news']) - 1:
                                        st.markdown("---")
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
                                # Limpiar el tema
                                theme_clean = str(theme).strip()
                                theme_display = theme_clean[:60] + ('...' if len(theme_clean) > 60 else '')
                                
                                # MEJORADO: Usar expander para clusters - Sin solapamiento
                                with st.expander(f"📁 **Cluster {i+1}**: {theme_display} ({len(cluster_data)} noticias)", expanded=(i==0)):
                                    st.caption(f"**Tema principal:** {theme_clean}")
                                    st.caption(f"**Noticias en este cluster:** {len(cluster_data)}")
                                    
                                    # Mostrar distribución de sentimientos
                                    sent_dist = cluster_data['sentimiento_ia'].value_counts()
                                    st.markdown("**📊 Distribución de Sentimientos:**")
                                    for sent, count in sent_dist.items():
                                        percentage = (count/len(cluster_data)*100) if len(cluster_data) > 0 else 0
                                        st.write(f"- **{sent}:** {count} ({percentage:.1f}%)")
                                    
                                    st.markdown("---")
                                    
                                    # Mostrar algunas noticias del cluster
                                    st.markdown("**📰 Muestra de Noticias:**")
                                    sample_news = cluster_data.head(5)
                                    for idx, news_row in sample_news.iterrows():
                                        sent = news_row.get('sentimiento_ia', 'Neutro')
                                        emoji = "🟢" if sent == "Positivo" else "🔴" if sent == "Negativo" else "⚪"
                                        titular_full = str(news_row.get('titular', ''))
                                        titular_short = titular_full[:80] + ('...' if len(titular_full) > 80 else '')
                                        st.caption(f"{emoji} {titular_short}")
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
                        
                        # MEJORADO: Usar expander para evitar solapamiento y mejorar legibilidad
                        alert_title_escaped = html_escape(str(alert.get('title', 'Alerta')))
                        alert_message_escaped = html_escape(str(alert.get('message', '')))
                        alert_recommendation_escaped = html_escape(str(alert.get('recommendation', '')))
                        
                        with st.expander(f"{icon} **{alert_title_escaped}**", expanded=(i == 1 and alert['severity'] == 'critical')):
                            st.markdown(f"""
                            <div style="background-color: white; padding: 15px; border-radius: 8px; 
                                        border-left: {border}; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
                                <p style="font-size: 1.05em; margin-bottom: 12px; line-height: 1.6; word-wrap: break-word;">
                                    <b>Descripción:</b> {alert_message_escaped}
                                </p>
                                <div style="background-color: #f8f9fa; padding: 12px; border-radius: 5px; margin: 10px 0; line-height: 1.6;">
                                    <p style="margin: 0; word-wrap: break-word;"><b>💡 Recomendación:</b> {alert_recommendation_escaped}</p>
                                </div>
                                <small style="color: #6c757d; display: block; margin-top: 10px;">🕒 Generada: {alert.get('timestamp', 'N/A')}</small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Mostrar detalles adicionales si existen
                            if 'details' in alert and alert['details']:
                                st.markdown("---")
                                st.markdown("**📋 Detalles Adicionales:**")
                                if isinstance(alert['details'], dict):
                                    for key, value in alert['details'].items():
                                        if isinstance(value, list):
                                            st.write(f"**{key}:**")
                                            for item in value[:5]:  # Mostrar máximo 5
                                                st.caption(f"  • {str(item)}")
                                        else:
                                            st.write(f"**{key}:** {str(value)}")
                                else:
                                    st.write(str(alert['details']))
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

