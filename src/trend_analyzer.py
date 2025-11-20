"""
Análisis de tendencias y predicciones para noticias agroindustriales
Utiliza machine learning para detectar patrones y generar insights
"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from collections import Counter
import re
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    def __init__(self):
        """Inicializa el analizador de tendencias"""
        self.df = None
    
    def load_data(self, df):
        """Carga datos para análisis"""
        self.df = df.copy()
        
        # Convertir fechas si es posible
        if 'fecha' in self.df.columns:
            try:
                self.df['fecha_parsed'] = pd.to_datetime(self.df['fecha'], errors='coerce')
            except:
                pass
    
    def get_sentiment_trend_over_time(self):
        """
        Analiza evolución del sentimiento en el tiempo
        
        Returns:
            DataFrame con tendencias temporales
        """
        if self.df is None or 'fecha_parsed' not in self.df.columns:
            return None
        
        # Filtrar filas con fecha válida
        df_with_dates = self.df[self.df['fecha_parsed'].notna()].copy()
        
        if len(df_with_dates) == 0:
            return None
        
        # Agrupar por fecha y sentimiento
        df_with_dates['fecha_only'] = df_with_dates['fecha_parsed'].dt.date
        
        trend = df_with_dates.groupby(['fecha_only', 'sentimiento_ia']).size().unstack(fill_value=0)
        
        return trend
    
    def extract_keywords(self, sentiment_filter=None, top_n=15):
        """
        Extrae palabras clave más frecuentes
        
        Args:
            sentiment_filter: "Positivo", "Negativo", "Neutro" o None para todos
            top_n: Número de palabras clave a retornar
        
        Returns:
            Lista de tuplas (palabra, frecuencia)
        """
        if self.df is None:
            return []
        
        # Filtrar por sentimiento si se especifica
        df_filtered = self.df if sentiment_filter is None else self.df[self.df['sentimiento_ia'] == sentiment_filter]
        
        # Combinar titular y cuerpo
        texts = df_filtered['titular'].fillna('') + ' ' + df_filtered['cuerpo'].fillna('')
        
        # Palabras a excluir (stopwords en español)
        stopwords_es = set([
            'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber',
            'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo',
            'pero', 'más', 'hacer', 'o', 'poder', 'decir', 'este', 'ir', 'otro', 'ese',
            'si', 'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy', 'sin',
            'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno', 'mismo', 'yo',
            'también', 'hasta', 'año', 'dos', 'querer', 'entre', 'así', 'primero',
            'desde', 'grande', 'eso', 'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella',
            'del', 'los', 'las', 'una', 'unos', 'unas', 'al', 'ha', 'han', 'he'
        ])
        
        # Extraer palabras
        all_words = []
        for text in texts:
            words = re.findall(r'\b[a-záéíóúñ]{4,}\b', text.lower())
            all_words.extend([w for w in words if w not in stopwords_es])
        
        # Contar frecuencias
        word_freq = Counter(all_words).most_common(top_n)
        
        return word_freq
    
    def cluster_news(self, n_clusters=3):
        """
        Agrupa noticias por similitud temática
        
        Args:
            n_clusters: Número de clusters a crear
        
        Returns:
            DataFrame con columna 'cluster' agregada
        """
        if self.df is None or len(self.df) < n_clusters:
            return None
        
        # Combinar textos
        texts = self.df['titular'].fillna('') + ' ' + self.df['cuerpo'].fillna('')
        
        # Vectorizar
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        X = vectorizer.fit_transform(texts)
        
        # Clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)
        
        # Agregar a DataFrame
        df_clustered = self.df.copy()
        df_clustered['cluster'] = clusters
        
        # Extraer temas principales de cada cluster
        cluster_themes = []
        feature_names = vectorizer.get_feature_names_out()
        
        for i in range(n_clusters):
            # Obtener centroide del cluster
            centroid = kmeans.cluster_centers_[i]
            # Top 5 palabras más relevantes
            top_indices = centroid.argsort()[-5:][::-1]
            theme_words = [feature_names[idx] for idx in top_indices]
            cluster_themes.append(', '.join(theme_words))
        
        return df_clustered, cluster_themes
    
    def get_risk_score(self):
        """
        Calcula índice de riesgo basado en proporción de noticias negativas
        
        Returns:
            dict con score y nivel de riesgo
        """
        if self.df is None or len(self.df) == 0:
            return {"score": 0, "level": "Sin datos", "color": "gray"}
        
        total = len(self.df)
        negativas = len(self.df[self.df['sentimiento_ia'] == 'Negativo'])
        
        risk_score = (negativas / total) * 100
        
        if risk_score < 20:
            level = "Bajo"
            color = "green"
        elif risk_score < 40:
            level = "Moderado"
            color = "orange"
        else:
            level = "Alto"
            color = "red"
        
        return {
            "score": round(risk_score, 1),
            "level": level,
            "color": color,
            "negativas": negativas,
            "total": total
        }
    
    def get_opportunities_score(self):
        """
        Calcula índice de oportunidades basado en noticias positivas
        
        Returns:
            dict con score y nivel
        """
        if self.df is None or len(self.df) == 0:
            return {"score": 0, "level": "Sin datos", "color": "gray"}
        
        total = len(self.df)
        positivas = len(self.df[self.df['sentimiento_ia'] == 'Positivo'])
        
        opp_score = (positivas / total) * 100
        
        if opp_score > 40:
            level = "Alto"
            color = "green"
        elif opp_score > 20:
            level = "Moderado"
            color = "orange"
        else:
            level = "Bajo"
            color = "red"
        
        return {
            "score": round(opp_score, 1),
            "level": level,
            "color": color,
            "positivas": positivas,
            "total": total
        }
    
    def generate_executive_summary(self):
        """
        Genera resumen ejecutivo con insights clave
        
        Returns:
            String con resumen
        """
        if self.df is None or len(self.df) == 0:
            return "No hay datos suficientes para generar resumen."
        
        total = len(self.df)
        pos = len(self.df[self.df['sentimiento_ia'] == 'Positivo'])
        neg = len(self.df[self.df['sentimiento_ia'] == 'Negativo'])
        neu = len(self.df[self.df['sentimiento_ia'] == 'Neutro'])
        
        risk = self.get_risk_score()
        opp = self.get_opportunities_score()
        
        # Palabras clave por sentimiento
        keywords_neg = self.extract_keywords('Negativo', top_n=5)
        keywords_pos = self.extract_keywords('Positivo', top_n=5)
        
        summary = f"""
## 📊 Resumen Ejecutivo - Análisis Agroindustrial

### Distribución General
- **Total de noticias analizadas**: {total}
- **Positivas**: {pos} ({pos/total*100:.1f}%)
- **Negativas**: {neg} ({neg/total*100:.1f}%)
- **Neutras**: {neu} ({neu/total*100:.1f}%)

### Índices Clave
- **Índice de Riesgo**: {risk['score']}% - Nivel {risk['level']} :{risk['color']}_circle:
- **Índice de Oportunidades**: {opp['score']}% - Nivel {opp['level']} :{opp['color']}_circle:

### Temas Principales en Noticias Negativas
{', '.join([word for word, freq in keywords_neg[:5]])}

### Temas Principales en Noticias Positivas
{', '.join([word for word, freq in keywords_pos[:5]])}

### Recomendaciones
"""
        
        # Generar recomendaciones basadas en análisis
        if risk['score'] > 40:
            summary += "- ⚠️ **ALERTA**: Alto nivel de riesgo detectado. Revisar noticias negativas prioritariamente.\n"
        
        if opp['score'] > 30:
            summary += "- ✅ Identificadas oportunidades significativas en el sector. Revisar noticias positivas.\n"
        
        if neg > pos:
            summary += "- 🔍 El sentimiento general es negativo. Considerar estrategias de mitigación de riesgos.\n"
        else:
            summary += "- 📈 El sentimiento general es favorable. Momento oportuno para inversiones.\n"
        
        return summary
    
    def predict_sentiment_trend(self):
        """
        Predice tendencia futura del sentimiento (simplificado)
        
        Returns:
            String con predicción
        """
        if self.df is None or 'fecha_parsed' not in self.df.columns:
            return "No hay suficientes datos temporales para predicción."
        
        df_with_dates = self.df[self.df['fecha_parsed'].notna()].copy()
        
        if len(df_with_dates) < 5:
            return "Se necesitan al menos 5 noticias con fecha para predicción."
        
        # Ordenar por fecha
        df_sorted = df_with_dates.sort_values('fecha_parsed')
        
        # Calcular tendencia en últimas vs primeras noticias
        recent_count = len(df_sorted) // 4  # Último 25%
        old_count = len(df_sorted) // 4  # Primer 25%
        
        recent_neg = len(df_sorted.tail(recent_count)[df_sorted.tail(recent_count)['sentimiento_ia'] == 'Negativo'])
        old_neg = len(df_sorted.head(old_count)[df_sorted.head(old_count)['sentimiento_ia'] == 'Negativo'])
        
        recent_neg_pct = (recent_neg / recent_count) * 100 if recent_count > 0 else 0
        old_neg_pct = (old_neg / old_count) * 100 if old_count > 0 else 0
        
        trend_diff = recent_neg_pct - old_neg_pct
        
        if trend_diff > 10:
            prediction = "📉 **TENDENCIA NEGATIVA**: El sentimiento está empeorando. Incremento de noticias negativas."
        elif trend_diff < -10:
            prediction = "📈 **TENDENCIA POSITIVA**: El sentimiento está mejorando. Reducción de noticias negativas."
        else:
            prediction = "➡️ **TENDENCIA ESTABLE**: El sentimiento se mantiene sin cambios significativos."
        
        return prediction

