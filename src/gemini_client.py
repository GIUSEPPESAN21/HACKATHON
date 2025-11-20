import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
import time
import re
import logging
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from src.cache_manager import CacheManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgroSentimentAnalyzer:
    def __init__(self):
        self.api_key = None
        self.model = None
        self.available_models_cache = None
        self.cache = CacheManager()
        self.batch_mode = False
        
        try:
            self.api_key = st.secrets.get("GEMINI_API_KEY")
            if not self.api_key:
                self.api_key = st.secrets.get("gemini", {}).get("api_key")
            
            if not self.api_key:
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.toml")
                return

            genai.configure(api_key=self.api_key)
            self.model = True
            
            try:
                self.available_models_cache = self._list_available_models()
            except Exception:
                pass
            
        except Exception as e:
            st.error(f"🤖 Error Crítico Configuración Gemini: {e}")

    def _list_available_models(self):
        try:
            models = genai.list_models()
            model_names_short = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    full_name = model.name
                    if '/' in full_name:
                        short_name = full_name.split('/')[-1]
                        model_names_short.append(short_name)
                    else:
                        model_names_short.append(full_name)
            return model_names_short
        except Exception as e:
            logger.error(f"Error al listar modelos: {e}")
            return []

    def _parse_text_response(self, text_response):
        sentimiento = None
        explicacion = "Análisis automático."

        try:
            clasif_match = re.search(r"CLASIFICACI[ÓO]N:\s*([^\n]*)", text_response, re.IGNORECASE)
            
            if not clasif_match:
                if re.search(r"\b(Positivo|Positiva)\b", text_response, re.IGNORECASE):
                    sentimiento = "Positivo"
                elif re.search(r"\b(Negativo|Negativa)\b", text_response, re.IGNORECASE):
                    sentimiento = "Negativo"
                elif re.search(r"\b(Neutro|Neutra)\b", text_response, re.IGNORECASE):
                    sentimiento = "Neutro"
            
            if clasif_match:
                raw_sent = clasif_match.group(1).strip()
                raw_sent_clean = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]", "", raw_sent)
                
                if re.search(r"\b(Positivo|Positiva)\b", raw_sent_clean, re.IGNORECASE):
                    sentimiento = "Positivo"
                elif re.search(r"\b(Negativo|Negativa)\b", raw_sent_clean, re.IGNORECASE):
                    sentimiento = "Negativo"
                elif re.search(r"\b(Neutro|Neutra)\b", raw_sent_clean, re.IGNORECASE):
                    sentimiento = "Neutro"

            if sentimiento is None:
                texto_lower = text_response.lower()
                palabras_positivas = ["positivo", "favorable", "bueno", "crecimiento", "éxito", "inversión", "exportación"]
                palabras_negativas = ["negativo", "desfavorable", "malo", "crisis", "pérdida", "problema", "sequía", "plaga"]
                
                conteo_pos = sum(1 for palabra in palabras_positivas if palabra in texto_lower)
                conteo_neg = sum(1 for palabra in palabras_negativas if palabra in texto_lower)
                
                if conteo_pos > conteo_neg:
                    sentimiento = "Positivo"
                elif conteo_neg > conteo_pos:
                    sentimiento = "Negativo"
                else:
                    sentimiento = "Neutro"

            arg_match = re.search(r"ARGUMENTO:\s*(.*?)(?:\n\n|\Z)", text_response, re.IGNORECASE | re.DOTALL)
            if not arg_match:
                arg_match = re.search(r"(?:ARGUMENTO|EXPLICACI[ÓO]N|RAZ[ÓO]N):\s*(.*)", text_response, re.IGNORECASE | re.DOTALL)
            
            if arg_match:
                explicacion = arg_match.group(1).strip()
                explicacion = re.sub(r'\s+', ' ', explicacion)

        except Exception as e:
            logger.error(f"Error parseando respuesta: {e}")
            if sentimiento is None:
                sentimiento = "Neutro"
                explicacion = f"Error al procesar respuesta: {str(e)}"

        if sentimiento not in ["Positivo", "Negativo", "Neutro"]:
            sentimiento = "Neutro"

        return {"sentimiento": sentimiento, "explicacion": explicacion}

    def analyze_news(self, text, use_cache=True):
        if not self.api_key:
            return {"sentimiento": "Neutro", "explicacion": "Error: Sin API Key"}
        
        if use_cache:
            cached_result = self.cache.get(text)
            if cached_result:
                logger.info(f"✅ Resultado del caché (hits: {cached_result.get('cache_hits', 0)})")
                return cached_result

        prompt = f"""Eres un analista experto en riesgos agroindustriales para el Valle del Cauca, Colombia.

Tu tarea es clasificar el SENTIMIENTO de la siguiente noticia en UNA de estas tres categorías EXACTAS:

🔴 NEGATIVO: Noticias sobre crisis, problemas, pérdidas, sequías, plagas, paros, bloqueos, inseguridad, extorsión, caídas de precios, conflictos, protestas, daños ambientales, precios injustos, pérdidas económicas.

🟢 POSITIVO: Noticias sobre inversiones, exportaciones exitosas, subsidios, tecnología implementada, alianzas comerciales, superávit, cosechas récord, crecimiento, acuerdos comerciales, innovaciones exitosas, desarrollo del sector.

⚪ NEUTRO: Solo noticias puramente informativas sin carga emocional clara, boletines administrativos, reportes estadísticos sin interpretación positiva o negativa, anuncios neutros.

CONTEXTO: Considera el impacto en el sector agroindustrial del Valle del Cauca (caña de azúcar, café, frutas, hortalizas).

NOTICIA A ANALIZAR:
"{text}"

INSTRUCCIONES CRÍTICAS:
1. Analiza cuidadosamente el contenido y determina el sentimiento REAL
2. NO uses "Neutro" por defecto - solo si realmente es informativo sin carga emocional
3. Responde EXACTAMENTE en este formato (sin texto adicional antes o después):

CLASIFICACIÓN: Positivo
ARGUMENTO: [Explicación clara de 1-2 frases en español sobre por qué clasificaste así]

O

CLASIFICACIÓN: Negativo
ARGUMENTO: [Explicación clara de 1-2 frases en español sobre por qué clasificaste así]

O

CLASIFICACIÓN: Neutro
ARGUMENTO: [Explicación clara de 1-2 frases en español sobre por qué clasificaste así]

IMPORTANTE: Responde SOLO con las dos líneas (CLASIFICACIÓN y ARGUMENTO), sin texto adicional."""

        candidates = [
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
        ]
        
        if self.available_models_cache:
            preferred_models = [m for m in self.available_models_cache 
                               if any(x in m for x in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]) 
                               and "exp" not in m.lower()]
            if preferred_models:
                candidates = preferred_models[:3] + [c for c in candidates if c not in preferred_models]

        for model_name in candidates:
            try:
                model = genai.GenerativeModel(
                    model_name,
                    generation_config={
                        "temperature": 0.1, 
                        "max_output_tokens": 300,
                        "top_p": 0.8,
                        "top_k": 40
                    },
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                
                response = model.generate_content(prompt)
                
                if response.parts and response.text:
                    resultado = self._parse_text_response(response.text)
                    
                    if use_cache:
                        self.cache.set(text, resultado["sentimiento"], resultado["explicacion"])
                    
                    if self.available_models_cache is None:
                        self.available_models_cache = []
                    if model_name not in self.available_models_cache:
                        self.available_models_cache.insert(0, model_name)
                    elif self.available_models_cache.index(model_name) > 0:
                        self.available_models_cache.remove(model_name)
                        self.available_models_cache.insert(0, model_name)
                    
                    logger.debug(f"✅ Modelo {model_name} funcionó correctamente")
                    return resultado
                else:
                    logger.warning(f"⚠️ Modelo {model_name} no retornó contenido válido")
                    continue
                
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    logger.warning(f"⚠️ Modelo {model_name} no encontrado (404)")
                    if self.available_models_cache and model_name in self.available_models_cache:
                        self.available_models_cache.remove(model_name)
                    continue
                elif "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    logger.warning(f"⚠️ Cuota agotada en {model_name}. Esperando 10s...")
                    if self.available_models_cache and model_name in self.available_models_cache:
                        self.available_models_cache.remove(model_name)
                    time.sleep(10)
                    continue
                else:
                    logger.error(f"❌ Error en {model_name}: {error_msg[:200]}")
                    continue
        
        return {"sentimiento": "Neutro", "explicacion": "Error: Sistema saturado. Intenta más tarde."}

    def analyze_batch(self, df, progress_bar=None, use_smart_batch=True):
        results_sent = []
        results_expl = []
        total = len(df)
        
        if total == 0: return [], []
        
        cache_hits = 0
        api_calls = 0

        for index, row in df.iterrows():
            titular = str(row.get('titular', ''))
            cuerpo = str(row.get('cuerpo', ''))
            text = f"{titular}. {cuerpo}"
            
            analysis = self.analyze_news(text, use_cache=use_smart_batch)
            
            if analysis.get("from_cache"):
                cache_hits += 1
            else:
                api_calls += 1
            
            results_sent.append(analysis["sentimiento"])
            results_expl.append(analysis["explicacion"])
            
            if progress_bar:
                progress_bar.progress((index + 1) / total)
            
            if not analysis.get("from_cache"):
                time.sleep(2)
        
        logger.info(f"📊 Batch completado: {cache_hits} del caché, {api_calls} llamadas API")
        
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
                if not analysis.get("from_cache"):
                    time.sleep(2)
            return analyzed_data
        except Exception as e:
            st.error(f"Error Web: {e}")
            return []

