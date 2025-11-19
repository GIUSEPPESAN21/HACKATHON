import streamlit as st
import subprocess
import sys

# --- BLOQUE DE AUTO-INSTALACIÓN ---
# Esto soluciona el error "ModuleNotFoundError" desde Python
def instalar_librerias():
    with st.spinner('Instalando librerías de IA en el servidor... (esto tarda 1 min)'):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pysentimiento", "torch", "transformers"])
        except Exception as e:
            st.error(f"Error al instalar: {e}")

try:
    # Intentamos importar
    from pysentimiento import create_analyzer
except ImportError:
    # Si falla, instalamos y luego importamos
    instalar_librerias()
    from pysentimiento import create_analyzer
# ----------------------------------

import pandas as pd

# ... AQUÍ SIGUE EL RESTO DE TU CÓDIGO (st.set_page_config, etc) ...
# Asegúrate de NO volver a importar pysentimiento abajo.

# 1. Configuración de la página
st.set_page_config(page_title="Agro-Sentimiento", layout="wide")
st.title("🌾 Clasificador de Noticias Agroindustriales")
st.markdown("Sube tu base de datos de noticias para detectar sentimientos (Positivo, Negativo, Neutro).")

# 2. Carga del Modelo (Se carga una vez y se queda en caché para rapidez)
@st.cache_resource
def cargar_modelo():
    # Usamos un modelo específico para español
    analyzer = create_analyzer(task="sentiment", lang="es")
    return analyzer

analyzer = cargar_modelo()

# 3. Módulo de carga de archivos
archivo_subido = st.file_uploader("Carga tu archivo Excel o CSV", type=["xlsx", "csv"])

if archivo_subido is not None:
    # Leer el archivo dependiendo de la extensión
    try:
        if archivo_subido.name.endswith('.csv'):
            df = pd.read_csv(archivo_subido)
        else:
            df = pd.read_excel(archivo_subido)
        
        st.write("Vista previa de tus datos:", df.head())

        # 4. Selección de la columna a analizar
        columna_texto = st.selectbox("¿Cuál columna contiene la noticia?", df.columns)

        if st.button("Analizar Sentimientos"):
            with st.spinner('Analizando noticias... esto puede tomar unos momentos'):
                
                # Función interna para aplicar el modelo
                def predecir_sentimiento(texto):
                    if pd.isna(texto): return "Neutro"
                    resultado = analyzer.predict(str(texto))
                    return resultado.output # Retorna POS, NEG o NEU

                # Aplicar a toda la columna
                df['Sentimiento_Predicho'] = df[columna_texto].apply(predecir_sentimiento)
                
                # 5. Mostrar Resultados
                st.success("¡Análisis completado!")
                
                # Métricas rápidas
                conteo = df['Sentimiento_Predicho'].value_counts()
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.dataframe(conteo)
                with col2:
                    st.bar_chart(conteo)

                # Mostrar tabla final
                st.dataframe(df)

                # 6. Botón de descarga
                csv_final = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Descargar Resultados",
                    csv_final,
                    "noticias_clasificadas.csv",
                    "text/csv"
                )

    except Exception as e:
        st.error(f"Hubo un error al leer el archivo: {e}")
