import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
import time

class AgroSentimentAnalyzer:
    def __init__(self):
        try:
            # Búsqueda de API Key en los secrets
            api_key = st.secrets.get("GEMINI_API_KEY")
            
            if not api_key:
                # Fallback para evitar errores si no está configurado aún
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.toml")
                self.model = None
                return

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            
        except Exception as e:
            st.error(f"🤖 Error Configuración Gemini: {e}")
            self.model = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def analyze_news(self, text):
        """
        Analiza una noticia individual con contexto específico del Valle del Cauca.
        """
        if not self.model:
            return "Error Config"

        # PROMPT DE INGENIERÍA ROBUSTO
        prompt = f"""
        Actúa como un analista senior de riesgos agroindustriales para la región del Valle del Cauca, Colombia.
        Tu tarea es clasificar el sentimiento de la siguiente noticia para un sistema de alertas tempranas.

        Reglas estrictas de clasificación:
        1. NEGATIVO: Noticias sobre plagas, sequías, fenómeno del niño, paros armados, bloqueos de vías, caída de precios, pérdidas económicas, inseguridad rural, uso excesivo de químicos.
        2. POSITIVO: Noticias sobre nuevas inversiones, subsidios del gobierno, tecnología agrícola, aumento de exportaciones, clima favorable, alianzas productivas, apertura de mercados.
        3. NEUTRO: Noticias meramente informativas, nombramientos administrativos, boletines técnicos sin impacto económico directo inmediato.

        Noticia: "{text}"

        Instrucción de Salida: Responde ÚNICAMENTE con una de estas tres palabras exactas: "Positivo", "Negativo" o "Neutro". No expliques nada más.
        """

        # DESACTIVAR FILTROS DE SEGURIDAD (Crucial para noticias de protestas/violencia/plagas)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        try:
            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            if not response.parts:
                return "Neutro" # Si Google bloquea, asumimos neutro para no romper el flujo
                
            # Limpieza agresiva de la respuesta
            raw_sentiment = response.text.strip().lower()
            
            if "positivo" in raw_sentiment:
                return "Positivo"
            elif "negativo" in raw_sentiment:
                return "Negativo"
            elif "neutro" in raw_sentiment:
                return "Neutro"
            else:
                return "Neutro" # Default seguro
                
        except Exception as e:
            if "429" in str(e):
                raise e # Permitir reintento si es error de cuota
            print(f"Error analizando noticia: {e}")
            return "Neutro"

    def analyze_batch(self, df, progress_bar=None):
        results = []
        total = len(df)
        
        if total == 0:
            return []

        for index, row in df.iterrows():
            text_to_analyze = str(row.get('texto_completo', ''))
            
            # Llamada a la IA
            sentiment = self.analyze_news(text_to_analyze)
            results.append(sentiment)
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            # Pausa anti-bloqueo (Evita error 429 Resource Exhausted)
            time.sleep(1.2)
            
        return results
