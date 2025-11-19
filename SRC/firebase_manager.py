import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json
from datetime import datetime

# Uso de Singleton para evitar reinicialización en re-runs de Streamlit
@st.cache_resource
def init_firestore():
    """
    Inicializa la conexión a Firestore usando st.secrets.
    Retorna el cliente de DB.
    """
    try:
        # Verificar si ya existe una app inicializada
        if not firebase_admin._apps:
            # Construir diccionario de credenciales desde secrets
            # Streamlit convierte la sección [firebase] de toml a un diccionario
            cred_dict = dict(st.secrets["firebase"])
            
            # Corrección común: las llaves privadas en TOML a veces pierden el formato
            # Aseguramos que los saltos de línea estén correctos
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        return db
    except Exception as e:
        st.error(f"Error conectando a Firebase: {e}")
        return None

def save_analysis_results(df, collection_name="noticias_agro"):
    """
    Guarda los resultados del análisis en Firestore en lote (Batch).
    """
    db = init_firestore()
    if not db:
        return False, "No hay conexión a DB"

    try:
        batch = db.batch()
        count = 0
        MAX_BATCH_SIZE = 450 # Firestore limite es 500
        
        timestamp = datetime.now()

        for _, row in df.iterrows():
            # Crear referencia de documento
            # Usamos un ID compuesto o dejamos que Firestore genere uno
            doc_ref = db.collection(collection_name).document()
            
            data = {
                "id_original": str(row.get('id_original', '')),
                "titular": row.get('titular', ''),
                "fecha_noticia": row.get('fecha', ''),
                "sentimiento_ia": row.get('sentimiento_ia', 'Neutro'),
                "fecha_analisis": timestamp,
                "procesado_por": "SAVA_MVP"
            }
            
            batch.set(doc_ref, data)
            count += 1
            
            # Commit si llegamos al límite del batch
            if count >= MAX_BATCH_SIZE:
                batch.commit()
                batch = db.batch()
                count = 0
        
        # Commit final de los restantes
        if count > 0:
            batch.commit()
            
        return True, "Datos guardados exitosamente"
    except Exception as e:
        return False, f"Error guardando en Firestore: {e}"

def fetch_history(collection_name="noticias_agro", limit=50):
    """
    Recupera historial de análisis.
    """
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
        st.warning(f"No se pudo recuperar el historial: {e}")
        return []
