# 🚀 Guía de Inicio Rápido - SAVA Agro-Insight PRO

## ⚡ En 5 minutos tendrás todo funcionando

---

## Paso 1: Instalar Dependencias (2 minutos)

Abre una terminal en esta carpeta y ejecuta:

```bash
pip install -r requirements.txt
```

**¿Qué se instalará?**
- Streamlit (interfaz web)
- Gemini AI (análisis de sentimiento)
- Plotly (gráficos)
- Folium (mapas)
- Y más... (ver requirements.txt)

---

## Paso 2: Configurar API Key (1 minuto)

### Obtener tu API Key de Gemini:

1. Ve a: https://makersuite.google.com/app/apikey
2. Inicia sesión con tu cuenta Google
3. Click en "Create API Key"
4. Copia la clave generada

### Configurar en el proyecto:

1. Ve a la carpeta `.streamlit/`
2. Copia el archivo `secrets.toml.example`
3. Renómbralo a `secrets.toml`
4. Abre `secrets.toml` y pega tu API key:

```toml
GEMINI_API_KEY = "tu_api_key_aqui"
```

5. Guarda el archivo

**IMPORTANTE:** El archivo `secrets.toml` NO se subirá a Git (está en .gitignore)

---

## Paso 3: Ejecutar la Aplicación (30 segundos)

En la terminal, ejecuta:

```bash
streamlit run main.py
```

Se abrirá automáticamente en tu navegador: http://localhost:8501

---

## Paso 4: Probar el Sistema (1 minuto)

### Opción A: Analizar CSV

1. Prepara un archivo CSV con columnas:
   - `Titular` o `Headline`
   - `Cuerpo` o `Body`
   - `Fecha` o `Date`

2. En la app, ve a "📂 Análisis CSV"
3. Sube tu archivo
4. **Activa el caché** en el sidebar (importante!)
5. Click en "🧠 Analizar con IA"

### Opción B: Buscar Noticias en Vivo

1. Ve a "🌐 Noticias en Vivo"
2. Escribe: "agroindustria Valle del Cauca"
3. Click en "🚀 Buscar y Analizar"
4. ¡Listo! Verás noticias clasificadas automáticamente

---

## 🎯 ¿Qué hacer después?

### Explora las funcionalidades:

- 🗺️ **Mapa Geográfico**: Visualiza donde ocurren las noticias
- 🤖 **Chatbot IA**: Pregunta sobre las noticias analizadas
- 📈 **Tendencias**: Ve índices de riesgo y oportunidades
- 🔔 **Alertas**: Recibe alertas automáticas de riesgos
- 📄 **Exportar**: Descarga reportes PDF o Excel profesionales

### Optimiza el consumo de API:

1. ✅ **Siempre activa el caché** (en sidebar)
2. ✅ No re-analices el mismo dataset varias veces
3. ✅ Usa "Batch inteligente" para datasets grandes
4. ✅ Limpia el caché cada mes

---

## ❓ Problemas Comunes

### Error: "GEMINI_API_KEY not found"
**Solución**: Verifica que creaste el archivo `.streamlit/secrets.toml` con tu API key

### Error: "No module named 'streamlit'"
**Solución**: Ejecuta `pip install -r requirements.txt`

### La app no abre en el navegador
**Solución**: Abre manualmente http://localhost:8501

### Consume mucha API
**Solución**: Activa el caché en el sidebar

---

## 📚 Documentación Completa

Lee el `README.md` para información detallada sobre:
- Todas las funcionalidades
- Configuración avanzada
- Solución de problemas
- Estructura del proyecto

---

## 💡 Consejos Pro

1. **Primera vez**: Prueba con pocas noticias (5-10) para familiarizarte
2. **Datasets grandes**: Activa "Batch inteligente" (ahorra hasta 80% de API)
3. **Re-análisis**: El caché te permite analizar gratis las mismas noticias
4. **Exportar**: Usa PDF para presentaciones profesionales
5. **Chatbot**: Haz preguntas como "¿Cuáles son los principales riesgos?"

---

## 🎉 ¡Listo!

Tu sistema SAVA Agro-Insight PRO v2.0 está completamente configurado y listo para usar.

**Ahorro esperado**: -70% en consumo de API vs versiones anteriores

---

**¿Dudas? Lee el README.md o revisa el código (está bien documentado)**

Desarrollado con ❤️ por SAVA Software Team

