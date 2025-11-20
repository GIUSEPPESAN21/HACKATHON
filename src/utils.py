import pandas as pd
import streamlit as st
from io import StringIO

def load_and_validate_csv(uploaded_file):
    """
    Carga y valida el CSV de noticias forzando el separador correcto
    para el dataset R9.
    Maneja múltiples codificaciones para evitar errores de caracteres.
    """
    # Lista de codificaciones a intentar (en orden de preferencia)
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8-sig']
    
    df = None
    encoding_used = None
    
    try:
        # 1. Intentar leer con diferentes codificaciones y separadores
        # Intentar primero con punto y coma (Estándar del archivo R9)
        for encoding in encodings:
            try:
                uploaded_file.seek(0)  # Reiniciar el archivo
                # Intentar con punto y coma
                df = pd.read_csv(
                    uploaded_file, 
                    sep=';', 
                    dtype=str, 
                    encoding=encoding,
                    engine='python',  # Usar engine python para mejor manejo de errores
                    on_bad_lines='skip' if hasattr(pd, '__version__') and pd.__version__ >= '1.3.0' else 'error'
                )
                # Verificar que se leyeron columnas válidas
                if df is not None and len(df.columns) >= 2:
                    encoding_used = encoding
                    break  # Si funciona, salir del loop
            except (UnicodeDecodeError, UnicodeError) as e:
                continue  # Intentar siguiente codificación
            except Exception:
                # Si es otro error, intentar siguiente codificación
                continue
        
        # Si aún no funcionó, intentar con coma
        if df is None or len(df.columns) < 2:
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(
                        uploaded_file, 
                        sep=',', 
                        dtype=str, 
                        encoding=encoding,
                        engine='python',
                        on_bad_lines='skip' if hasattr(pd, '__version__') and pd.__version__ >= '1.3.0' else 'error'
                    )
                    if df is not None and len(df.columns) >= 2:
                        encoding_used = encoding
                        break
                except (UnicodeDecodeError, UnicodeError):
                    continue
                except Exception:
                    continue
        
        # Si aún no funcionó, último intento leyendo como bytes y decodificando manualmente
        if df is None or len(df.columns) < 2:
            try:
                uploaded_file.seek(0)
                # Leer el archivo como bytes primero
                file_bytes = uploaded_file.read()
                
                # Intentar decodificar con diferentes codificaciones
                for encoding in encodings:
                    try:
                        file_text = file_bytes.decode(encoding, errors='replace')
                        # Convertir a StringIO para leer con pandas
                        df = pd.read_csv(StringIO(file_text), sep=';', dtype=str, engine='python')
                        if df is not None and len(df.columns) >= 2:
                            encoding_used = f"{encoding} (con reemplazo)"
                            break
                    except:
                        continue
                
                # Si aún no funciona con punto y coma, intentar con coma
                if df is None or len(df.columns) < 2:
                    for encoding in encodings:
                        try:
                            file_text = file_bytes.decode(encoding, errors='replace')
                            df = pd.read_csv(StringIO(file_text), sep=',', dtype=str, engine='python')
                            if df is not None and len(df.columns) >= 2:
                                encoding_used = f"{encoding} (con reemplazo)"
                                break
                        except:
                            continue
                            
            except Exception as e:
                return None, f"Error crítico leyendo el archivo: No se pudo leer con ninguna codificación. Detalles: {str(e)}"
        
        if df is None or len(df) == 0:
            return None, "Error: El archivo está vacío o no se pudo leer correctamente."

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
        
        # Log de la codificación usada (opcional, solo para debugging)
        if encoding_used:
            st.caption(f"✅ Archivo leído correctamente (codificación: {encoding_used})")
        
        return df_clean, None

    except Exception as e:
        error_msg = str(e)
        # Mensaje más específico para errores de codificación
        if 'codec' in error_msg or 'decode' in error_msg or 'encoding' in error_msg.lower():
            return None, f"Error de codificación: El archivo tiene caracteres no válidos. Intenta guardar el CSV con codificación UTF-8. Detalles: {error_msg}"
        else:
            return None, f"Error crítico leyendo el archivo: {error_msg}"

