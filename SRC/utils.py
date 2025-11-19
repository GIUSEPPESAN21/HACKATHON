import pandas as pd
import streamlit as st

def load_and_validate_csv(uploaded_file):
    """
    Carga y valida el CSV de noticias.
    Maneja delimitadores comunes (; o ,) y verifica columnas requeridas.
    """
    try:
        # Intentar detectar delimitador leyendo la primera línea o probando
        # Dado el dataset del usuario, priorizamos ';'
        df = pd.read_csv(uploaded_file, sep=';')
        
        if len(df.columns) < 2:
            # Fallback si no se parseó bien
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=',')

        # Normalización de nombres de columnas (limpieza)
        df.columns = [c.strip() for c in df.columns]
        
        # Mapeo de columnas esperadas (flexibilidad)
        required_columns = {
            'Headline': ['Titular', 'Titular de la Noticia', 'Headline', 'Title'],
            'Body': ['Cuerpo', 'Cuerpo del Texto (resumen)', 'Body', 'Content', 'Resumen'],
            'Date': ['Fecha', 'Fecha Publicación', 'Date']
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
            if not found:
                missing.append(key)

        if missing:
            return None, f"Faltan columnas requeridas: {', '.join(missing)}. Verifique el formato CSV."

        # Renombrar para estandarizar uso interno
        df_clean = df.rename(columns={
            mapped_cols['Headline']: 'titular',
            mapped_cols['Body']: 'cuerpo',
            mapped_cols['Date']: 'fecha'
        })
        
        # Mantener ID si existe, sino crear uno temporal
        if 'ID' in df.columns:
            df_clean['id_original'] = df['ID']
        else:
            df_clean['id_original'] = df.index + 1

        # Limpieza básica de texto
        df_clean['texto_completo'] = df_clean['titular'].fillna('') + ". " + df_clean['cuerpo'].fillna('')
        
        return df_clean, None

    except Exception as e:
        return None, f"Error procesando el archivo: {str(e)}"
