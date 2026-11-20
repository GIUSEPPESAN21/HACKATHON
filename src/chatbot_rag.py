"""
Chatbot inteligente con RAG (Retrieval-Augmented Generation)
Permite interactuar con las noticias analizadas de forma conversacional
"""
import google.generativeai as genai
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AgriNewsBot:
    def __init__(self, api_key):
        """
        Inicializa el chatbot con API key de Gemini
        
        Args:
            api_key: Google Gemini API Key
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Usar modelo económico para chat
        self.chat_model = genai.GenerativeModel('gemini-flash-latest')
        
        # Historial de conversación
        self.conversation_history = []
        
        # Base de conocimiento (noticias cargadas)
        self.knowledge_base = []
        self.vectorizer = None
        self.tfidf_matrix = None
    
    def load_news_database(self, df):
        """
        Carga noticias en la base de conocimiento del bot
        
        Args:
            df: DataFrame con noticias analizadas
        """
        self.knowledge_base = []
        
        for index, row in df.iterrows():
            news_entry = {
                'id': index,
                'titular': str(row.get('titular', '')),
                'cuerpo': str(row.get('cuerpo', '')),
                'sentimiento': row.get('sentimiento_ia', 'Neutro'),
                'explicacion': row.get('explicacion_ia', ''),
                'fecha': row.get('fecha', ''),
                'text_full': f"{row.get('titular', '')} {row.get('cuerpo', '')} {row.get('explicacion_ia', '')}"
            }
            self.knowledge_base.append(news_entry)
        
        # Crear índice TF-IDF para búsqueda semántica
        if self.knowledge_base:
            texts = [entry['text_full'] for entry in self.knowledge_base]
            self.vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            logger.info(f"✅ Base de conocimiento cargada: {len(self.knowledge_base)} noticias")
    
    def retrieve_relevant_news(self, query, top_k=3):
        """
        Recupera noticias relevantes para la consulta (RAG)
        
        Args:
            query: Pregunta del usuario
            top_k: Número de noticias más relevantes a retornar
        
        Returns:
            Lista de noticias relevantes
        """
        if not self.knowledge_base or self.vectorizer is None:
            return []
        
        # Vectorizar consulta
        query_vector = self.vectorizer.transform([query])
        
        # Calcular similitud coseno
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Obtener índices de las más similares
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Filtrar solo las que tienen similitud > 0
        relevant_news = []
        for idx in top_indices:
            if similarities[idx] > 0:
                news = self.knowledge_base[idx].copy()
                news['similarity'] = float(similarities[idx])
                relevant_news.append(news)
        
        return relevant_news
    
    def chat(self, user_message):
        """
        Procesa mensaje del usuario y genera respuesta contextual
        
        Args:
            user_message: Mensaje del usuario
        
        Returns:
            Respuesta del bot
        """
        if not self.knowledge_base:
            return {
                'response': "⚠️ No hay noticias cargadas. Por favor, realiza primero un análisis de noticias.",
                'relevant_news': []
            }
        
        # Recuperar noticias relevantes
        relevant_news = self.retrieve_relevant_news(user_message, top_k=3)
        
        # Construir contexto para el modelo
        context = "CONTEXTO DE NOTICIAS RELEVANTES:\n\n"
        if relevant_news:
            for i, news in enumerate(relevant_news, 1):
                context += f"""
Noticia {i}:
- Titular: {news['titular']}
- Sentimiento: {news['sentimiento']}
- Análisis: {news['explicacion']}
- Fecha: {news['fecha']}
---
"""
        else:
            context += "No se encontraron noticias específicamente relevantes. Usa tu conocimiento general.\n"
        
        # Construir prompt
        prompt = f"""Eres un asistente experto en agroindustria del Valle del Cauca, Colombia.

Tu rol es ayudar al usuario a entender y analizar noticias del sector agroindustrial.

{context}

HISTORIAL DE CONVERSACIÓN:
{self._format_history()}

PREGUNTA DEL USUARIO: {user_message}

INSTRUCCIONES:
1. Responde de forma clara, concisa y profesional
2. Usa la información de las noticias relevantes cuando sea apropiado
3. Si las noticias no son relevantes, da una respuesta general basada en conocimiento del sector
4. Sé proactivo: ofrece insights adicionales o sugerencias
5. Usa emojis ocasionalmente para hacer la conversación más amigable
6. Mantén un tono experto pero accesible

RESPUESTA:"""
        
        try:
            # Generar respuesta
            response = self.chat_model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,  # Más creativo para chat
                    "max_output_tokens": 500,
                }
            )
            
            bot_response = response.text
            
            # Guardar en historial
            self.conversation_history.append({
                'user': user_message,
                'bot': bot_response
            })
            
            # Limitar historial a últimas 10 interacciones
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return {
                'response': bot_response,
                'relevant_news': relevant_news
            }
            
        except Exception as e:
            logger.error(f"Error en chatbot: {e}")
            return {
                'response': f"⚠️ Error al procesar tu pregunta: {str(e)}",
                'relevant_news': relevant_news
            }
    
    def _format_history(self):
        """Formatea historial de conversación"""
        if not self.conversation_history:
            return "(Inicio de conversación)"
        
        history_text = ""
        for interaction in self.conversation_history[-3:]:  # Últimas 3 interacciones
            history_text += f"Usuario: {interaction['user']}\n"
            history_text += f"Bot: {interaction['bot']}\n\n"
        
        return history_text
    
    def reset_conversation(self):
        """Reinicia la conversación"""
        self.conversation_history = []
        logger.info("Conversación reiniciada")
    
    def get_quick_stats(self):
        """Genera estadísticas rápidas de las noticias cargadas"""
        if not self.knowledge_base:
            return "No hay noticias cargadas."
        
        total = len(self.knowledge_base)
        positivas = sum(1 for n in self.knowledge_base if n['sentimiento'] == 'Positivo')
        negativas = sum(1 for n in self.knowledge_base if n['sentimiento'] == 'Negativo')
        neutras = sum(1 for n in self.knowledge_base if n['sentimiento'] == 'Neutro')
        
        return f"""📊 **Estadísticas de la Base de Conocimiento:**

🔢 Total de noticias: {total}
🟢 Positivas: {positivas} ({positivas/total*100:.1f}%)
🔴 Negativas: {negativas} ({negativas/total*100:.1f}%)
⚪ Neutras: {neutras} ({neutras/total*100:.1f}%)

💬 Puedes preguntarme sobre estas noticias."""
    
    def get_suggested_questions(self):
        """Genera preguntas sugeridas basadas en las noticias"""
        if not self.knowledge_base:
            return []
        
        # Analizar contenido para sugerir preguntas
        sentimiento_predominante = max(
            ['Positivo', 'Negativo', 'Neutro'],
            key=lambda s: sum(1 for n in self.knowledge_base if n['sentimiento'] == s)
        )
        
        suggestions = [
            "¿Cuáles son las principales amenazas para el sector agroindustrial?",
            "Resúmeme las noticias más importantes",
            "¿Qué oportunidades hay en el sector?",
        ]
        
        if sentimiento_predominante == "Negativo":
            suggestions.append("¿Cuáles son los principales problemas detectados?")
        elif sentimiento_predominante == "Positivo":
            suggestions.append("¿Qué buenas noticias hay para el sector?")
        
        return suggestions

