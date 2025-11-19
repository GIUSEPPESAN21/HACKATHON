import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
import time
import re
import logging
from duckduckgo_search import DDGS

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgroSentimentAnalyzer:
    def __init__(self):
        try:
            self.api_key = st.secrets.get("GEMINI_API_KEY")
            if not self.api_key:
                self.api_key = st.secrets.get("gemini", {}).get("api_key")
            
            if not self.api_key:
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.toml")
                return

            genai.configure(api_key=self.api_key)
            
        except Exception as e:
            st.error(f"🤖 Error Crítico Configuración Gemini: {e}")

    def _parse_text_response(self, text_response):
        """Analiza la respuesta de texto plano para extraer clasificación y argumento."""
        sentimiento = "Neutro"
        explicacion = "Análisis automático."

        try:
            # Regex mejorado para capturar contenido multilínea
            clasif_match = re.search(r"CLASIFICACIÓN:\s*([^\n]*)", text_response, re.IGNORECASE)
            arg_match = re.search(r"ARGUMENTO:\s*(.*)", text_response, re.IGNORECASE | re.DOTALL)

            if clasif_match:
                raw_sent = clasif_match.group(1).strip().capitalize()
                # Limpieza de caracteres extra y normalización
                raw_sent = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ]", "", raw_sent)
                
                if "Positivo" in raw_sent: sentimiento = "Positivo"
                elif "Negativo" in raw_sent: sentimiento = "Negativo"
                elif "Neutro" in raw_sent: sentimiento = "Neutro"

            if arg_match:
                explicacion = arg_match.group(1).strip()

        except Exception as e:
            logger.error(f"Error parseando respuesta: {e}")

        return {"sentimiento": sentimiento, "explicacion": explicacion}

    def analyze_news(self, text):
        """
        Analiza una noticia con estrategia de espera agresiva si se agota la cuota.
        """
        if not self.api_key:
            return {"sentimiento": "Neutro", "explicacion": "Error: Sin API Key"}

        # Prompt optimizado
        prompt = f"""
        Actúa como un analista de riesgos agroindustriales para el Valle del Cauca.
        
        CRITERIOS:
        🔴 NEGATIVO: Paro, bloqueo, sequía, plaga, pérdidas, inseguridad, extorsión, crisis, caída de precios.
        🟢 POSITIVO: Inversión, exportación, subsidio, tecnología, alianza, superávit, cosecha récord.
        ⚪ NEUTRO: Boletines informativos sin impacto directo.

        NOTICIA: "{text}"

        RESPONDE EXACTAMENTE ASÍ:
        CLASIFICACIÓN: [Positivo/Negativo/Neutro]
        ARGUMENTO: [Explicación de 1 frase]
        """

        # Lista de modelos ordenada por EFICIENCIA DE CUOTA
        candidates = [
            "gemini-1.5-flash",       # El más rápido y con mejor cuota
            "gemini-1.5-flash-8b",    # Versión ultra ligera de respaldo
            "gemini-1.5-pro",         # Potente, pero más lento
            "gemini-2.0-flash-exp"    # Experimental (Cuota muy baja, última opción)
        ]

        for model_name in candidates:
            try:
                model = genai.GenerativeModel(
                    model_name,
                    generation_config={"temperature": 0.1, "max_output_tokens": 300},
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                
                response = model.generate_content(prompt)
                
                if response.parts:
                    return self._parse_text_response(response.text)
                
            except Exception as e:
                error_msg = str(e)
                # MANEJO CRÍTICO DE ERROR 429
                if "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning(f"⚠️ Cuota agotada en {model_name}. Esperando 20s para recuperar...")
                    # CAMBIO CLAVE: Esperar 20 segundos antes de intentar otro modelo
                    # Esto previene que saturemos todos los modelos en 1 segundo.
                    time.sleep(20) 
                    continue
                else:
                    logger.error(f"Error en {model_name}: {e}")
                    continue

        return {"sentimiento": "Neutro", "explicacion": "Sistema saturado por alta demanda."}

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
            
            # CAMBIO CLAVE: Aumentado a 5 segundos.
            # La capa gratuita permite ~15 RPM. 60/5 = 12 RPM (Seguro).
            time.sleep(5) 
            
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
                # Pausa de seguridad aumentada
                time.sleep(5)
            return analyzed_data
        except Exception as e:
            st.error(f"Error Web: {e}")
            return []
