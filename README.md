# Clasificador de Sentimiento para Noticias Agroindustriales 🌱

Sistema productivo para analizar y clasificar sentimiento (positivo, negativo, neutro) en noticias agrícolas del Valle del Cauca, Colombia. Utiliza Gemini API para análisis de IA, interfaz Streamlit, y persistencia en Firebase.

## 🚀 Características

- ✅ Clasificación de sentimientos en 3 categorías: Positivo, Negativo, Neutro
- ✅ Análisis de noticias desde CSV o búsqueda web en tiempo real
- ✅ Dashboard interactivo con visualizaciones
- ✅ Integración con Firebase para persistencia de datos
- ✅ Sistema robusto de parsing que evita clasificaciones incorrectas

## 📋 Requisitos

- Python 3.8+
- API Key de Google Gemini
- Credenciales de Firebase (opcional, para persistencia)

## 🔧 Instalación

```bash
# Clonar el repositorio
git clone <tu-repositorio>

# Instalar dependencias
pip install -r requirements.txt
```

## ⚙️ Configuración

1. Crear archivo `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "tu_api_key_aqui"

[firebase_credentials]
service_account_base64 = "tu_credencial_base64_aqui"
```

2. Ejecutar la aplicación:
```bash
streamlit run main.py
```

## 📁 Estructura del Proyecto

```
Codigo/
├── main.py                 # Aplicación principal Streamlit
├── requirements.txt        # Dependencias
├── src/
│   ├── gemini_client.py   # Cliente de Gemini (análisis de sentimientos)
│   ├── utils.py            # Utilidades (carga de CSV)
│   ├── firebase_manager.py # Gestión de Firebase
│   └── __init__.py
├── tests/
│   └── test_sentiment.py   # Pruebas de clasificación
└── docs/                   # Documentación técnica
```

## 🧪 Pruebas

```bash
pytest tests/test_sentiment.py -v
```

## 📚 Documentación

Documentación técnica detallada disponible en la carpeta `docs/`:
- `ANALISIS_Y_CORRECCIONES.md` - Análisis del problema y soluciones
- `RESUMEN_CAMBIOS_COMPLETOS.md` - Resumen de cambios implementados
- `ANALISIS_LIMPIEZA.md` - Análisis de limpieza de archivos

## 🐛 Problemas Conocidos y Soluciones

### Problema: Todas las noticias se clasifican como "Neutro"
**Solución**: Ya corregido en la versión actual. El sistema ahora:
- Usa parsing robusto multi-capa
- No asigna "Neutro" por defecto
- Analiza palabras clave cuando el formato no es estándar

## 📝 Licencia

MIT License - Ver LICENSE para más detalles.

---

## Estructura de Carpetas