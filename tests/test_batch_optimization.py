"""
Tests para la optimización de análisis batch (un solo llamado por sesión)
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.gemini_client import AgroSentimentAnalyzer


class TestBatchOptimization:
    """Pruebas para la optimización de análisis batch"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        # Mock de streamlit secrets
        with patch('streamlit.secrets') as mock_secrets:
            mock_secrets.get.return_value = "test_api_key"
            self.analyzer = AgroSentimentAnalyzer()
    
    def test_analyze_batch_single_api_call(self):
        """Prueba que analyze_batch hace UN SOLO llamado API para todas las noticias nuevas"""
        df = pd.DataFrame({
            'titular': [
                'Inversión agrícola',
                'Crisis por sequía',
                'Reporte estadístico'
            ],
            'cuerpo': [
                'Se anuncian inversiones importantes',
                'Pérdidas significativas reportadas',
                'Datos del último trimestre'
            ]
        })
        
        # Mock del método _analyze_session_batch para verificar que se llama UNA vez
        with patch.object(self.analyzer, '_analyze_session_batch') as mock_batch:
            mock_batch.return_value = [
                {"sentimiento": "Positivo", "explicacion": "Test 1"},
                {"sentimiento": "Negativo", "explicacion": "Test 2"},
                {"sentimiento": "Neutro", "explicacion": "Test 3"}
            ]
            
            # Mock del caché para que todas sean nuevas
            with patch.object(self.analyzer.cache, 'get', return_value=None):
                with patch.object(self.analyzer.cache, 'set'):
                    sents, expls = self.analyzer.analyze_batch(df, progress_bar=None)
            
            # Verificar que se llamó UNA SOLA VEZ
            assert mock_batch.call_count == 1
            assert len(sents) == 3
            assert len(expls) == 3
    
    def test_analyze_batch_all_cached(self):
        """Prueba que si todas están en caché, NO se hace ningún llamado API"""
        df = pd.DataFrame({
            'titular': ['Test 1', 'Test 2'],
            'cuerpo': ['Cuerpo 1', 'Cuerpo 2']
        })
        
        # Mock del caché para que todas estén en caché
        cached_result = {
            "sentimiento": "Positivo",
            "explicacion": "Del caché",
            "from_cache": True,
            "cache_hits": 1
        }
        
        with patch.object(self.analyzer.cache, 'get', return_value=cached_result):
            with patch.object(self.analyzer, '_analyze_session_batch') as mock_batch:
                sents, expls = self.analyzer.analyze_batch(df, progress_bar=None)
                
                # Verificar que NO se llamó a la API
                assert mock_batch.call_count == 0
                assert len(sents) == 2
                assert all(s == "Positivo" for s in sents)
    
    def test_analyze_batch_mixed_cache(self):
        """Prueba que maneja correctamente mezcla de caché y nuevas"""
        df = pd.DataFrame({
            'titular': ['Cached 1', 'New 1', 'Cached 2'],
            'cuerpo': ['Body 1', 'Body 2', 'Body 3']
        })
        
        cached_result = {
            "sentimiento": "Positivo",
            "explicacion": "Del caché",
            "from_cache": True,
            "cache_hits": 1
        }
        
        call_count = 0
        def cache_get_side_effect(text):
            # Primera y tercera están en caché, segunda no
            if 'Cached' in text:
                return cached_result
            return None
        
        with patch.object(self.analyzer.cache, 'get', side_effect=cache_get_side_effect):
            with patch.object(self.analyzer.cache, 'set'):
                with patch.object(self.analyzer, '_analyze_session_batch') as mock_batch:
                    mock_batch.return_value = [
                        {"sentimiento": "Negativo", "explicacion": "Nueva"}
                    ]
                    
                    sents, expls = self.analyzer.analyze_batch(df, progress_bar=None)
                    
                    # Debe hacer UN SOLO llamado con solo la noticia nueva
                    assert mock_batch.call_count == 1
                    # Verificar que se pasó solo 1 noticia nueva
                    call_args = mock_batch.call_args[0][0]
                    assert len(call_args) == 1
                    
                    # Verificar resultados finales
                    assert len(sents) == 3
                    assert sents[0] == "Positivo"  # Del caché
                    assert sents[1] == "Negativo"   # Nueva
                    assert sents[2] == "Positivo"    # Del caché
    
    def test_parse_batch_response_format_standard(self):
        """Prueba parsing de respuesta batch con formato estándar"""
        response = """1|Positivo|Inversión positiva en el sector
2|Negativo|Crisis por sequía
3|Neutro|Reporte informativo"""
        
        results = self.analyzer._parse_batch_response(response, 3)
        
        assert len(results) == 3
        assert results[0]["sentimiento"] == "Positivo"
        assert results[1]["sentimiento"] == "Negativo"
        assert results[2]["sentimiento"] == "Neutro"
    
    def test_parse_batch_response_format_alternative(self):
        """Prueba parsing con formato alternativo"""
        response = """NOTICIA 1|Positivo|Inversión
NOTICIA 2|Negativo|Crisis"""
        
        results = self.analyzer._parse_batch_response(response, 2)
        
        assert len(results) == 2
        assert results[0]["sentimiento"] == "Positivo"
        assert results[1]["sentimiento"] == "Negativo"
    
    def test_parse_batch_response_incomplete(self):
        """Prueba que rellena resultados faltantes con Neutro"""
        response = """1|Positivo|Test 1
2|Negativo|Test 2"""
        # Solo 2 resultados pero esperamos 5
        
        results = self.analyzer._parse_batch_response(response, 5)
        
        assert len(results) == 5
        assert results[0]["sentimiento"] == "Positivo"
        assert results[1]["sentimiento"] == "Negativo"
        # Los demás deben ser Neutro
        assert all(r["sentimiento"] == "Neutro" for r in results[2:])
    
    def test_parse_batch_response_normalizes_sentiment(self):
        """Prueba que normaliza sentimientos correctamente"""
        response = """1|positivo|Test
2|NEGATIVO|Test
3|neutro|Test
4|Positivo|Test"""
        
        results = self.analyzer._parse_batch_response(response, 4)
        
        assert results[0]["sentimiento"] == "Positivo"
        assert results[1]["sentimiento"] == "Negativo"
        assert results[2]["sentimiento"] == "Neutro"
        assert results[3]["sentimiento"] == "Positivo"
    
    def test_analyze_session_batch_handles_large_batch(self):
        """Prueba que maneja lotes grandes correctamente"""
        # Crear 50 noticias de prueba
        texts = [f"Noticia de prueba número {i}" for i in range(50)]
        
        # Mock de la respuesta de Gemini
        mock_response = MagicMock()
        mock_response.text = "\n".join([
            f"{i+1}|Positivo|Test {i+1}" for i in range(50)
        ])
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            # Mock de API key
            self.analyzer.api_key = "test_key"
            
            results = self.analyzer._analyze_session_batch(texts)
            
            assert len(results) == 50
            assert all(r["sentimiento"] in ["Positivo", "Negativo", "Neutro"] for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

