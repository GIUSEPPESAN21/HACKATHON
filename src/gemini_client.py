import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
import time
import re
import logging
try:
    from ddgs import DDGS  # Nuevo nombre del paquete
except ImportError:
    from duckduckgo_search import DDGS  # Fallback al nombre antiguo

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgroSentimentAnalyzer:
    def __init__(self):
        # INICIALIZACIÓN SEGURA: Definimos atributos por defecto para evitar AttributeError
        self.api_key = None
        self.model = None # Se mantiene por compatibilidad, aunque usamos rotación dinámica
        self.available_models_cache = None  # Cache de modelos disponibles
        
        try:
            self.api_key = st.secrets.get("GEMINI_API_KEY")
            if not self.api_key:
                self.api_key = st.secrets.get("gemini", {}).get("api_key")
            
            if not self.api_key:
                st.error("⚠️ Falta GEMINI_API_KEY en secrets.toml")
                return

            genai.configure(api_key=self.api_key)
            self.model = True # Bandera para indicar que estamos listos
            
            # Intentar detectar modelos disponibles al inicio (opcional, no crítico)
            try:
                self.available_models_cache = self._list_available_models()
            except Exception:
                pass  # No crítico si falla, se intentará después
            
        except Exception as e:
            st.error(f"🤖 Error Crítico Configuración Gemini: {e}")

    def _list_available_models(self):
        """Lista los modelos disponibles en la API de Gemini para debugging."""
        try:
            models = genai.list_models()
            available_models = []
            model_names_short = []  # Nombres cortos sin prefijo "models/"
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    full_name = model.name
                    available_models.append(full_name)
                    # Extraer nombre corto (ej: "models/gemini-1.5-flash-latest" -> "gemini-1.5-flash-latest")
                    if '/' in full_name:
                        short_name = full_name.split('/')[-1]
                        model_names_short.append(short_name)
                    else:
                        model_names_short.append(full_name)
            
            if model_names_short:
                # Solo loggear una vez o en modo debug para reducir verbosidad
                logger.debug(f"📋 Modelos disponibles ({len(model_names_short)}): {', '.join(model_names_short[:10])}")
            return model_names_short  # Retornar nombres cortos para facilitar uso
        except Exception as e:
            logger.error(f"Error al listar modelos: {e}")
            return []

    def _parse_text_response(self, text_response):
        """Analiza la respuesta de texto plano para extraer clasificación y argumento."""
        sentimiento = None  # Cambio crítico: No usar "Neutro" por defecto
        explicacion = "Análisis automático."

        try:
            # Búsqueda más robusta con múltiples patrones
            # Patrón 1: "CLASIFICACIÓN:" o "CLASIFICACION:" (con/sin tilde)
            clasif_match = re.search(r"CLASIFICACI[ÓO]N:\s*([^\n]*)", text_response, re.IGNORECASE)
            
            # Patrón 2: Buscar directamente las palabras en el texto
            if not clasif_match:
                # Buscar "Positivo", "Negativo" o "Neutro" en el texto
                if re.search(r"\b(Positivo|Positiva)\b", text_response, re.IGNORECASE):
                    sentimiento = "Positivo"
                elif re.search(r"\b(Negativo|Negativa)\b", text_response, re.IGNORECASE):
                    sentimiento = "Negativo"
                elif re.search(r"\b(Neutro|Neutra)\b", text_response, re.IGNORECASE):
                    sentimiento = "Neutro"
            
            # Si encontramos el patrón con "CLASIFICACIÓN:"
            if clasif_match:
                raw_sent = clasif_match.group(1).strip()
                # Limpieza de caracteres extra pero preservando espacios para mejor matching
                raw_sent_clean = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]", "", raw_sent)
                
                # Búsqueda más precisa
                if re.search(r"\b(Positivo|Positiva)\b", raw_sent_clean, re.IGNORECASE):
                    sentimiento = "Positivo"
                elif re.search(r"\b(Negativo|Negativa)\b", raw_sent_clean, re.IGNORECASE):
                    sentimiento = "Negativo"
                elif re.search(r"\b(Neutro|Neutra)\b", raw_sent_clean, re.IGNORECASE):
                    sentimiento = "Neutro"

            # Si aún no encontramos sentimiento, buscar en todo el texto
            if sentimiento is None:
                texto_lower = text_response.lower()
                # Buscar palabras clave que indiquen sentimiento
                palabras_positivas = ["positivo", "favorable", "bueno", "crecimiento", "éxito", "inversión", "exportación"]
                palabras_negativas = ["negativo", "desfavorable", "malo", "crisis", "pérdida", "problema", "sequía", "plaga"]
                
                conteo_pos = sum(1 for palabra in palabras_positivas if palabra in texto_lower)
                conteo_neg = sum(1 for palabra in palabras_negativas if palabra in texto_lower)
                
                if conteo_pos > conteo_neg:
                    sentimiento = "Positivo"
                elif conteo_neg > conteo_pos:
                    sentimiento = "Negativo"
                else:
                    # Solo usar Neutro si realmente no hay indicios claros
                    sentimiento = "Neutro"
                    logger.warning(f"No se pudo determinar sentimiento claramente. Texto: {text_response[:200]}")

            # Extraer argumento/explicación
            arg_match = re.search(r"ARGUMENTO:\s*(.*?)(?:\n\n|\Z)", text_response, re.IGNORECASE | re.DOTALL)
            if not arg_match:
                # Buscar cualquier explicación después de la clasificación
                arg_match = re.search(r"(?:ARGUMENTO|EXPLICACI[ÓO]N|RAZ[ÓO]N):\s*(.*)", text_response, re.IGNORECASE | re.DOTALL)
            
            if arg_match:
                explicacion = arg_match.group(1).strip()
                # Limpiar explicación de caracteres extra
                explicacion = re.sub(r'\s+', ' ', explicacion)

        except Exception as e:
            logger.error(f"Error parseando respuesta: {e}. Respuesta completa: {text_response[:500]}")
            # En caso de error, intentar al menos extraer algo del texto
            if sentimiento is None:
                sentimiento = "Neutro"
                explicacion = f"Error al procesar respuesta: {str(e)}"

        # Validación final: asegurar que siempre tenemos un sentimiento válido
        if sentimiento not in ["Positivo", "Negativo", "Neutro"]:
            logger.error(f"Sentimiento inválido detectado: '{sentimiento}'. Normalizando a 'Neutro'.")
            sentimiento = "Neutro"

        return {"sentimiento": sentimiento, "explicacion": explicacion}

    def analyze_news(self, text):
        """
        Analiza una noticia con estrategia de espera agresiva si se agota la cuota.
        """
        if not self.api_key:
            return {"sentimiento": "Neutro", "explicacion": "Error: Sin API Key"}

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

        # Lista de modelos ordenada por EFICIENCIA Y DISPONIBILIDAD
        # NOTA: Actualizado según modelos realmente disponibles (2025)
        # Priorizar modelos que sabemos que funcionan según logs del sistema
        candidates = [
            "gemini-2.5-flash",        # Modelo más nuevo y eficiente (prioridad 1)
            "gemini-2.0-flash",        # Modelo estable que funciona correctamente (prioridad 2)
            "gemini-2.0-flash-001",    # Variante estable de 2.0 flash
            "gemini-2.5-pro",          # Modelo pro más reciente
            "gemini-pro",              # Modelo estándar (compatibilidad legacy)
        ]
        
        # Si tenemos modelos en cache que funcionaron antes, priorizarlos
        if self.available_models_cache:
            # Filtrar modelos conocidos que funcionan bien
            preferred_models = [m for m in self.available_models_cache 
                               if any(x in m for x in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]) 
                               and "exp" not in m.lower()]  # Evitar experimentales con problemas de cuota
            if preferred_models:
                # Insertar modelos preferidos al inicio
                candidates = preferred_models[:3] + [c for c in candidates if c not in preferred_models]

        for model_name in candidates:
            try:
                # Intentar crear el modelo - si el nombre no existe, generará error
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
                    # Guardar modelo exitoso en cache para priorizarlo en el futuro
                    if self.available_models_cache is None:
                        self.available_models_cache = []
                    if model_name not in self.available_models_cache:
                        self.available_models_cache.insert(0, model_name)  # Priorizar al inicio
                    elif self.available_models_cache.index(model_name) > 0:
                        # Mover al inicio si ya estaba en la lista
                        self.available_models_cache.remove(model_name)
                        self.available_models_cache.insert(0, model_name)
                    
                    # Log para debugging (solo en desarrollo, menos verboso)
                    if resultado["sentimiento"] == "Neutro":
                        logger.debug(f"Clasificación Neutro detectada. Respuesta Gemini: {response.text[:200]}")
                    logger.debug(f"✅ Modelo {model_name} funcionó correctamente")
                    return resultado
                else:
                    logger.warning(f"⚠️ Modelo {model_name} no retornó contenido válido")
                    continue
                
            except Exception as e:
                error_msg = str(e)
                # Manejo de errores específicos
                if "404" in error_msg or "not found" in error_msg.lower():
                    logger.warning(f"⚠️ Modelo {model_name} no encontrado (404). Probando siguiente modelo...")
                    # Remover modelo inexistente del cache si está ahí
                    if self.available_models_cache and model_name in self.available_models_cache:
                        self.available_models_cache.remove(model_name)
                    continue
                elif "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    logger.warning(f"⚠️ Cuota agotada en {model_name}. Esperando 20s para recuperar...")
                    # Remover modelo con problemas de cuota del cache si está ahí
                    if self.available_models_cache and model_name in self.available_models_cache:
                        self.available_models_cache.remove(model_name)
                    time.sleep(20) # Pausa larga de seguridad
                    continue
                else:
                    logger.error(f"❌ Error en {model_name}: {error_msg[:200]}")
                    continue

        # Si todos los modelos fallaron, intentar usar modelos disponibles detectados automáticamente
        logger.warning("⚠️ Todos los modelos candidatos fallaron. Intentando detectar modelos disponibles...")
        
        # Usar cache si está disponible, sino intentar listar ahora
        available_models = self.available_models_cache if self.available_models_cache else self._list_available_models()
        
        # Filtrar modelos: priorizar estables, evitar experimentales con problemas de cuota
        if available_models:
            # Filtrar modelos estables (evitar exp, preview, etc. que pueden tener problemas)
            stable_models = [m for m in available_models 
                           if not any(x in m.lower() for x in ["exp", "preview", "experimental"])
                           and any(x in m for x in ["gemini-2.5", "gemini-2.0", "gemini-pro"])]
            
            # Si no hay estables, usar los disponibles pero evitar los que sabemos que fallan
            if not stable_models:
                stable_models = [m for m in available_models if m not in candidates]  # Evitar los que ya fallaron
            
            # Si encontramos modelos disponibles, intentar usarlos
            if stable_models:
                logger.debug(f"🔄 Intentando con modelos detectados automáticamente: {', '.join(stable_models[:3])}")
                for model_name in stable_models[:3]:  # Intentar solo los primeros 3 para no demorar mucho
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
                            logger.debug(f"✅ Modelo {model_name} funcionó correctamente (detectado automáticamente)")
                            # Actualizar cache con este modelo que funcionó
                            if self.available_models_cache is None:
                                self.available_models_cache = []
                            if model_name not in self.available_models_cache:
                                self.available_models_cache.insert(0, model_name)  # Poner al inicio para priorizar
                            elif self.available_models_cache.index(model_name) > 0:
                                # Mover al inicio si ya estaba en la lista
                                self.available_models_cache.remove(model_name)
                                self.available_models_cache.insert(0, model_name)
                            return resultado
                    except Exception as e:
                        logger.debug(f"Modelo {model_name} falló: {str(e)[:100]}")
                        continue
        
        # Si llegamos aquí, todos los intentos fallaron
        logger.error("❌ Todos los modelos de Gemini fallaron. No se pudo analizar la noticia.")
        if available_models:
            logger.warning(f"💡 Modelos disponibles detectados: {', '.join(available_models[:5])}")
            logger.warning(f"💡 Los modelos candidatos intentados fueron: {', '.join(candidates)}")
        else:
            logger.error("No se pudieron listar modelos disponibles. Verifica tu API key y conexión.")
        
        return {"sentimiento": "Neutro", "explicacion": "Error: Sistema saturado o sin acceso a modelos de IA. Intenta más tarde."}

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
            
            # Pausa de seguridad entre noticias (5 segundos para evitar bloqueo)
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
                time.sleep(5)
            return analyzed_data
        except Exception as e:
            st.error(f"Error Web: {e}")
            return []
