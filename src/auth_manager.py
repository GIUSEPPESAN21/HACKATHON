"""
Sistema de autenticación y registro de usuarios
Usa Firebase Firestore para almacenar usuarios
"""
import firebase_admin
from firebase_admin import firestore
import streamlit as st
import hashlib
from datetime import datetime
from src.firebase_manager import init_firestore

def hash_password(password):
    """Genera hash SHA-256 de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    """
    Registra un nuevo usuario en Firebase
    
    Args:
        username: Nombre de usuario único
        email: Email del usuario
        password: Contraseña en texto plano (se hashea)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    db = init_firestore()
    if not db:
        return False, "❌ Error de conexión con Firebase"
    
    try:
        users_ref = db.collection('users')
        
        # Verificar si el usuario ya existe
        existing_user = users_ref.where('username', '==', username).limit(1).get()
        if existing_user:
            return False, "❌ El nombre de usuario ya está en uso"
        
        # Verificar si el email ya existe
        existing_email = users_ref.where('email', '==', email).limit(1).get()
        if existing_email:
            return False, "❌ El email ya está registrado"
        
        # Validar contraseña
        if len(password) < 6:
            return False, "❌ La contraseña debe tener al menos 6 caracteres"
        
        # Crear nuevo usuario
        hashed_password = hash_password(password)
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now(),
            'last_login': None,
            'role': 'user'  # Por defecto, rol de usuario
        }
        
        # Guardar en Firestore
        users_ref.add(user_data)
        
        return True, "✅ Usuario registrado exitosamente"
        
    except Exception as e:
        return False, f"❌ Error al registrar usuario: {str(e)}"

def authenticate_user(username, password):
    """
    Autentica un usuario
    
    Args:
        username: Nombre de usuario o email
        password: Contraseña en texto plano
    
    Returns:
        tuple: (success: bool, user_data: dict or None, message: str)
    """
    db = init_firestore()
    if not db:
        return False, None, "❌ Error de conexión con Firebase"
    
    try:
        users_ref = db.collection('users')
        
        # Buscar por username
        users = users_ref.where('username', '==', username).limit(1).get()
        
        # Si no encuentra por username, buscar por email
        if not users:
            users = users_ref.where('email', '==', username).limit(1).get()
        
        if not users:
            return False, None, "❌ Usuario o contraseña incorrectos"
        
        # Obtener el primer usuario (debe ser único)
        user_doc = users[0]
        user_data = user_doc.to_dict()
        
        # Verificar contraseña
        hashed_password = hash_password(password)
        if user_data['password'] != hashed_password:
            return False, None, "❌ Usuario o contraseña incorrectos"
        
        # Actualizar último login
        user_doc.reference.update({
            'last_login': datetime.now()
        })
        
        # Preparar datos del usuario (sin la contraseña)
        user_info = {
            'id': user_doc.id,
            'username': user_data['username'],
            'email': user_data['email'],
            'role': user_data.get('role', 'user'),
            'created_at': user_data.get('created_at'),
            'last_login': datetime.now()
        }
        
        return True, user_info, "✅ Inicio de sesión exitoso"
        
    except Exception as e:
        return False, None, f"❌ Error al autenticar: {str(e)}"

def get_current_user():
    """Obtiene el usuario actual de la sesión"""
    return st.session_state.get('user', None)

def is_authenticated():
    """Verifica si el usuario está autenticado"""
    return 'user' in st.session_state and st.session_state['user'] is not None

def logout():
    """Cierra la sesión del usuario"""
    if 'user' in st.session_state:
        del st.session_state['user']
    st.rerun()

def require_auth(func):
    """
    Decorador para requerir autenticación en funciones
    """
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("🔒 Debes iniciar sesión para acceder a esta función")
            return None
        return func(*args, **kwargs)
    return wrapper

