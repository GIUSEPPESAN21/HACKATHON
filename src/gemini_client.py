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
from src.cache_manager import CacheManager

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgroSentimentAnalyzer:
    def __init__(self):
        # INICIALIZACIÓN SEGURA: Definimos atributos por defecto para evitar AttributeError
        self.api_key = None
        self.model = None # Se mantiene por compatibilidad, aunque usamos rotación dinámica
        self.available_models_cache = None  # Cache de modelos disponibles
        self.cache = CacheManager()  # Sistema de caché para reducir llamadas API
        self.batch_mode = False  # Modo batch para procesar múltiples noticias
        
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

    def analyze_news(self, text, use_cache=True):
        """
        Analiza una noticia con caché inteligente para reducir consumo de API.
        
        Args:
            text: Texto de la noticia
            use_cache: Si True, busca en caché antes de llamar a la API
        
        Returns:
            dict con sentimiento y explicación
        """
        if not self.api_key:
            return {"sentimiento": "Neutro", "explicacion": "Error: Sin API Key"}
        
        # 🚀 OPTIMIZACIÓN 1: Verificar caché primero
        if use_cache:
            cached_result = self.cache.get(text)
            if cached_result:
                logger.info(f"✅ Resultado obtenido del caché (hits: {cached_result.get('cache_hits', 0)})")
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

        # 🚀 OPTIMIZACIÓN 2: Priorizar modelos FLASH (más rápidos y baratos)
        # Lista ordenada por COSTO y VELOCIDAD (Flash < Pro)
        candidates = [
            "gemini-2.0-flash-exp",    # Experimental pero más barato (prioridad 1)
            "gemini-2.0-flash",        # Modelo estable y económico (prioridad 2)
            "gemini-1.5-flash",        # Fallback flash económico
            "gemini-1.5-flash-latest", # Última versión flash
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
                    
                    # 🚀 OPTIMIZACIÓN 3: Guardar en caché para futuros usos
                    if use_cache:
                        self.cache.set(text, resultado["sentimiento"], resultado["explicacion"])
                    
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
                    logger.warning(f"⚠️ Cuota agotada en {model_name}. Esperando 10s (reducido)...")
                    # Remover modelo con problemas de cuota del cache si está ahí
                    if self.available_models_cache and model_name in self.available_models_cache:
                        self.available_models_cache.remove(model_name)
                    time.sleep(10) # 🚀 REDUCIDO de 20s a 10s
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

    def analyze_batch(self, df, progress_bar=None, use_smart_batch=True):
        """
        🚀 OPTIMIZADO: Procesa TODAS las noticias en UN SOLO llamado a la API por sesión
        Máxima optimización: 1 llamada API independientemente del número de noticias
        
        Args:
            df: DataFrame con noticias
            progress_bar: Barra de progreso de Streamlit
            use_smart_batch: Si True, usa procesamiento en un solo batch (ignorado, siempre activo)
        """
        total = len(df)
        
        if total == 0: 
            return [], []
        
        # Separar noticias en caché vs nuevas
        texts_to_analyze = []
        cached_results = {}
        cache_hits = 0
        
        for index, row in df.iterrows():
            titular = str(row.get('titular', ''))
            cuerpo = str(row.get('cuerpo', ''))
            text = f"{titular}. {cuerpo}"
            
            # Verificar caché primero
            cached = self.cache.get(text)
            if cached:
                cached_results[index] = cached
                cache_hits += 1
            else:
                texts_to_analyze.append((index, text))
        
        # Si todas están en caché, retornar inmediatamente
        if len(texts_to_analyze) == 0:
            logger.info(f"✅ Todas las {total} noticias están en caché. 0 llamadas API.")
            results_sent = [cached_results.get(i, {}).get("sentimiento", "Neutro") for i in range(total)]
            results_expl = [cached_results.get(i, {}).get("explicacion", "Del caché") for i in range(total)]
            if progress_bar:
                progress_bar.progress(1.0)
            return results_sent, results_expl
        
        # 🚀 OPTIMIZACIÓN CRÍTICA: UN SOLO LLAMADO para todas las noticias nuevas
        logger.info(f"📊 Analizando {len(texts_to_analyze)} noticias nuevas en UN SOLO llamado API (sesión única)")
        
        if progress_bar:
            progress_bar.progress(0.3)  # 30% - preparando
        
        # Llamar al método de análisis único
        new_results = self._analyze_session_batch([text for _, text in texts_to_analyze])
        
        if progress_bar:
            progress_bar.progress(0.7)  # 70% - procesando
        
        # Guardar en caché y construir resultados finales
        results_sent = []
        results_expl = []
        
        result_index = 0
        for i in range(total):
            if i in cached_results:
                # Del caché
                results_sent.append(cached_results[i]["sentimiento"])
                results_expl.append(cached_results[i]["explicacion"])
            else:
                # Del análisis nuevo
                if result_index < len(new_results):
                    result = new_results[result_index]
                    results_sent.append(result["sentimiento"])
                    results_expl.append(result["explicacion"])
                    
                    # Guardar en caché
                    _, text = texts_to_analyze[result_index]
                    self.cache.set(text, result["sentimiento"], result["explicacion"])
                    result_index += 1
                else:
                    # Fallback si algo falló
                    results_sent.append("Neutro")
                    results_expl.append("Error en procesamiento")
        
        if progress_bar:
            progress_bar.progress(1.0)  # 100% - completado
        
        # Log de optimización
        api_calls = 1 if len(texts_to_analyze) > 0 else 0
        logger.info(f"📊 Sesión completada: {cache_hits} del caché, {api_calls} llamada(s) API ({(cache_hits/total*100):.1f}% ahorro por caché, {((total-api_calls)/total*100):.1f}% ahorro total)")
        
        return results_sent, results_expl
    
    def _analyze_session_batch(self, texts_list):
        """
        🚀 MÁXIMA OPTIMIZACIÓN: Analiza TODAS las noticias en UN SOLO llamado a Gemini
        Reduce consumo de API a 1 llamada independientemente del número de noticias
        
        Args:
            texts_list: Lista de textos a analizar (todas las noticias de la sesión)
        
        Returns:
            Lista de diccionarios con sentimiento y explicación
        """
        if not self.api_key:
            return [{"sentimiento": "Neutro", "explicacion": "Error: Sin API Key"} for _ in texts_list]
        
        if not texts_list:
            return []
        
        total = len(texts_list)
        logger.info(f"🚀 Iniciando análisis único de {total} noticias en una sola llamada API")
        
        # Construir prompt con TODAS las noticias
        prompt_batch = """Eres un analista experto en riesgos agroindustriales para el Valle del Cauca, Colombia.

Tu tarea es clasificar el SENTIMIENTO de CADA noticia en UNA de estas tres categorías EXACTAS:

🔴 NEGATIVO: Noticias sobre crisis, problemas, pérdidas, sequías, plagas, paros, bloqueos, inseguridad, extorsión, caídas de precios, conflictos, protestas, daños ambientales, precios injustos, pérdidas económicas.

🟢 POSITIVO: Noticias sobre inversiones, exportaciones exitosas, subsidios, tecnología implementada, alianzas comerciales, superávit, cosechas récord, crecimiento, acuerdos comerciales, innovaciones exitosas, desarrollo del sector.

⚪ NEUTRO: Solo noticias puramente informativas sin carga emocional clara, boletines administrativos, reportes estadísticos sin interpretación positiva o negativa, anuncios neutros.

CONTEXTO: Considera el impacto en el sector agroindustrial del Valle del Cauca (caña de azúcar, café, frutas, hortalizas).

NOTICIAS A ANALIZAR:
"""
        
        # Agregar todas las noticias (limitar a 500 caracteres cada una para evitar tokens excesivos)
        for idx, text in enumerate(texts_list, 1):
            text_limited = text[:500] if len(text) > 500 else text
            prompt_batch += f"\n--- NOTICIA {idx} ---\n{text_limited}\n"
        
        prompt_batch += f"""

INSTRUCCIONES CRÍTICAS:
1. Analiza cuidadosamente CADA noticia y determina su sentimiento REAL
2. NO uses "Neutro" por defecto - solo si realmente es informativo sin carga emocional
3. Responde EXACTAMENTE en este formato (una línea por noticia, numeradas del 1 al {total}):

1|Sentimiento|Explicación breve
2|Sentimiento|Explicación breve
3|Sentimiento|Explicación breve
...

Donde Sentimiento debe ser EXACTAMENTE: "Positivo", "Negativo" o "Neutro"
Y Explicación debe ser una frase breve en español explicando por qué.

IMPORTANTE: Responde SOLO con las líneas numeradas, sin texto adicional antes o después."""
        
        # Intentar con modelos económicos primero
        candidates = [
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
        ]
        
        # Ajustar tokens según cantidad de noticias
        max_tokens = min(8000, 300 + (total * 100))  # ~100 tokens por noticia + overhead
        
        for model_name in candidates:
            try:
                model = genai.GenerativeModel(
                    model_name,
                    generation_config={
                        "temperature": 0.1,
                        "max_output_tokens": max_tokens,
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
                
                logger.info(f"🔄 Llamando a {model_name} con {total} noticias...")
                response = model.generate_content(prompt_batch)
                
                if response.text:
                    # Parsear respuesta
                    batch_results = self._parse_batch_response(response.text, total)
                    
                    if len(batch_results) == total:
                        logger.info(f"✅ Análisis único completado: {total} noticias procesadas en 1 llamada API")
                        return batch_results
                    else:
                        logger.warning(f"⚠️ Respuesta incompleta: {len(batch_results)}/{total} noticias. Reintentando...")
                        # Continuar al siguiente modelo
                        continue
                else:
                    logger.warning(f"⚠️ Modelo {model_name} no retornó contenido válido")
                    continue
                    
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    logger.warning(f"⚠️ Modelo {model_name} no encontrado. Probando siguiente...")
                    continue
                elif "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    logger.warning(f"⚠️ Cuota agotada en {model_name}. Esperando 10s...")
                    time.sleep(10)
                    continue
                else:
                    logger.error(f"❌ Error en {model_name}: {error_msg[:200]}")
                    continue
        
        # Si todos los modelos fallaron, usar fallback individual (pero esto no debería pasar)
        logger.error(f"❌ Todos los modelos fallaron. Usando fallback individual para {total} noticias.")
        results = []
        for text in texts_list:
            result = self.analyze_news(text, use_cache=False)
            results.append(result)
            time.sleep(0.5)  # Pequeña pausa entre llamadas
        return results

    def analyze_batch_smart(self, texts_list, max_per_batch=5):
        """
        🚀 SUPER OPTIMIZACIÓN: Procesa múltiples noticias en UN SOLO prompt
        Reduce consumo de API hasta en 80% vs análisis individual
        
        Args:
            texts_list: Lista de textos a analizar
            max_per_batch: Máximo de noticias por prompt (5 óptimo)
        
        Returns:
            Lista de diccionarios con sentimiento y explicación
        """
        if not self.api_key:
            return [{"sentimiento": "Neutro", "explicacion": "Error: Sin API Key"} for _ in texts_list]
        
        results = []
        total = len(texts_list)
        
        # Procesar en lotes
        for i in range(0, total, max_per_batch):
            batch = texts_list[i:i+max_per_batch]
            
            # Construir prompt con múltiples noticias
            prompt_batch = """Eres un analista experto en riesgos agroindustriales para el Valle del Cauca, Colombia.

Clasifica el SENTIMIENTO de CADA noticia en: Positivo, Negativo, o Neutro.

CONTEXTO:
🔴 NEGATIVO: Crisis, problemas, pérdidas, sequías, plagas, conflictos
🟢 POSITIVO: Inversiones, exportaciones, tecnología, crecimiento
⚪ NEUTRO: Información sin carga emocional clara

"""
            
            for idx, text in enumerate(batch, 1):
                prompt_batch += f"\n--- NOTICIA {idx} ---\n{text[:400]}\n"  # Limitar a 400 chars por noticia
            
            prompt_batch += """

RESPONDE EN ESTE FORMATO EXACTO (una línea por noticia):
1|Positivo|Razón breve
2|Negativo|Razón breve
3|Neutro|Razón breve
..."""
            
            # Intentar con modelo más económico primero
            try:
                model = genai.GenerativeModel(
                    "gemini-2.0-flash-exp",  # Más barato para batches
                    generation_config={
                        "temperature": 0.1,
                        "max_output_tokens": 500,  # Suficiente para 5 noticias
                    }
                )
                
                response = model.generate_content(prompt_batch)
                
                if response.text:
                    # Parsear respuesta multi-línea
                    batch_results = self._parse_batch_response(response.text, len(batch))
                    results.extend(batch_results)
                else:
                    # Fallback a análisis individual si falla batch
                    for text in batch:
                        results.append(self.analyze_news(text))
                
                time.sleep(1)  # Espera mínima entre batches
                
            except Exception as e:
                logger.error(f"Error en batch smart: {e}. Usando fallback individual.")
                for text in batch:
                    results.append(self.analyze_news(text))
        
        return results
    
    def _parse_batch_response(self, response_text, expected_count):
        """
        Parsea respuesta de batch con formato: N|Sentimiento|Explicacion
        Maneja múltiples formatos para mayor robustez
        """
        results = []
        lines = response_text.strip().split('\n')
        
        # Diccionario para almacenar resultados por número
        parsed_results = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Patrón 1: Formato estándar N|Sentimiento|Explicacion
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                
                # Intentar extraer número de noticia
                try:
                    if parts[0].isdigit():
                        num = int(parts[0])
                    elif parts[0].startswith('NOTICIA') or parts[0].startswith('Noticia'):
                        # Formato: "NOTICIA 1|..."
                        num = int(re.search(r'\d+', parts[0]).group())
                    else:
                        # Si no hay número, usar el índice
                        num = len(parsed_results) + 1
                except:
                    num = len(parsed_results) + 1
                
                if len(parts) >= 3:
                    sentimiento = parts[1].strip()
                    explicacion = '|'.join(parts[2:]).strip()  # Unir resto por si hay | en explicación
                elif len(parts) == 2:
                    # Formato alternativo: N|Sentimiento (sin explicación)
                    sentimiento = parts[1].strip()
                    explicacion = "Análisis automático."
                else:
                    continue
                
                # Validar y normalizar sentimiento
                sentimiento_lower = sentimiento.lower()
                if "positiv" in sentimiento_lower or sentimiento_lower == "positivo":
                    sentimiento = "Positivo"
                elif "negativ" in sentimiento_lower or sentimiento_lower == "negativo":
                    sentimiento = "Negativo"
                elif "neutr" in sentimiento_lower or sentimiento_lower == "neutro":
                    sentimiento = "Neutro"
                else:
                    # Si no coincide, intentar detectar por palabras clave en explicación
                    expl_lower = explicacion.lower()
                    if any(palabra in expl_lower for palabra in ["crisis", "problema", "pérdida", "sequía", "plaga", "conflicto"]):
                        sentimiento = "Negativo"
                    elif any(palabra in expl_lower for palabra in ["inversión", "crecimiento", "éxito", "exportación", "desarrollo"]):
                        sentimiento = "Positivo"
                    else:
                        sentimiento = "Neutro"
                
                parsed_results[num] = {
                    "sentimiento": sentimiento,
                    "explicacion": explicacion if explicacion else "Análisis automático."
                }
            
            # Patrón 2: Formato con CLASIFICACIÓN y ARGUMENTO por noticia
            elif "CLASIFICACI" in line.upper() and ":" in line:
                # Buscar número de noticia en líneas anteriores
                num = len(parsed_results) + 1
                # Extraer sentimiento de esta línea
                sent_match = re.search(r"(Positivo|Negativo|Neutro)", line, re.IGNORECASE)
                if sent_match:
                    sentimiento = sent_match.group(1).capitalize()
                    # Buscar explicación en línea siguiente
                    explicacion = "Análisis automático."
                    parsed_results[num] = {
                        "sentimiento": sentimiento,
                        "explicacion": explicacion
                    }
        
        # Ordenar por número y construir lista final
        sorted_nums = sorted(parsed_results.keys())
        for num in sorted_nums:
            if num <= expected_count:
                results.append(parsed_results[num])
        
        # Si no parseó bien o faltan resultados, rellenar
        while len(results) < expected_count:
            results.append({
                "sentimiento": "Neutro", 
                "explicacion": "Error en procesamiento batch - respuesta no parseada correctamente"
            })
        
        # Limitar a expected_count por si acaso
        return results[:expected_count]
    
    def search_and_analyze_web(self, query="agroindustria Valle del Cauca", max_results=5):
        """
        🚀 OPTIMIZADO: Busca noticias web y las analiza en UN SOLO llamado API
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(keywords=query, region="co-co", safesearch="off", max_results=max_results))
            
            if not results: 
                return []

            # Separar en caché vs nuevas
            texts_to_analyze = []
            cached_analyses = {}
            web_items = []
            
            for idx, item in enumerate(results):
                full_text = f"{item.get('title','')}. {item.get('body','')}"
                
                # Verificar caché
                cached = self.cache.get(full_text)
                if cached:
                    cached_analyses[idx] = cached
                else:
                    texts_to_analyze.append((idx, full_text))
                
                web_items.append(item)
            
            # 🚀 OPTIMIZACIÓN: Analizar todas las nuevas en un solo llamado
            if texts_to_analyze:
                logger.info(f"🌐 Analizando {len(texts_to_analyze)} noticias web nuevas en 1 llamada API")
                new_analyses = self._analyze_session_batch([text for _, text in texts_to_analyze])
                
                # Guardar en caché
                for (idx, text), analysis in zip(texts_to_analyze, new_analyses):
                    self.cache.set(text, analysis["sentimiento"], analysis["explicacion"])
                    cached_analyses[idx] = analysis
            
            # Construir resultado final
            analyzed_data = []
            analysis_idx = 0
            
            for idx, item in enumerate(web_items):
                if idx in cached_analyses:
                    analysis = cached_analyses[idx]
                else:
                    # Fallback (no debería pasar)
                    analysis = {"sentimiento": "Neutro", "explicacion": "Error en análisis"}
                
                analyzed_data.append({
                    "titular": item.get('title',''),
                    "cuerpo": item.get('body',''),
                    "fecha": item.get('date',''),
                    "fuente": item.get('source',''),
                    "url": item.get('url',''),
                    "sentimiento_ia": analysis["sentimiento"],
                    "explicacion_ia": analysis["explicacion"],
                    "id_original": f"web_{int(time.time())}_{idx}"
                })
            
            logger.info(f"✅ {len(analyzed_data)} noticias web analizadas (1 llamada API para nuevas)")
            return analyzed_data
            
        except Exception as e:
            logger.error(f"Error Web: {e}")
            if 'st' in globals():
                st.error(f"Error Web: {e}")
            return []
