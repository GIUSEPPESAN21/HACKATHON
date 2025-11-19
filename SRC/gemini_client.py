import google.generativeai as genai
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
import time

class AgroSentimentAnalyzer:
    def __init__(self):
        # Inicialización segura de API Key
        try:
            api_key = st.secrets["gemini"]["api_key"]
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            st.error(f"Error configurando Gemini API: {e}. Verifique st.secrets.")
            self.model = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def analyze_news(self, text):
        """
        Clasifica el sentimiento de una noticia con contexto agroindustrial.
        Incluye lógica de reintentos (backoff) para manejar rate limits.
        """
        if not self.model:
            return "Error Config"

        prompt = f"""
        Actúa como un analista experto en agroindustria y economía rural para el Valle del Cauca, Colombia.
        Analiza la siguiente noticia y clasifica su sentimiento EXCLUSIVAMENTE como una de estas tres opciones: 
        'Positivo', 'Negativo' o 'Neutro'.

        Criterios de evaluación:
        - Positivo: Inversiones, buen clima, subsidios, tecnología, aumento de exportaciones.
        - Negativo: Plagas, sequías, protestas, caida de precios, inseguridad.
        - Neutro: Informes técnicos sin connotación emocional, anuncios administrativos rutinarios.

        Noticia: "{text}"

        Responde SOLO con la palabra de la clasificación.
        """

        try:
            response = self.model.generate_content(prompt)
            # Limpieza de la respuesta
            sentiment = response.text.strip().replace('.', '').capitalize()
            
            valid_responses = ['Positivo', 'Negativo', 'Neutro']
            if sentiment not in valid_responses:
                # Fallback básico si el modelo alucina
                return "Neutro"
                
            return sentiment
        except Exception as e:
            # Loggear error internamente si es necesario
            raise e # Lanzar para que @retry funcione

    def analyze_batch(self, df, progress_bar=None):
        """
        Procesa un DataFrame completo.
        """
        results = []
        total = len(df)
        
        for index, row in df.iterrows():
            sentiment = self.analyze_news(row['texto_completo'])
            results.append(sentiment)
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            # Pausa preventiva para respetar límites de la capa gratuita (aprox 60 req/min)
            time.sleep(1.5) 
            
        return results
