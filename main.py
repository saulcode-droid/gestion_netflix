import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SISTEMA STREAMING VIP", page_icon="🎬", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_v139.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, tipo_negocio TEXT, plataforma TEXT, email TEXT UNIQUE, 
                       password TEXT, fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER, fecha_venta TEXT)''')
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN_GLOBAL')", (hash_pass('admin123'),))
    conn.commit()

init_db()

# --- ESTILOS CSS PROFESIONALES (NEÓN Y CENTRADO) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #0b0e14; color: white; }
    
    /* Botones Gigantes Neón */
    .stButton>button {
        background-color: #161b22 !important;
        color: white !important;
        border: 2px solid #00ff00 !important;
        border-radius: 15px !important;
        box-shadow: 0 0 10px rgba(0,255,0,0.2);
        height: auto !important;
        padding: 20px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px #00ff00;
        transform: scale(1.03);
        color: #00ff00 !important;
    }

    /* Imagen del Hacker Centrada */
    .hacker-img { display: block; margin: 0 auto; border-radius: 20px; box-shadow: 0 0 20px #00ff00; }
    
    /* Centrar textos */
    h1, h2, h3 { text-align: center; text-transform: uppercase; letter-spacing: 2px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAR ESTADOS DE SESIÓN (PARA EVITAR ERRORES) ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'u_ran' not in st.session_state: st.session_state['u_ran'] = None
if 'modo' not in st.session_state: st.session_state['modo'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'

# ==========================================
# 1. LOGIN RESTAURADO Y SEGURO
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png", width=250)
        st.markdown("<h1>SISTEMA ELITE</h1>", unsafe_allow_html=True)
        u_input = st.text_input("USUARIO")
        p_input = st.text_input("CONTRASEÑA", type="password")
        
        c1, c2 = st.columns(2)
        if c1.button("🚀 ENTRAR"):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u_input,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p_input):
                st.session_state.update({
                    'auth': True, 'u_id': res[0], 'u_nom': u_input, 
                    'u_ran': res[1], 'modo': None, 'herramienta': 'MENU'
                })
                st.rerun()
            else: st.error("DATOS INCORRECTOS")
        
        if c2.button("❓ OLVIDÉ CLAVE"):
            st.info("CONTACTE A SAÚL PARA RESTABLECER")
    st.stop()

# ==========================================
# 2. SELECTOR DE MODO (BOTONES GRANDES CON ICONOS)
# ==========================================
uid = st.session_state['u_id']
conn = get_db()

if st.session_state['modo'] is None:
    st.markdown(f"<h2>BIENVENIDO ADMIN: {st.session_state['u_nom'].upper()}</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3067/3067260.png' width='120'></p>", unsafe_allow_html=True)
        if st.button("📱 VENTA POR PERFILES"):
            st.session_state['modo'] = "PERFILES"; st.rerun()
            
    with col2:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/5602/5602732.png' width='120'></p>", unsafe_allow_html=True)
        if st.button("📧 CUENTAS COMPLETAS"):
            st.session_state['modo'] = "CUENTAS"; st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 CERRAR SESIÓN TOTAL"):
        st.session_state.clear(); st.rerun()
    st.stop()

# ==========================================
# 3. PANEL DE CONTROL (3x2 CON IMÁGENES)
# ==========================================
if st.session_state['herramienta'] == 'MENU':
    st.markdown(f"<h2>MODO: {st.session_state['modo']}</h2>", unsafe_allow_html=True)
    st.write("---")
    
    # Fila 1
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3502/3502601.png' width='80'></p>", unsafe_allow_html=True)
        if st.button("➕ SUBIR"): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
    with m2:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/869/869121.png' width='80'></p>", unsafe_allow_html=True)
        if st.button("📱 GESTIÓN"): st.session_state['herramienta'] = 'GESTION'; st.rerun()
    with m3:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3119/3119338.png' width='80'></p>", unsafe_allow_html=True)
        if st.button("🔔 COBRANZA"): st.session_state['herramienta'] = 'COBRANZA'; st.rerun()
        
    # Fila 2
    m4, m5, m6 = st.columns(3)
    with m4:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/2454/2454282.png' width='80'></p>", unsafe_allow_html=True)
        if st.button("💰 FINANZAS"): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
    with m5:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3221/3221803.png' width='80'></p>", unsafe_allow_html=True)
        if st.button("🗑️ BAJAS"): st.session_state['herramienta'] = 'ELIMINAR'; st.rerun()
    with m6:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/9131/9131529.png' width='80'></p>", unsafe_allow_html=True)
        if st.button("👤 PERFIL"): st.session_state['herramienta'] = 'PERFIL'; st.rerun()

    st.write("---")
    if st.button("⬅️ CAMBIAR MODO"):
        st.session_state['modo'] = None; st.rerun()

# ==========================================
# 4. HERRAMIENTA: GESTIÓN (BOTONES DE COLOR)
# ==========================================
elif st.session_state['herramienta'] == 'GESTION':
    st.markdown("<h2>PANEL DE GESTIÓN</h2>", unsafe_allow_html=True)
    if st.button("⬅️ VOLVER AL MENÚ"): st.session_state['herramienta'] = 'MENU'; st.rerun()
    
    colp = st.columns(6)
    plats = [("NETFLIX","#E50914"), ("MAX","#7B2CBF"), ("PRIME","#00A8E1"), ("DISNEY","#006E99"), ("VIX","#FF5A00"), ("CRUNCHY","#F47521")]
    for i, (name, color) in enumerate(plats):
        if colp[i].button(name): st.session_state['p_sel'] = name
    
    p_sel = st.session_state.get('p_sel', 'NETFLIX')
    st.info(f"GESTIONANDO: {p_sel}")
    
    # Aquí iría el resto de tu lógica de ventas...
    st.write("Cargando cuentas...")

# (El resto de funciones se cargan solo si herramienta != 'MENU')
elif st.session_state['herramienta'] == 'SUBIR':
    if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
    st.markdown("<h2>SUBIR PLATAFORMAS</h2>", unsafe_allow_html=True)
    # Lógica de subir...

elif st.session_state['herramienta'] == 'FINANZAS':
    if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
    st.markdown("<h2>REPORTES FINANCIEROS</h2>", unsafe_allow_html=True)
    # Lógica finanzas...

elif st.session_state['herramienta'] == 'COBRANZA':
    if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
    st.markdown("<h2>CENTRAL DE NOTIFICACIONES</h2>", unsafe_allow_html=True)

elif st.session_state['herramienta'] == 'ELIMINAR':
    if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
    st.markdown("<h2>BAJAS DEL SISTEMA</h2>", unsafe_allow_html=True)

elif st.session_state['herramienta'] == 'PERFIL':
    if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
    st.markdown("<h2>MI PERFIL DE SOCIO</h2>", unsafe_allow_html=True)