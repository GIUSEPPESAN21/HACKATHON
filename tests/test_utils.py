"""
Tests para funciones utilitarias
"""
import pytest
import pandas as pd
import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import load_and_validate_csv


class TestUtils:
    """Pruebas para funciones utilitarias"""
    
    def test_load_csv_with_semicolon(self):
        """Prueba carga de CSV con separador punto y coma"""
        csv_content = """Titular;Cuerpo;Fecha;ID
Inversión agrícola;Se anuncian inversiones;2024-01-01;1
Crisis por sequía;Pérdidas significativas;2024-01-02;2"""
        
        csv_file = io.StringIO(csv_content)
        df, error = load_and_validate_csv(csv_file)
        
        assert error is None
        assert df is not None
        assert len(df) == 2
        assert 'titular' in df.columns
        assert 'cuerpo' in df.columns
        assert 'fecha' in df.columns
    
    def test_load_csv_with_comma(self):
        """Prueba carga de CSV con separador coma (fallback)"""
        csv_content = """Titular,Cuerpo,Fecha,ID
Inversión agrícola,Se anuncian inversiones,2024-01-01,1
Crisis por sequía,Pérdidas significativas,2024-01-02,2"""
        
        csv_file = io.StringIO(csv_content)
        df, error = load_and_validate_csv(csv_file)
        
        assert error is None
        assert df is not None
        assert len(df) == 2
    
    def test_load_csv_missing_columns(self):
        """Prueba que detecta columnas faltantes"""
        csv_content = """Titular;Cuerpo
Inversión agrícola;Se anuncian inversiones"""
        
        csv_file = io.StringIO(csv_content)
        df, error = load_and_validate_csv(csv_file)
        
        assert error is not None
        assert "Faltan columnas" in error
    
    def test_load_csv_column_mapping(self):
        """Prueba el mapeo inteligente de columnas"""
        # CSV con nombres alternativos
        csv_content = """Headline;Body;Date;ID
Inversión agrícola;Se anuncian inversiones;2024-01-01;1
Crisis por sequía;Pérdidas significativas;2024-01-02;2"""
        
        csv_file = io.StringIO(csv_content)
        df, error = load_and_validate_csv(csv_file)
        
        assert error is None
        assert 'titular' in df.columns
        assert 'cuerpo' in df.columns
        assert 'fecha' in df.columns
    
    def test_load_csv_generates_id(self):
        """Prueba que genera ID si no existe"""
        csv_content = """Titular;Cuerpo;Fecha
Inversión agrícola;Se anuncian inversiones;2024-01-01
Crisis por sequía;Pérdidas significativas;2024-01-02"""
        
        csv_file = io.StringIO(csv_content)
        df, error = load_and_validate_csv(csv_file)
        
        assert error is None
        assert 'id_original' in df.columns
        assert len(df['id_original'].unique()) == 2
    
    def test_load_csv_handles_missing_values(self):
        """Prueba que maneja valores faltantes correctamente"""
        csv_content = """Titular;Cuerpo;Fecha;ID
Inversión agrícola;;2024-01-01;1
;Pérdidas significativas;2024-01-02;2"""
        
        csv_file = io.StringIO(csv_content)
        df, error = load_and_validate_csv(csv_file)
        
        assert error is None
        assert df['cuerpo'].iloc[0] == '' or pd.isna(df['cuerpo'].iloc[0])
        assert df['titular'].iloc[1] == 'Sin Titular' or pd.isna(df['titular'].iloc[1])
    
    def test_load_csv_creates_texto_completo(self):
        """Prueba que crea la columna texto_completo"""
        csv_content = """Titular;Cuerpo;Fecha;ID
Inversión agrícola;Se anuncian inversiones;2024-01-01;1"""
        
        csv_file = io.StringIO(csv_content)
        df, error = load_and_validate_csv(csv_file)
        
        assert error is None
        assert 'texto_completo' in df.columns
        assert 'Inversión agrícola' in df['texto_completo'].iloc[0]
        assert 'Se anuncian inversiones' in df['texto_completo'].iloc[0]
    
    def test_load_csv_strips_column_names(self):
        """Prueba que elimina espacios extra en nombres de columnas"""
        csv_content = """ Titular ; Cuerpo ; Fecha ; ID 
Inversión agrícola;Se anuncian inversiones;2024-01-01;1"""
        
        csv_file = io.StringIO(csv_content)
        df, error = load_and_validate_csv(csv_file)
        
        assert error is None
        # Los nombres de columnas deben estar limpios
        assert all(not col.startswith(' ') and not col.endswith(' ') for col in df.columns)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

