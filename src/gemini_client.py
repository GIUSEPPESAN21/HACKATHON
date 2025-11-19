import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import json
import re
import logging
from duckduckgo_search import DDGS

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgroSentimentAnalyzer:
    def __init__(self):
        try:
            # Recuperación robusta de la API Key
            self.api_key = st.secrets.get("GEMINI_API_KEY")
            if not self.api_key:
                self.api_key = st.secrets.get("gemini", {}).get("api_key")
            
            if not self.api_key:
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.toml")
                self.model = None
            else:
                # Configuración inicial (se re-configura en cada llamada para robustez)
                genai.configure(api_key=self.api_key)
                self.model = True # Flag simple para indicar que estamos listos
            
        except Exception as e:
            st.error(f"🤖 Error Configuración Gemini: {e}")
            self.model = None

    def _clean_json_string(self, json_string):
        """Limpia la respuesta de bloques markdown."""
        try:
            if "```" in json_string:
                json_string = re.sub(r"```json\n?|```", "", json_string)
            return json_string.strip()
        except:
            return json_string

    def _get_robust_prompt(self, text):
        """
        Prompt optimizado con tus criterios específicos para el Valle del Cauca.
        Adaptado para retornar JSON y mantener compatibilidad con el sistema.
        """
        return f"""
        Eres un analista senior de riesgos agroindustriales especializado en la región del Valle del Cauca, Colombia. 
        El sistema de alertas tempranas requiere clasificaciones precisas.

        Criterios de clasificación:
        NEGATIVO: Plagas, sequías, fenómeno del niño, paros armados, bloqueos de vías, caída de precios, pérdidas económicas, inseguridad rural, uso excesivo de químicos.
        POSITIVO: Nuevas inversiones, subsidios del gobierno, tecnología agrícola, aumento de exportaciones, clima favorable, alianzas productivas, apertura de mercados.
        NEUTRO: Noticias meramente informativas, nombramientos administrativos, boletines técnicos sin impacto económico directo inmediato.

        Instrucciones Críticas:
        1. Evita confundir medidas preventivas con crisis actuales.
        2. Distingue impacto económico directo vs potencial.
        3. Clasifica según el impacto predominante.
        4. Ignora el tono emocional, enfócate en el contenido factual.

        Noticia a analizar: "{text}"

        SALIDA OBLIGATORIA (FORMATO JSON):
        Para compatibilidad con el sistema, debes responder estrictamente con este JSON:
        {{
            "sentimiento": "Positivo" | "Negativo" | "Neutro",
            "explicacion": "Breve justificación (max 15 palabras) basada en tus criterios."
        }}
        """

    def analyze_news(self, text):
        """
        FUNCIÓN CORREGIDA Y OPTIMIZADA (Basada en tu solicitud v2.0)
        - Itera sobre múltiples modelos (2.0 experimental -> 1.5 stable).
        - Manejo de errores robusto.
        """
        if not self.api_key:
            return {"sentimiento": "Neutro", "explicacion": "Error Configuración"}

        # Configuración de generación optimizada para análisis
        generation_config = {
            "temperature": 0.3, # Baja temperatura para mayor precisión
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
            "response_mime_type": "application/json" # Forzamos JSON nativamente
        }

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        # Lista de modelos priorizada (Tu lista solicitada)
        model_candidates = [
            "gemini-2.0-flash-exp",       # Prioridad 1: Experimental rápido
            "gemini-1.5-flash",           # Prioridad 2: Estable rápido
            "gemini-1.5-pro",             # Prioridad 3: Estable potente
            "gemini-1.5-flash-8b"         # Prioridad 4: Ultraligero
        ]

        last_error = None

        for modelo_nombre in model_candidates:
            try:
                # Instanciar modelo específico
                model = genai.GenerativeModel(
                    model_name=modelo_nombre,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )

                # Intentar generar contenido
                response = model.generate_content(self._get_robust_prompt(text))
                
                if response.parts:
                    cleaned_text = self._clean_json_string(response.text)
                    
                    # Guardamos qué modelo se usó (útil para depuración)
                    if 'model_usage_stats' not in st.session_state:
                        st.session_state['model_usage_stats'] = {}
                    st.session_state['model_usage_stats'][modelo_nombre] = st.session_state['model_usage_stats'].get(modelo_nombre, 0) + 1
                    
                    try:
                        result = json.loads(cleaned_text)
                        sent = result.get("sentimiento", "Neutro").capitalize()
                        expl = result.get("explicacion", "Análisis automático")
                        
                        # Validación final
                        if sent not in ["Positivo", "Negativo", "Neutro"]:
                            sent = "Neutro"
                            
                        return {"sentimiento": sent, "explicacion": expl}
                        
                    except json.JSONDecodeError:
                        # Si falla el JSON, intentamos el siguiente modelo o retornamos error suave
                        logger.warning(f"Fallo JSON en {modelo_nombre}")
                        continue 

            except Exception as e:
                logger.warning(f"Modelo {modelo_nombre} falló: {str(e)}")
                last_error = e
                continue # Intentar siguiente modelo
        
        # Si llegamos aquí, todos los modelos fallaron
        st.error(f"Todos los modelos de IA fallaron. Último error: {last_error}")
        return {"sentimiento": "Neutro", "explicacion": "Fallo general IA"}

    def analyze_batch(self, df, progress_bar=None):
        """Procesa el lote de noticias con la lógica robusta."""
        results_sent = []
        results_expl = []
        total = len(df)
        
        if total == 0: return [], []

        # Inicializar estadísticas de uso si no existen
        if 'model_usage_stats' not in st.session_state:
            st.session_state['model_usage_stats'] = {}

        for index, row in df.iterrows():
            # Construir texto completo
            titular = str(row.get('titular', ''))
            cuerpo = str(row.get('cuerpo', ''))
            text = f"{titular}. {cuerpo}"
            
            # Llamada a la IA (que ahora itera modelos internamente)
            analysis = self.analyze_news(text)
            
            results_sent.append(analysis["sentimiento"])
            results_expl.append(analysis["explicacion"])
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            # Pausa reducida porque tenemos fallback de modelos
            time.sleep(0.3)
            
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
            st.error(f"Error Búsqueda Web: {e}")
            return []
