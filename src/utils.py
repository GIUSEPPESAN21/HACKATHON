import pandas as pd
import streamlit as st

def load_and_validate_csv(uploaded_file):
    """
    Carga y valida el CSV de noticias forzando el separador correcto
    para el dataset R9.
    """
    try:
        # 1. Forzamos separador de punto y coma (Estándar del archivo R9)
        # Usamos 'dtype=str' para leer todo como texto al principio y evitar errores de conversión
        df = pd.read_csv(uploaded_file, sep=';', dtype=str)
        
        # Si falló y solo leyó 1 columna, intentamos con coma
        if len(df.columns) < 2:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=',', dtype=str)

        # 2. Limpieza de nombres de columnas (eliminar espacios extra)
        df.columns = [c.strip() for c in df.columns]
        
        # 3. Mapeo inteligente de columnas
        required_columns = {
            'Headline': ['Titular', 'Titular de la Noticia', 'Headline', 'Title'],
            'Body': ['Cuerpo', 'Cuerpo del Texto (resumen)', 'Body', 'Content', 'Resumen'],
            'Date': ['Fecha', 'Fecha Publicación', 'Date', 'Fecha Publicacion'],
            'ID': ['ID', 'id', 'Id']
        }
        
        mapped_cols = {}
        missing = []

        for key, possibilities in required_columns.items():
            found = False
            for p in possibilities:
                if p in df.columns:
                    mapped_cols[key] = p
                    found = True
                    break
            if not found and key != 'ID': # El ID es opcional, lo podemos generar
                missing.append(key)

        if missing:
            return None, f"❌ Faltan columnas: {', '.join(missing)}. Revisa que el CSV use punto y coma (;)."

        # 4. Crear DataFrame limpio
        df_clean = pd.DataFrame()
        
        # Manejo del ID: Si existe, úsalo. Si no, usa el índice + 1.
        if 'ID' in mapped_cols:
            df_clean['id_original'] = df[mapped_cols['ID']].astype(str)
        else:
            df_clean['id_original'] = (df.index + 1).astype(str)

        df_clean['titular'] = df[mapped_cols['Headline']].fillna('Sin Titular')
        df_clean['cuerpo'] = df[mapped_cols['Body']].fillna('')
        df_clean['fecha'] = df[mapped_cols['Date']].fillna('')

        # Crear texto completo para la IA
        df_clean['texto_completo'] = df_clean['titular'] + ". " + df_clean['cuerpo']
        
        return df_clean, None

    except Exception as e:
        return None, f"Error crítico leyendo el archivo: {str(e)}"

