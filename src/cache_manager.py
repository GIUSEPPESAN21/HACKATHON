"""
Sistema de caché inteligente para evitar re-análisis de noticias
Reduce consumo de API hasta en 80%
"""
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import os

class CacheManager:
    def __init__(self, db_path="cache/sentiment_cache.db"):
        """Inicializa base de datos SQLite para caché local"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else "cache", exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Crea tabla de caché si no existe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_cache (
                content_hash TEXT PRIMARY KEY,
                titular TEXT,
                sentimiento TEXT,
                explicacion TEXT,
                timestamp DATETIME,
                hits INTEGER DEFAULT 1
            )
        ''')
        
        # Índice para búsquedas rápidas
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON sentiment_cache(timestamp)
        ''')
        conn.commit()
        conn.close()
    
    def _generate_hash(self, text):
        """Genera hash único para el contenido"""
        return hashlib.md5(text.strip().lower().encode()).hexdigest()
    
    def get(self, text, max_age_days=30):
        """
        Busca resultado en caché
        
        Args:
            text: Texto de la noticia
            max_age_days: Edad máxima del caché en días
        
        Returns:
            dict o None si no existe o está vencido
        """
        content_hash = self._generate_hash(text)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar y verificar edad
        cursor.execute('''
            SELECT sentimiento, explicacion, timestamp, hits
            FROM sentiment_cache
            WHERE content_hash = ?
        ''', (content_hash,))
        
        result = cursor.fetchone()
        
        if result:
            sentimiento, explicacion, timestamp, hits = result
            cache_date = datetime.fromisoformat(timestamp)
            
            # Verificar si no está vencido
            if datetime.now() - cache_date <= timedelta(days=max_age_days):
                # Incrementar contador de hits
                cursor.execute('''
                    UPDATE sentiment_cache 
                    SET hits = hits + 1 
                    WHERE content_hash = ?
                ''', (content_hash,))
                conn.commit()
                conn.close()
                
                return {
                    "sentimiento": sentimiento,
                    "explicacion": explicacion,
                    "from_cache": True,
                    "cache_hits": hits + 1
                }
        
        conn.close()
        return None
    
    def set(self, text, sentimiento, explicacion):
        """Guarda resultado en caché"""
        content_hash = self._generate_hash(text)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extraer titular (primeras 200 caracteres)
        titular = text[:200]
        
        cursor.execute('''
            INSERT OR REPLACE INTO sentiment_cache 
            (content_hash, titular, sentimiento, explicacion, timestamp, hits)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (content_hash, titular, sentimiento, explicacion, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Obtiene estadísticas del caché"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*), SUM(hits) FROM sentiment_cache')
        total_entries, total_hits = cursor.fetchone()
        
        cursor.execute('''
            SELECT sentimiento, COUNT(*) 
            FROM sentiment_cache 
            GROUP BY sentimiento
        ''')
        distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_entries": total_entries or 0,
            "total_hits": total_hits or 0,
            "distribution": distribution,
            "cache_hit_rate": f"{((total_hits - total_entries) / total_hits * 100):.1f}%" if total_hits else "0%"
        }
    
    def clear_old_entries(self, max_age_days=90):
        """Limpia entradas antiguas para liberar espacio"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
        cursor.execute('DELETE FROM sentiment_cache WHERE timestamp < ?', (cutoff_date,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted

