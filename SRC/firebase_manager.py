import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json
import base64
from datetime import datetime

# Uso de Singleton para evitar reinicialización en re-runs
@st.cache_resource
def init_firestore():
    """
    Inicializa Firestore decodificando la Service Account desde Base64.
    Soporta tu estructura específica de secrets.toml.
    """
    try:
        # Verificar si ya existe una app inicializada para no reinicializar
        if not firebase_admin._apps:
            
            # Lógica para decodificar Base64 (Tu configuración actual)
            if "firebase_credentials" in st.secrets and "service_account_base64" in st.secrets["firebase_credentials"]:
                # 1. Leer el string Base64
                b64_cred = st.secrets["firebase_credentials"]["service_account_base64"]
                
                # 2. Decodificar a bytes y luego a string JSON
                json_cred = base64.b64decode(b64_cred).decode('utf-8')
                
                # 3. Convertir a diccionario Python
                cred_dict = json.loads(json_cred)
                
                # 4. Autenticar con el diccionario
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            
            # Fallback: Soporte para configuración estándar (por si acaso)
            elif "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            
            else:
                st.error("❌ No se encontraron credenciales de Firebase en secrets.toml")
                return None
        
        # Retornar cliente Firestore
        db = firestore.client()
        return db

    except Exception as e:
        st.error(f"🔥 Error crítico conectando a Firebase: {e}")
        return None

def save_analysis_results(df, collection_name="noticias_agro"):
    """
    Guarda los resultados en Firestore usando Batch writes.
    """
    db = init_firestore()
    if not db:
        return False, "No hay conexión a Base de Datos"

    try:
        batch = db.batch()
        count = 0
        MAX_BATCH_SIZE = 450 
        
        timestamp = datetime.now()

        for _, row in df.iterrows():
            doc_ref = db.collection(collection_name).document()
            
            # Sanitización básica de datos para evitar errores de tipo
            data = {
                "id_original": str(row.get('id_original', 'N/A')),
                "titular": str(row.get('titular', 'Sin Titular')),
                "fecha_noticia": str(row.get('fecha', '')),
                "sentimiento_ia": str(row.get('sentimiento_ia', 'Neutro')),
                "fecha_analisis": timestamp,
                "procesado_por": "SAVA_MVP_BASE64"
            }
            
            batch.set(doc_ref, data)
            count += 1
            
            if count >= MAX_BATCH_SIZE:
                batch.commit()
                batch = db.batch()
                count = 0
        
        if count > 0:
            batch.commit()
            
        return True, f"✅ Se guardaron {len(df)} noticias exitosamente."
    except Exception as e:
        return False, f"❌ Error guardando en Firestore: {e}"

def fetch_history(collection_name="noticias_agro", limit=50):
    db = init_firestore()
    if not db:
        return []
    try:
        docs = db.collection(collection_name)\
                 .order_by("fecha_analisis", direction=firestore.Query.DESCENDING)\
                 .limit(limit)\
                 .stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        st.warning(f"⚠️ Error recuperando historial: {e}")
        return []
