import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import json
import re
from duckduckgo_search import DDGS

class AgroSentimentAnalyzer:
    def __init__(self):
        try:
            # Lógica de recuperación de API Key
            api_key = st.secrets.get("GEMINI_API_KEY")
            if not api_key:
                api_key = st.secrets.get("gemini", {}).get("api_key")
            
            if not api_key:
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.toml")
                self.model = None
                return

            genai.configure(api_key=api_key)
            # Usamos gemini-1.5-flash por velocidad, pero con config de JSON forzado
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
        except Exception as e:
            st.error(f"🤖 Error Configuración Gemini: {e}")
            self.model = None

    def _clean_json_string(self, json_string):
        """
        Limpia la respuesta de la IA para evitar errores de formato.
        Elimina bloques de código markdown ```json ... ```
        """
        try:
            # Eliminar bloques de código markdown
            if "```" in json_string:
                json_string = re.sub(r"```json\n?|```", "", json_string)
            return json_string.strip()
        except:
            return json_string

    def _get_keywords_prompt(self):
        return """
        BASE DE CONOCIMIENTO PRIORITARIA - VALLE DEL CAUCA:
        
        🚨 SENTIMIENTO NEGATIVO (Prioridad Alta):
        - Si menciona: Paro, bloqueo, minga, invasión de tierras, sequía, fenómeno del niño, plagas, pérdidas económicas, inseguridad, extorsión, caída de precios, altos costos, protesta, crisis.
        - Regla: Ante la duda, si hay riesgo de pérdida de dinero o producción, clasifica como NEGATIVO.

        ✅ SENTIMIENTO POSITIVO:
        - Si menciona: Nueva inversión, exportación exitosa, subsidios entregados, tecnología implementada, inauguración de obras, alianzas firmadas, superávit, cosecha récord, certificación de calidad.
        
        ⚪ SENTIMIENTO NEUTRO (Solo si no hay nada más):
        - Solo para: Anuncios de reuniones futuras (sin resultados), boletines informativos rutinarios, nombramientos de funcionarios, datos censales sin análisis de impacto.
        """

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def analyze_news(self, text):
        if not self.model:
            return {"sentimiento": "Neutro", "explicacion": "Error Configuración"}

        prompt = f"""
        Eres un analista de riesgos agroindustriales crítico y directo.
        
        {self._get_keywords_prompt()}

        TAREA:
        Analiza la siguiente noticia. NO seas neutral si detectas el más mínimo riesgo u oportunidad.
        
        Noticia: "{text}"

        SALIDA OBLIGATORIA (JSON):
        {{
            "sentimiento": "Positivo" | "Negativo" | "Neutro",
            "explicacion": "Frase corta (max 10 palabras) indicando la palabra clave detectada."
        }}
        """

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        try:
            # Forzamos MIME type JSON para que el modelo sea obediente
            response = self.model.generate_content(
                prompt, 
                safety_settings=safety_settings,
                generation_config={"response_mime_type": "application/json"}
            )
            
            if not response.parts:
                return {"sentimiento": "Neutro", "explicacion": "Google Security Block"}
            
            # Limpieza y Parseo Robusto
            cleaned_text = self._clean_json_string(response.text)
            result = json.loads(cleaned_text)
            
            sent = result.get("sentimiento", "Neutro").capitalize()
            expl = result.get("explicacion", "Sin detalle")
            
            # Normalización final
            if sent not in ["Positivo", "Negativo", "Neutro"]:
                sent = "Neutro"
                
            return {"sentimiento": sent, "explicacion": expl}
                
        except json.JSONDecodeError:
            # Si falla el JSON, intentamos rescatar algo manualmente o devolvemos error limpio
            print(f"Error JSON crudo: {response.text}") 
            return {"sentimiento": "Neutro", "explicacion": "Error formato IA"}
        except Exception as e:
            print(f"Error general: {e}")
            return {"sentimiento": "Neutro", "explicacion": "Error conexión"}

    def analyze_batch(self, df, progress_bar=None):
        results_sent = []
        results_expl = []
        total = len(df)
        
        if total == 0: return [], []

        for index, row in df.iterrows():
            # Construir texto robusto
            titular = str(row.get('titular', ''))
            cuerpo = str(row.get('cuerpo', ''))
            text = f"{titular}. {cuerpo}"
            
            analysis = self.analyze_news(text)
            
            results_sent.append(analysis["sentimiento"])
            results_expl.append(analysis["explicacion"])
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            # Pequeña pausa para estabilidad
            time.sleep(0.5)
            
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
        
