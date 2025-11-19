import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json
import base64
from datetime import datetime

# Singleton: Solo conecta una vez
@st.cache_resource
def init_firestore():
    try:
        # Si ya está conectado, retornar cliente existente
        if firebase_admin._apps:
            return firestore.client()

        # Lógica de credenciales
        if "firebase_credentials" in st.secrets and "service_account_base64" in st.secrets["firebase_credentials"]:
            # Decodificar Base64
            b64_cred = st.secrets["firebase_credentials"]["service_account_base64"]
            json_str = base64.b64decode(b64_cred).decode('utf-8')
            cred_dict = json.loads(json_str)
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
            
        elif "firebase" in st.secrets:
            # Soporte legacy
            cred_dict = dict(st.secrets["firebase"])
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
            
        else:
            print("❌ No se encontraron secretos de Firebase.")
            return None

    except Exception as e:
        print(f"🔥 Error inicializando Firebase: {e}")
        return None

def save_analysis_results(df, collection_name="noticias_agro"):
    """
    Guarda resultados con manejo de errores explícito.
    """
    db = init_firestore()
    if not db:
        return False, "Error de conexión: No se pudo conectar a Firestore."

    try:
        batch = db.batch()
        count = 0
        MAX_BATCH_SIZE = 400 # Margen de seguridad
        
        timestamp = datetime.now()
        
        total_saved = 0

        for index, row in df.iterrows():
            # Usar id_original como ID del documento para evitar duplicados en BD
            doc_id = str(row.get('id_original', f'auto_{index}'))
            doc_ref = db.collection(collection_name).document(doc_id)
            
            data = {
                "id": doc_id,
                "titular": str(row.get('titular', 'Sin Titular')),
                "fecha_publicacion": str(row.get('fecha', '')),
                "sentimiento": str(row.get('sentimiento_ia', 'Neutro')),
                "texto_completo": str(row.get('texto_completo', ''))[:500], # Truncar para ahorrar espacio
                "fecha_analisis": timestamp,
                "status": "procesado"
            }
            
            batch.set(doc_ref, data)
            count += 1
            total_saved += 1
            
            if count >= MAX_BATCH_SIZE:
                batch.commit()
                batch = db.batch()
                count = 0
        
        if count > 0:
            batch.commit()
            
        return True, f"✅ Se guardaron {total_saved} registros correctamente en la colección '{collection_name}'."
        
    except Exception as e:
        return False, f"❌ Error guardando datos: {str(e)}"

def fetch_history(collection_name="noticias_agro", limit=50):
    db = init_firestore()
    if not db: return []
    try:
        docs = db.collection(collection_name)\
                 .order_by("fecha_analisis", direction=firestore.Query.DESCENDING)\
                 .limit(limit)\
                 .stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        return []
