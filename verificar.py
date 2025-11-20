#!/usr/bin/env python3
"""
Script de verificación rápida para SAVA Agro-Insight
Verifica que todo esté en orden antes del deploy
"""
import os
import sys
from pathlib import Path

def print_status(check, message):
    """Imprime estado con emoji"""
    if check:
        print(f"✅ {message}")
        return True
    else:
        print(f"❌ {message}")
        return False

def verificar_estructura():
    """Verifica estructura de archivos"""
    print("\n📁 Verificando estructura de archivos...\n")
    
    archivos_requeridos = [
        "main.py",
        "requirements.txt",
        "README.md",
        ".gitignore",
        "src/__init__.py",
        "src/gemini_client.py",
        "src/cache_manager.py",
        "src/utils.py",
        "src/firebase_manager.py",
        "src/geo_mapper.py",
        "src/chatbot_rag.py",
        "src/trend_analyzer.py",
        "src/alert_system.py",
        "src/export_manager.py"
    ]
    
    todos_ok = True
    for archivo in archivos_requeridos:
        existe = os.path.exists(archivo)
        todos_ok = print_status(existe, f"{archivo}") and todos_ok
    
    return todos_ok

def verificar_imports():
    """Verifica que los imports principales funcionen"""
    print("\n🔍 Verificando imports principales...\n")
    
    imports_ok = True
    
    try:
        import streamlit
        print_status(True, "streamlit importado")
    except ImportError as e:
        print_status(False, f"streamlit - {e}")
        imports_ok = False
    
    try:
        import pandas
        print_status(True, "pandas importado")
    except ImportError as e:
        print_status(False, f"pandas - {e}")
        imports_ok = False
    
    try:
        import google.generativeai
        print_status(True, "google-generativeai importado")
    except ImportError as e:
        print_status(False, f"google-generativeai - {e}")
        imports_ok = False
    
    try:
        import folium
        print_status(True, "folium importado")
    except ImportError as e:
        print_status(False, f"folium - {e}")
        imports_ok = False
    
    try:
        from src.cache_manager import CacheManager
        print_status(True, "CacheManager importado")
    except ImportError as e:
        print_status(False, f"CacheManager - {e}")
        imports_ok = False
    
    try:
        from src.gemini_client import AgroSentimentAnalyzer
        print_status(True, "AgroSentimentAnalyzer importado")
    except ImportError as e:
        print_status(False, f"AgroSentimentAnalyzer - {e}")
        imports_ok = False
    
    return imports_ok

def verificar_secrets():
    """Verifica configuración de secrets"""
    print("\n🔐 Verificando configuración...\n")
    
    secrets_example = os.path.exists(".streamlit/secrets.toml.example")
    print_status(secrets_example, "Archivo de ejemplo de secrets existe")
    
    secrets_real = os.path.exists(".streamlit/secrets.toml")
    if secrets_real:
        print_status(True, "secrets.toml configurado")
    else:
        print_status(False, "secrets.toml NO encontrado (debes crearlo)")
    
    return secrets_example

def verificar_correcciones():
    """Verifica que las correcciones estén aplicadas"""
    print("\n🔧 Verificando correcciones aplicadas...\n")
    
    correcciones_ok = True
    
    # Verificar que no hay analyze_batch_smart en main.py
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "analyze_batch_smart" in content:
            print_status(False, "main.py: analyze_batch_smart todavía presente")
            correcciones_ok = False
        else:
            print_status(True, "main.py: No hay analyze_batch_smart")
    
    # Verificar que no hay use_container_width
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "use_container_width" in content:
            print_status(False, "main.py: use_container_width todavía presente")
            correcciones_ok = False
        else:
            print_status(True, "main.py: No hay use_container_width")
    
    # Verificar que no hay folium_static
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "folium_static" in content:
            print_status(False, "main.py: folium_static todavía presente")
            correcciones_ok = False
        else:
            print_status(True, "main.py: No hay folium_static")
    
    # Verificar que geo_mapper no tiene Stamen Terrain
    with open("src/geo_mapper.py", "r", encoding="utf-8") as f:
        content = f.read()
        if "Stamen Terrain" in content and "OpenTopoMap" not in content:
            print_status(False, "geo_mapper.py: Stamen Terrain sin corrección")
            correcciones_ok = False
        else:
            print_status(True, "geo_mapper.py: TileLayer corregido")
    
    return correcciones_ok

def main():
    """Función principal"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║       🌱 SAVA Agro-Insight PRO v2.0                     ║
║       Script de Verificación                            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Verificaciones
    estructura_ok = verificar_estructura()
    imports_ok = verificar_imports()
    secrets_ok = verificar_secrets()
    correcciones_ok = verificar_correcciones()
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("="*60 + "\n")
    
    print_status(estructura_ok, "Estructura de archivos")
    print_status(imports_ok, "Imports y dependencias")
    print_status(secrets_ok, "Configuración")
    print_status(correcciones_ok, "Correcciones aplicadas")
    
    print("\n" + "="*60 + "\n")
    
    if estructura_ok and imports_ok and correcciones_ok:
        print("🎉 ¡TODO VERIFICADO CORRECTAMENTE!")
        print("\n✅ El proyecto está listo para:")
        print("   • Ejecutar localmente (streamlit run main.py)")
        print("   • Deploy en Streamlit Cloud")
        print("   • Uso en producción")
        
        if not os.path.exists(".streamlit/secrets.toml"):
            print("\n⚠️  IMPORTANTE: Crea .streamlit/secrets.toml con tu API key")
        
        return 0
    else:
        print("❌ HAY PROBLEMAS QUE CORREGIR")
        print("\n🔧 Revisa los errores arriba y corrígelos.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificación cancelada")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        sys.exit(1)

