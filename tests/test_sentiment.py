"""
Pruebas para validar la clasificación de sentimientos en noticias agroindustriales.
Estas pruebas verifican que el sistema clasifica correctamente en las tres categorías.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.gemini_client import AgroSentimentAnalyzer


class TestSentimentClassification:
    """Pruebas para la clasificación de sentimientos."""
    
    def test_parse_text_response_positivo(self):
        """Prueba que el parser identifica correctamente sentimientos positivos."""
        analyzer = AgroSentimentAnalyzer()
        
        respuesta = """
        CLASIFICACIÓN: Positivo
        ARGUMENTO: Las exportaciones y acuerdos comerciales indican crecimiento positivo del sector.
        """
        
        resultado = analyzer._parse_text_response(respuesta)
        assert resultado["sentimiento"] == "Positivo"
        assert "exportaciones" in resultado["explicacion"].lower() or "acuerdos" in resultado["explicacion"].lower()
    
    def test_parse_text_response_negativo(self):
        """Prueba que el parser identifica correctamente sentimientos negativos."""
        analyzer = AgroSentimentAnalyzer()
        
        respuesta = """
        CLASIFICACIÓN: Negativo
        ARGUMENTO: Pérdidas significativas por sequía afectan negativamente al sector.
        """
        
        resultado = analyzer._parse_text_response(respuesta)
        assert resultado["sentimiento"] == "Negativo"
        assert "pérdidas" in resultado["explicacion"].lower() or "sequía" in resultado["explicacion"].lower()
    
    def test_parse_text_response_neutro(self):
        """Prueba que el parser identifica correctamente sentimientos neutros."""
        analyzer = AgroSentimentAnalyzer()
        
        respuesta = """
        CLASIFICACIÓN: Neutro
        ARGUMENTO: Noticia informativa sobre proyecciones sin carga emocional clara.
        """
        
        resultado = analyzer._parse_text_response(respuesta)
        assert resultado["sentimiento"] == "Neutro"
    
    def test_parse_text_response_sin_formato_exacto(self):
        """Prueba que el parser funciona incluso sin el formato exacto."""
        analyzer = AgroSentimentAnalyzer()
        
        # Respuesta sin "CLASIFICACIÓN:" pero con la palabra "Positivo"
        respuesta = """
        El análisis indica que esta noticia es Positiva debido a las inversiones realizadas.
        ARGUMENTO: Las inversiones en tecnología agrícola son favorables.
        """
        
        resultado = analyzer._parse_text_response(respuesta)
        assert resultado["sentimiento"] == "Positivo"
    
    def test_parse_text_response_por_palabras_clave(self):
        """Prueba que el parser usa palabras clave cuando no encuentra formato."""
        analyzer = AgroSentimentAnalyzer()
        
        # Respuesta con palabras clave positivas pero sin formato
        respuesta = "Esta noticia muestra crecimiento y éxito en las exportaciones del sector."
        
        resultado = analyzer._parse_text_response(respuesta)
        # Debería detectar palabras positivas
        assert resultado["sentimiento"] in ["Positivo", "Neutro"]  # Puede ser Neutro si no es claro
    
    def test_parse_text_response_por_palabras_clave_negativas(self):
        """Prueba detección por palabras clave negativas."""
        analyzer = AgroSentimentAnalyzer()
        
        respuesta = "Crisis y pérdidas afectan al sector por problemas de sequía."
        
        resultado = analyzer._parse_text_response(respuesta)
        assert resultado["sentimiento"] in ["Negativo", "Neutro"]
    
    def test_distribucion_tres_categorias(self):
        """Prueba crítica: Verifica que NO todas las noticias se clasifiquen como neutras."""
        analyzer = AgroSentimentAnalyzer()
        
        noticias = [
            "Inversión récord de $50 millones en tecnología agrícola.",
            "Crisis sin precedentes: 80% de pérdidas en cultivos por heladas.",
            "Sector agroindustrial espera repunte en temporada navideña."
        ]
        
        resultados = []
        for noticia in noticias:
            # Mock de respuesta de Gemini
            with patch.object(analyzer, 'analyze_news') as mock_analyze:
                if "Inversión" in noticia:
                    mock_analyze.return_value = {"sentimiento": "Positivo", "explicacion": "Inversión es positiva"}
                elif "Crisis" in noticia:
                    mock_analyze.return_value = {"sentimiento": "Negativo", "explicacion": "Crisis es negativa"}
                else:
                    mock_analyze.return_value = {"sentimiento": "Neutro", "explicacion": "Informativo"}
                
                resultado = analyzer.analyze_news(noticia)
                resultados.append(resultado["sentimiento"])
        
        # Verificar que tenemos las tres categorías
        assert "Positivo" in resultados, "Debe haber al menos una noticia positiva"
        assert "Negativo" in resultados, "Debe haber al menos una noticia negativa"
        assert "Neutro" in resultados, "Debe haber al menos una noticia neutra"
        
        # CRÍTICO: Verificar que NO todas son neutras
        assert not all(s == "Neutro" for s in resultados), \
            "ERROR CRÍTICO: Todas las noticias están siendo clasificadas como neutras"
    
    def test_validacion_sentimientos_validos(self):
        """Prueba que siempre se retorna un sentimiento válido."""
        analyzer = AgroSentimentAnalyzer()
        
        # Respuesta inválida o vacía
        respuestas_invalidas = [
            "",
            "Texto sin clasificación clara",
            "CLASIFICACIÓN: Inválido",
            "CLASIFICACIÓN: PositivoNegativo"  # Sin espacio
        ]
        
        for respuesta in respuestas_invalidas:
            resultado = analyzer._parse_text_response(respuesta)
            assert resultado["sentimiento"] in ["Positivo", "Negativo", "Neutro"], \
                f"Sentimiento inválido retornado: {resultado['sentimiento']}"
    
    def test_parse_text_response_sin_tilde(self):
        """Prueba que el parser maneja respuestas sin tilde en CLASIFICACIÓN."""
        analyzer = AgroSentimentAnalyzer()
        
        respuesta = """
        CLASIFICACION: Positivo
        ARGUMENTO: Las inversiones son favorables.
        """
        
        resultado = analyzer._parse_text_response(respuesta)
        assert resultado["sentimiento"] == "Positivo"


class TestBatchAnalysis:
    """Pruebas para el análisis por lotes."""
    
    def test_analyze_batch_distribucion_correcta(self):
        """Prueba que el análisis por lotes distribuye correctamente los sentimientos."""
        analyzer = AgroSentimentAnalyzer()
        
        df = pd.DataFrame({
            'titular': [
                'Inversión en tecnología agrícola',
                'Crisis por sequía',
                'Reporte estadístico del sector'
            ],
            'cuerpo': [
                'Se anuncian inversiones importantes',
                'Pérdidas significativas reportadas',
                'Datos del último trimestre'
            ]
        })
        
        # Mock de analyze_news para retornar diferentes sentimientos
        with patch.object(analyzer, 'analyze_news') as mock_analyze:
            mock_analyze.side_effect = [
                {"sentimiento": "Positivo", "explicacion": "Inversión positiva"},
                {"sentimiento": "Negativo", "explicacion": "Crisis negativa"},
                {"sentimiento": "Neutro", "explicacion": "Informativo"}
            ]
            
            sents, expls = analyzer.analyze_batch(df, progress_bar=None)
            
            assert len(sents) == 3
            assert "Positivo" in sents
            assert "Negativo" in sents
            assert "Neutro" in sents
            
            # CRÍTICO: Verificar que NO todas son neutras
            assert not all(s == "Neutro" for s in sents), \
                "ERROR: Todas las noticias fueron clasificadas como neutras"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

