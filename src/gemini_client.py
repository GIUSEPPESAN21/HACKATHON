import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
import time

class AgroSentimentAnalyzer:
    def __init__(self):
        try:
            # Soporte flexible para la API Key
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            elif "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
                api_key = st.secrets["gemini"]["api_key"]
            else:
                # Fallback temporal para evitar crash inmediato si no hay secrets
                api_key = "" 
                
            if not api_key:
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.")
                self.model = None
                return

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            
        except Exception as e:
            st.error(f"🤖 Error Configuración Gemini: {e}")
            self.model = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def analyze_news(self, text):
        if not self.model:
            return "Error Config"

        prompt = f"""
        Analista experto en agroindustria del Valle del Cauca.
        Clasifica el sentimiento de esta noticia: "{text}"
        
        Opciones: 'Positivo', 'Negativo', 'Neutro'.
        Responde SOLO la palabra.
        """

        # CONFIGURACIÓN CRÍTICA: Desactivar filtros de seguridad excesivos
        # Esto evita errores cuando las noticias hablan de "protestas" o "muertes" (común en noticias).
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        try:
            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            # Verificar si la respuesta fue bloqueada
            if not response.parts:
                return "Neutro" # Fallback seguro si Google bloquea el contenido
                
            sentiment = response.text.strip().replace('.', '').capitalize()
            
            if sentiment not in ['Positivo', 'Negativo', 'Neutro']:
                return "Neutro"
                
            return sentiment
        except Exception as e:
            # Si es un error de cuota (429), reintentar. Si es otro, devolver error.
            if "429" in str(e):
                raise e 
            return "Error"

    def analyze_batch(self, df, progress_bar=None):
        results = []
        total = len(df)
        
        if total == 0:
            return []

        for index, row in df.iterrows():
            # Usar texto_completo si existe, sino armarlo
            text_to_analyze = row.get('texto_completo', str(row.get('titular', '')) + " " + str(row.get('cuerpo', '')))
            
            sentiment = self.analyze_news(text_to_analyze)
            results.append(sentiment)
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            # Pausa vital para evitar error 429 (Too Many Requests)
            time.sleep(1.5)
            
        return results
