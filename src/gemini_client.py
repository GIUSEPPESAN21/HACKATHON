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
                genai.configure(api_key=self.api_key)
                self.model = True 
            
        except Exception as e:
            st.error(f"🤖 Error Configuración Gemini: {e}")
            self.model = None

    def _clean_json_string(self, json_string):
        """
        LIMPIEZA QUIRÚRGICA:
        Extrae exclusivamente el objeto JSON usando índices, ignorando cualquier texto
        introductorio o final que la IA pueda agregar.
        """
        try:
            # 1. Eliminar bloques de código Markdown si existen
            if "```" in json_string:
                json_string = re.sub(r"```json\n?|```", "", json_string)
            
            # 2. Buscar matemáticamente donde empieza '{' y termina '}'
            start = json_string.find('{')
            end = json_string.rfind('}')
            
            if start != -1 and end != -1:
                # Extraer solo el contenido JSON válido
                return json_string[start:end+1]
            
            return json_string.strip()
        except Exception as e:
            logger.error(f"Error limpiando JSON: {e}")
            return json_string

    def _get_robust_prompt(self, text):
        return f"""
        Eres un analista experto en riesgos agrícolas del Valle del Cauca.
        
        BASE DE CONOCIMIENTO (CRITERIOS ESTRICTOS):
        [NEGATIVO]: Paro, bloqueo, minga, sequía, plaga, pérdidas, inseguridad, extorsión, caída precios, costos altos, crisis.
        [POSITIVO]: Inversión, exportación, subsidio, tecnología, inauguración, alianza, superávit, cosecha récord.
        [NEUTRO]: Informativo, boletín, reunión sin resultados, censo.

        TAREA:
        Clasifica la siguiente noticia. Si detectas CUALQUIER riesgo (paro, clima, plaga), debe ser NEGATIVO. No seas neutral si hay riesgo.

        Noticia: "{text}"

        FORMATO JSON OBLIGATORIO:
        {{
            "sentimiento": "Positivo" | "Negativo" | "Neutro",
            "explicacion": "Argumento de 5 a 10 palabras máximo."
        }}
        """

    def analyze_news(self, text):
        if not self.api_key:
            return {"sentimiento": "Neutro", "explicacion": "Falta API Key"}

        # Configuración optimizada para forzar estructura
        generation_config = {
            "temperature": 0.1, # Temperatura casi cero para máxima obediencia
            "top_p": 0.95,
            "max_output_tokens": 500,
            "response_mime_type": "application/json" # Forzado nativo de JSON
        }

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Lista de modelos priorizada
        # Usamos 1.5 Flash primero porque es el más estable con JSON Mode
        model_candidates = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp"
        ]

        for modelo_nombre in model_candidates:
            try:
                model = genai.GenerativeModel(
                    model_name=modelo_nombre,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )

                response = model.generate_content(self._get_robust_prompt(text))
                
                # Verificación de bloqueo de seguridad
                if not response.parts:
                    logger.warning(f"Bloqueo de seguridad en {modelo_nombre}")
                    continue

                cleaned_text = self._clean_json_string(response.text)
                
                try:
                    result = json.loads(cleaned_text)
                    sent = result.get("sentimiento", "Neutro").capitalize()
                    expl = result.get("explicacion", "Análisis IA")
                    
                    # Normalización
                    if sent not in ["Positivo", "Negativo", "Neutro"]:
                        sent = "Neutro"
                        
                    return {"sentimiento": sent, "explicacion": expl}
                    
                except json.JSONDecodeError:
                    logger.warning(f"JSON inválido en {modelo_nombre}: {cleaned_text}")
                    continue 

            except Exception as e:
                logger.error(f"Error en modelo {modelo_nombre}: {e}")
                continue
        
        return {"sentimiento": "Neutro", "explicacion": "Error de Procesamiento (Reintentar)"}

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
            
            time.sleep(0.5) # Pausa para estabilidad
            
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
