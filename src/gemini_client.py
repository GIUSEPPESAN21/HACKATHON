import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import re
import logging
from duckduckgo_search import DDGS

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgroSentimentAnalyzer:
    def __init__(self):
        self.model = None
        try:
            # 1. Recuperación de API Key
            self.api_key = st.secrets.get("GEMINI_API_KEY")
            if not self.api_key:
                self.api_key = st.secrets.get("gemini", {}).get("api_key")
            
            if not self.api_key:
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.toml")
                return

            genai.configure(api_key=self.api_key)
            
            # 2. Selección Automática del Mejor Modelo Disponible (Tu lógica mejorada)
            self.model = self._get_available_model()
            
        except Exception as e:
            st.error(f"🤖 Error Crítico Configuración Gemini: {e}")

    def _get_available_model(self):
        """
        Itera sobre una lista de modelos priorizada para encontrar uno funcional.
        """
        model_candidates = [
            "gemini-2.0-flash-exp",       # El más rápido e inteligente (Experimental)
            "gemini-1.5-pro",             # El más robusto (Estable)
            "gemini-1.5-flash",           # El más rápido (Estable)
            "gemini-1.5-flash-8b"         # Versión ligera
        ]

        for model_name in model_candidates:
            try:
                # Intentamos instanciar y hacer una prueba mínima de conexión (opcional)
                model = genai.GenerativeModel(model_name)
                logger.info(f"✅ Modelo activo: {model_name}")
                return model
            except Exception as e:
                logger.warning(f"⚠️ Fallo modelo {model_name}: {e}")
                continue
        
        st.error("❌ No se pudo conectar con ningún modelo de Google Gemini.")
        return None

    def _parse_text_response(self, text_response):
        """
        Analiza la respuesta en texto plano y extrae la clasificación y el argumento.
        Formato esperado:
        CLASIFICACIÓN: Positivo
        ARGUMENTO: Bla bla bla
        """
        sentimiento = "Neutro" # Default seguro
        explicacion = "No se pudo extraer explicación."

        try:
            # Usamos Regex para buscar las etiquetas independientemente de espacios o mayúsculas
            clasif_match = re.search(r"CLASIFICACIÓN:\s*([^\n]*)", text_response, re.IGNORECASE)
            arg_match = re.search(r"ARGUMENTO:\s*(.*)", text_response, re.IGNORECASE | re.DOTALL)

            if clasif_match:
                raw_sent = clasif_match.group(1).strip().capitalize()
                # Limpieza extra por si el modelo pone "Positivo." o "**Positivo**"
                raw_sent = raw_sent.replace('.', '').replace('*', '')
                if raw_sent in ["Positivo", "Negativo", "Neutro"]:
                    sentimiento = raw_sent
                # Corrección de "sesgos" comunes del modelo
                elif "Riesgo" in raw_sent or "Alerta" in raw_sent: 
                    sentimiento = "Negativo"

            if arg_match:
                explicacion = arg_match.group(1).strip()

        except Exception as e:
            logger.error(f"Error parseando respuesta IA: {e}")

        return {"sentimiento": sentimiento, "explicacion": explicacion}

    def analyze_news(self, text):
        if not self.model:
            return {"sentimiento": "Neutro", "explicacion": "Error: Sin Modelo IA"}

        # Prompt enfocado en TEXTO, no JSON
        prompt = f"""
        Actúa como un analista senior de riesgos agroindustriales para el Valle del Cauca.
        Tu trabajo es clasificar noticias para un sistema de Alertas Tempranas.

        CRITERIOS ESTRICTOS DE CLASIFICACIÓN:
        🔴 NEGATIVO (Prioridad Alta):
           - Palabras clave: Paro, bloqueo, minga, invasión, sequía, fenómeno del niño, plagas, pérdidas, inseguridad, extorsión, caída de precios, crisis.
           - REGLA DE ORO: Si hay CUALQUIER mención de riesgo para la producción o transporte, ES NEGATIVO. No seas neutral ante el riesgo.

        🟢 POSITIVO:
           - Palabras clave: Inversión, exportación, subsidio, tecnología, alianza, superávit, cosecha récord.

        ⚪ NEUTRO:
           - Solo para boletines informativos, censos o reuniones sin resultados concretos.

        NOTICIA A ANALIZAR:
        "{text}"

        INSTRUCCIONES DE SALIDA:
        Responde estrictamente con este formato de texto (sin markdown, sin json):

        CLASIFICACIÓN: [Positivo, Negativo o Neutro]
        ARGUMENTO: [Tu explicación breve y directa de por qué]
        """

        generation_config = {
            "temperature": 0.3, # Baja creatividad para ser preciso
            "max_output_tokens": 500,
        }

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        try:
            # Llamada directa sin forzar JSON
            response = self.model.generate_content(
                prompt, 
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            if response.parts:
                # Procesamos el texto plano que devuelve el modelo
                return self._parse_text_response(response.text)
            else:
                return {"sentimiento": "Neutro", "explicacion": "Bloqueo de Seguridad (Google)"}

        except Exception as e:
            logger.error(f"Error en inferencia IA: {e}")
            # Fallback simple si falla la API
            return {"sentimiento": "Neutro", "explicacion": "Error de Conexión API"}

    def analyze_batch(self, df, progress_bar=None):
        results_sent = []
        results_expl = []
        total = len(df)
        
        if total == 0: return [], []

        for index, row in df.iterrows():
            titular = str(row.get('titular', ''))
            cuerpo = str(row.get('cuerpo', ''))
            text = f"{titular}. {cuerpo}"
            
            analysis = self.analyze_news(text)
            
            results_sent.append(analysis["sentimiento"])
            results_expl.append(analysis["explicacion"])
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            time.sleep(0.5) # Pausa de cortesía para no saturar
            
        return results_sent, results_expl

    def search_and_analyze_web(self, query="agroindustria Valle del Cauca", max_results=5):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(keywords=query, region="co-co", safesearch="off", max_results=max_results))
            
            analyzed_data = []
            if not results: return []

            for item in results:
                full_text = f"{item.get('title','')}. {item.get('body','')}"
                analysis = self.analyze_news(full_text)
                
                analyzed_data.append({
                    "titular": item.get('title',''),
                    "cuerpo": item.get('body',''),
                    "fecha": item.get('date',''),
                    "fuente": item.get('source',''),
                    "url": item.get('url',''),
                    "sentimiento_ia": analysis["sentimiento"],
                    "explicacion_ia": analysis["explicacion"],
                    "id_original": f"web_{int(time.time())}_{results.index(item)}"
                })
                time.sleep(0.5)
            return analyzed_data
        except Exception as e:
            st.error(f"Error Web: {e}")
            return []
