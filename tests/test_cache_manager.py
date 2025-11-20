"""
Tests para el sistema de caché SQLite
"""
import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cache_manager import CacheManager


class TestCacheManager:
    """Pruebas para CacheManager"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.temp_dir, "test_cache.db")
        self.cache = CacheManager(db_path=self.cache_path)
    
    def teardown_method(self):
        """Limpieza después de cada test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cache_set_and_get(self):
        """Prueba guardar y recuperar del caché"""
        text = "Noticia de prueba sobre inversión agrícola"
        sentimiento = "Positivo"
        explicacion = "Inversión positiva en el sector"
        
        # Guardar
        self.cache.set(text, sentimiento, explicacion)
        
        # Recuperar
        result = self.cache.get(text)
        
        assert result is not None
        assert result["sentimiento"] == sentimiento
        assert result["explicacion"] == explicacion
        assert result["from_cache"] is True
    
    def test_cache_miss(self):
        """Prueba que retorna None cuando no hay en caché"""
        result = self.cache.get("Texto que no existe")
        assert result is None
    
    def test_cache_hash_consistency(self):
        """Prueba que el hash es consistente (mismo texto = mismo hash)"""
        text1 = "Noticia de prueba"
        text2 = "Noticia de prueba"  # Mismo texto
        
        self.cache.set(text1, "Positivo", "Test")
        result = self.cache.get(text2)
        
        assert result is not None
        assert result["sentimiento"] == "Positivo"
    
    def test_cache_case_insensitive(self):
        """Prueba que el caché es case-insensitive (normaliza a lowercase)"""
        text1 = "Noticia de Prueba"
        text2 = "noticia de prueba"
        
        self.cache.set(text1, "Positivo", "Test")
        result = self.cache.get(text2)
        
        assert result is not None
    
    def test_cache_hits_counter(self):
        """Prueba que el contador de hits funciona"""
        text = "Noticia de prueba"
        self.cache.set(text, "Positivo", "Test")
        
        # Primera recuperación
        result1 = self.cache.get(text)
        hits1 = result1["cache_hits"]
        
        # Segunda recuperación
        result2 = self.cache.get(text)
        hits2 = result2["cache_hits"]
        
        assert hits2 > hits1
        assert hits2 == hits1 + 1
    
    def test_cache_expiration(self):
        """Prueba que el caché expira después de max_age_days"""
        text = "Noticia antigua"
        self.cache.set(text, "Positivo", "Test")
        
        # Intentar recuperar con max_age muy corto (0 días = expirado)
        result = self.cache.get(text, max_age_days=0)
        
        # Debería retornar None porque está expirado
        assert result is None
    
    def test_cache_stats(self):
        """Prueba las estadísticas del caché"""
        # Agregar varias entradas
        self.cache.set("Noticia 1", "Positivo", "Test 1")
        self.cache.set("Noticia 2", "Negativo", "Test 2")
        self.cache.set("Noticia 3", "Neutro", "Test 3")
        
        # Recuperar algunas para incrementar hits
        self.cache.get("Noticia 1")
        self.cache.get("Noticia 1")
        
        stats = self.cache.get_stats()
        
        assert stats["total_entries"] == 3
        assert stats["total_hits"] >= 5  # 3 sets + 2 gets
        assert "Positivo" in stats["distribution"]
        assert "Negativo" in stats["distribution"]
        assert "Neutro" in stats["distribution"]
    
    def test_clear_old_entries(self):
        """Prueba la limpieza de entradas antiguas"""
        # Agregar entradas
        self.cache.set("Noticia nueva", "Positivo", "Test")
        
        # Limpiar con max_age muy corto (debería eliminar todo)
        deleted = self.cache.clear_old_entries(max_age_days=0)
        
        assert deleted >= 0
        
        # Verificar que se eliminó
        stats = self.cache.get_stats()
        assert stats["total_entries"] == 0
    
    def test_cache_multiple_sentiments(self):
        """Prueba que el caché maneja diferentes sentimientos correctamente"""
        texts = [
            ("Inversión positiva", "Positivo"),
            ("Crisis económica", "Negativo"),
            ("Reporte estadístico", "Neutro")
        ]
        
        for text, sentimiento in texts:
            self.cache.set(text, sentimiento, f"Test {sentimiento}")
        
        # Verificar que cada una se guarda correctamente
        for text, expected_sent in texts:
            result = self.cache.get(text)
            assert result["sentimiento"] == expected_sent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

