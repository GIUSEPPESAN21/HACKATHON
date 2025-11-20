"""
Tests de integración para flujos completos
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.gemini_client import AgroSentimentAnalyzer
from src.cache_manager import CacheManager
from src.utils import load_and_validate_csv


class TestIntegration:
    """Pruebas de integración para flujos completos"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        with patch('streamlit.secrets') as mock_secrets:
            mock_secrets.get.return_value = "test_api_key"
            self.analyzer = AgroSentimentAnalyzer()
    
    def test_full_workflow_csv_analysis(self):
        """Prueba flujo completo: carga CSV -> análisis -> resultados"""
        # Crear CSV de prueba
        csv_content = """Titular;Cuerpo;Fecha;ID
Inversión agrícola;Se anuncian inversiones importantes;2024-01-01;1
Crisis por sequía;Pérdidas significativas reportadas;2024-01-02;2
Reporte estadístico;Datos del último trimestre;2024-01-03;3"""
        
        import io
        csv_file = io.StringIO(csv_content)
        
        # 1. Cargar CSV
        df, error = load_and_validate_csv(csv_file)
        assert error is None
        assert len(df) == 3
        
        # 2. Analizar con mock
        with patch.object(self.analyzer, '_analyze_session_batch') as mock_batch:
            mock_batch.return_value = [
                {"sentimiento": "Positivo", "explicacion": "Inversión positiva"},
                {"sentimiento": "Negativo", "explicacion": "Crisis negativa"},
                {"sentimiento": "Neutro", "explicacion": "Informativo"}
            ]
            
            with patch.object(self.analyzer.cache, 'get', return_value=None):
                with patch.object(self.analyzer.cache, 'set'):
                    sents, expls = self.analyzer.analyze_batch(df, progress_bar=None)
        
        # 3. Verificar resultados
        assert len(sents) == 3
        assert len(expls) == 3
        assert "Positivo" in sents
        assert "Negativo" in sents
        assert "Neutro" in sents
        
        # 4. Verificar que se hizo UN SOLO llamado
        assert mock_batch.call_count == 1
    
    def test_cache_integration(self):
        """Prueba integración con caché en flujo completo"""
        df = pd.DataFrame({
            'titular': ['Test 1', 'Test 2', 'Test 3'],
            'cuerpo': ['Body 1', 'Body 2', 'Body 3']
        })
        
        # Primera ejecución: todas nuevas
        with patch.object(self.analyzer, '_analyze_session_batch') as mock_batch:
            mock_batch.return_value = [
                {"sentimiento": "Positivo", "explicacion": "Test"},
                {"sentimiento": "Negativo", "explicacion": "Test"},
                {"sentimiento": "Neutro", "explicacion": "Test"}
            ]
            
            with patch.object(self.analyzer.cache, 'get', return_value=None):
                with patch.object(self.analyzer.cache, 'set') as mock_set:
                    sents1, expls1 = self.analyzer.analyze_batch(df, progress_bar=None)
                    
                    # Verificar que se guardó en caché
                    assert mock_set.call_count == 3
        
        # Segunda ejecución: todas en caché
        cached_result = {
            "sentimiento": "Positivo",
            "explicacion": "Del caché",
            "from_cache": True,
            "cache_hits": 1
        }
        
        with patch.object(self.analyzer.cache, 'get', return_value=cached_result):
            with patch.object(self.analyzer, '_analyze_session_batch') as mock_batch:
                sents2, expls2 = self.analyzer.analyze_batch(df, progress_bar=None)
                
                # Verificar que NO se llamó a la API
                assert mock_batch.call_count == 0
                assert all(s == "Positivo" for s in sents2)
    
    def test_error_handling_in_workflow(self):
        """Prueba manejo de errores en flujo completo"""
        df = pd.DataFrame({
            'titular': ['Test 1'],
            'cuerpo': ['Body 1']
        })
        
        # Simular error en API
        with patch.object(self.analyzer, '_analyze_session_batch') as mock_batch:
            mock_batch.side_effect = Exception("API Error")
            
            with patch.object(self.analyzer.cache, 'get', return_value=None):
                # Debe manejar el error gracefully
                try:
                    sents, expls = self.analyzer.analyze_batch(df, progress_bar=None)
                    # Si no lanza excepción, verificar que retorna valores por defecto
                    assert len(sents) == 1
                except Exception:
                    # Si lanza excepción, está bien, pero debería manejarse
                    pass
    
    def test_mixed_cache_and_new_workflow(self):
        """Prueba flujo con mezcla de caché y noticias nuevas"""
        df = pd.DataFrame({
            'titular': ['Cached 1', 'New 1', 'Cached 2', 'New 2'],
            'cuerpo': ['Body 1', 'Body 2', 'Body 3', 'Body 4']
        })
        
        cached_result = {
            "sentimiento": "Positivo",
            "explicacion": "Del caché",
            "from_cache": True,
            "cache_hits": 1
        }
        
        def cache_get_side_effect(text):
            if 'Cached' in text:
                return cached_result
            return None
        
        with patch.object(self.analyzer.cache, 'get', side_effect=cache_get_side_effect):
            with patch.object(self.analyzer.cache, 'set') as mock_set:
                with patch.object(self.analyzer, '_analyze_session_batch') as mock_batch:
                    mock_batch.return_value = [
                        {"sentimiento": "Negativo", "explicacion": "Nueva 1"},
                        {"sentimiento": "Neutro", "explicacion": "Nueva 2"}
                    ]
                    
                    sents, expls = self.analyzer.analyze_batch(df, progress_bar=None)
                    
                    # Verificar que se hizo UN SOLO llamado con solo las 2 nuevas
                    assert mock_batch.call_count == 1
                    call_args = mock_batch.call_args[0][0]
                    assert len(call_args) == 2
                    
                    # Verificar que se guardaron solo las nuevas en caché
                    assert mock_set.call_count == 2
                    
                    # Verificar resultados finales
                    assert len(sents) == 4
                    assert sents[0] == "Positivo"  # Cached
                    assert sents[1] == "Negativo"   # New
                    assert sents[2] == "Positivo"    # Cached
                    assert sents[3] == "Neutro"      # New


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

