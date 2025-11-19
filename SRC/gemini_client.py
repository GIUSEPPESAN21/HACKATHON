import google.generativeai as genai
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
import time

class AgroSentimentAnalyzer:
    def __init__(self):
        # Inicialización adaptada a tu variable 'GEMINI_API_KEY'
        try:
            # Intenta buscar la llave en la raíz (tu formato)
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            # Fallback a la sección [gemini] por compatibilidad
            elif "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
                api_key = st.secrets["gemini"]["api_key"]
            else:
                raise ValueError("No se encontró la GEMINI_API_KEY en secrets.")

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            
        except Exception as e:
            st.error(f"🤖 Error Configuración Gemini: {e}")
            self.model = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def analyze_news(self, text):
        if not self.model:
            return "Error Config"

        # Prompt optimizado para el contexto Valle del Cauca
        prompt = f"""
        Analista experto en agroindustria del Valle del Cauca.
        Clasifica el sentimiento de esta noticia: "{text}"
        
        Opciones: 'Positivo' (Inversión, Tecnología, Crecimiento), 'Negativo' (Plagas, Paros, Pérdidas), 'Neutro' (Informativo).
        Responde SOLO la palabra.
        """

        try:
            response = self.model.generate_content(prompt)
            sentiment = response.text.strip().replace('.', '').capitalize()
            
            if sentiment not in ['Positivo', 'Negativo', 'Neutro']:
                return "Neutro" # Fail-safe
                
            return sentiment
        except Exception as e:
            raise e 

    def analyze_batch(self, df, progress_bar=None):
        results = []
        total = len(df)
        
        # Verificar si el dataframe está vacío
        if total == 0:
            return []

        for index, row in df.iterrows():
            sentiment = self.analyze_news(row['texto_completo'])
            results.append(sentiment)
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            time.sleep(1.2) # Rate limit preventivo
            
        return results
