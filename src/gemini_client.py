import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import json
# Importamos la búsqueda web gratuita
from duckduckgo_search import DDGS

class AgroSentimentAnalyzer:
    def __init__(self):
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
            if not api_key:
                # Intentar buscar en la sección [gemini] por compatibilidad
                api_key = st.secrets.get("gemini", {}).get("api_key")
            
            if not api_key:
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.toml")
                self.model = None
                return

            genai.configure(api_key=api_key)
            # Usamos flash por ser más rápido y mejor siguiendo instrucciones JSON
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
        except Exception as e:
            st.error(f"🤖 Error Configuración Gemini: {e}")
            self.model = None

    def _get_keywords_prompt(self):
        """Base de conocimiento inyectada en el prompt"""
        return """
        BASE DE CONOCIMIENTO AGRO-VALLE DEL CAUCA:
        
        [SENTIMIENTO NEGATIVO 🔴]
        - Palabras clave: Paro, bloqueo, minga, invasión, sequía, fenómeno del niño, plaga, hongo, pérdidas, quiebra, inseguridad, extorsión, caída de precios, altos costos de insumos.
        - Contexto: Afectación a la cadena de suministro, reducción de hectáreas sembradas.

        [SENTIMIENTO POSITIVO 🟢]
        - Palabras clave: Inversión, exportación, subsidio, crédito, tecnología, inauguración, alianza, superávit, recuperación, cosecha récord, apertura de mercados, certificación.
        - Contexto: Crecimiento económico, apoyo gubernamental efectivo.

        [SENTIMIENTO NEUTRO ⚪]
        - Palabras clave: Informe, boletín, monitoreo, censo, reunión, mesa de diálogo (sin resultados aún), capacitación, anuncio administrativo.
        - Contexto: Hechos meramente informativos sin adjetivos de éxito o fracaso.
        """

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def analyze_news(self, text):
        """
        Analiza una noticia devolviendo Sentimiento y Explicación en JSON.
        """
        if not self.model:
            return {"sentimiento": "Neutro", "explicacion": "Error de configuración IA"}

        prompt = f"""
        Eres un analista experto en riesgos agrícolas del Valle del Cauca.
        
        {self._get_keywords_prompt()}

        TAREA:
        Analiza la siguiente noticia y clasifícala. Debes justificar tu respuesta basándote en las palabras clave identificadas.

        Noticia: "{text}"

        FORMATO DE RESPUESTA (JSON OBLIGATORIO):
        Responde SOLO con un objeto JSON válido con esta estructura:
        {{
            "sentimiento": "Positivo" | "Negativo" | "Neutro",
            "explicacion": "Breve justificación de máximo 15 palabras explicando qué palabra clave detonó la clasificación."
        }}
        """

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        try:
            response = self.model.generate_content(prompt, safety_settings=safety_settings, generation_config={"response_mime_type": "application/json"})
            
            if not response.parts:
                return {"sentimiento": "Neutro", "explicacion": "Bloqueo de seguridad Google"}
            
            # Parsear JSON
            result = json.loads(response.text)
            
            # Normalizar mayúsculas/minúsculas
            sent = result.get("sentimiento", "Neutro").capitalize()
            expl = result.get("explicacion", "Sin explicación")
            
            if sent not in ["Positivo", "Negativo", "Neutro"]:
                sent = "Neutro"
                
            return {"sentimiento": sent, "explicacion": expl}
                
        except Exception as e:
            print(f"Error analizando noticia: {e}")
            return {"sentimiento": "Neutro", "explicacion": "Error de procesamiento"}

    def analyze_batch(self, df, progress_bar=None):
        """Procesa batch del CSV"""
        results_sent = []
        results_expl = []
        total = len(df)
        
        if total == 0: return [], []

        for index, row in df.iterrows():
            text = str(row.get('texto_completo', ''))
            
            analysis = self.analyze_news(text)
            
            results_sent.append(analysis["sentimiento"])
            results_expl.append(analysis["explicacion"])
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            time.sleep(0.5) # Flash es más rápido, podemos reducir la espera
            
        return results_sent, results_expl

    def search_and_analyze_web(self, query="agroindustria Valle del Cauca", max_results=5):
        """
        Busca noticias en vivo y las analiza.
        """
        try:
            # Buscar en la web usando DuckDuckGo (gratis)
            with DDGS() as ddgs:
                # 'n' significa búsqueda de noticias
                results = list(ddgs.news(keywords=query, region="co-co", safesearch="off", max_results=max_results))
            
            analyzed_data = []
            
            if not results:
                return []

            for item in results:
                title = item.get('title', '')
                body = item.get('body', '')
                date = item.get('date', '')
                source = item.get('source', '')
                url = item.get('url', '')
                
                full_text = f"{title}. {body}"
                
                # Analizar con Gemini
                analysis = self.analyze_news(full_text)
                
                analyzed_data.append({
                    "titular": title,
                    "cuerpo": body,
                    "fecha": date,
                    "fuente": source,
                    "url": url,
                    "sentimiento_ia": analysis["sentimiento"],
                    "explicacion_ia": analysis["explicacion"],
                    "id_original": f"web_{int(time.time())}_{results.index(item)}"
                })
                time.sleep(0.5)
                
            return analyzed_data
            
        except Exception as e:
            st.error(f"Error en búsqueda web: {e}")
            return []
