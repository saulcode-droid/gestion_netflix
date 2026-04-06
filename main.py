import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="PERUVIAN STREAMING V15", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_v15.db'

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
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN')", (hash_pass('admin123'),))
    conn.commit()

init_db()

# --- ESTILOS CSS ULTRA PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;} /* OCULTAR MENÚ LATERAL */
    
    .stApp { background-color: #0b0e14; color: white; }
    
    /* Efecto Cromado en Títulos */
    .chrome-text {
        background: linear-gradient(0deg, #888 0%, #fff 50%, #888 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-transform: uppercase;
        filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));
    }

    /* Botones de Mosaico Grandes */
    .stButton>button {
        background-color: #161b22 !important;
        color: white !important;
        border: 2px solid #00ff00 !important;
        border-radius: 20px !important;
        height: 180px !important;
        width: 100% !important;
        font-size: 20px !important;
        font-weight: bold !important;
        box-shadow: 0 0 15px rgba(0,255,0,0.2) !important;
        transition: 0.4s !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .stButton>button:hover {
        box-shadow: 0 0 35px #00ff00 !important;
        transform: scale(1.05) !important;
        background-color: #000 !important;
    }

    /* Botón Volver Pequeño */
    .btn-volver button {
        height: 50px !important;
        width: 150px !important;
        font-size: 14px !important;
        border-color: #ff4b4b !important;
    }
    
    .card-pro { background: #1a1e26; padding: 20px; border-radius: 15px; border-left: 5px solid #00ff00; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(v): return f"S/ {v:,.2f}"

# --- INICIALIZACIÓN DE ESTADOS ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'u_id' not in st.session_state: st.session_state['u_id'] = None
if 'u_nom' not in st.session_state: st.session_state['u_nom'] = None
if 'u_ran' not in st.session_state: st.session_state['u_ran'] = None
if 'step' not in st.session_state: st.session_state['step'] = 'LOGIN'
if 'modo' not in st.session_state: st.session_state['modo'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'

# ==========================================
# 1. LOGIN (CENTRADO)
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.3, 1])
    with col_log:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;'><img src='https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png' width='250'></div>", unsafe_allow_html=True)
        st.markdown("<h1 class='chrome-text' style='text-align:center;'>SISTEMA ELITE</h1>", unsafe_allow_html=True)
        u = st.text_input("USUARIO")
        p = st.text_input("CONTRASEÑA", type="password")
        if st.button("🚀 ENTRAR AL SISTEMA", use_container_width=True):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, user, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[3] == hash_pass(p):
                st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': res[1], 'u_ran': res[2], 'step': 'MODO'})
                st.rerun()
            else: st.error("DATOS INCORRECTOS")
    st.stop()

# ==========================================
# 2. SELECTOR DE MODO (BOTONES GRANDES CUADRADOS)
# ==========================================
conn = get_db(); uid = st.session_state['u_id']

if st.session_state['step'] == 'MODO':
    st.markdown(f"<h1 class='chrome-text' style='text-align:center;'>BIENVENIDO {st.session_state['u_nom'].upper()}</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3067/3067260.png' width='120'></p>", unsafe_allow_html=True)
        if st.button("📱 VENTA POR PERFILES", key="btn_p"):
            st.session_state.update({'modo': 'PERFILES', 'step': 'HERRAMIENTAS'}); st.rerun()
            
    with col2:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/5602/5602732.png' width='120'></p>", unsafe_allow_html=True)
        if st.button("📧 CUENTAS COMPLETAS", key="btn_c"):
            st.session_state.update({'modo': 'CUENTAS', 'step': 'HERRAMIENTAS'}); st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 SALIR TOTAL", key="btn_out"):
        st.session_state.clear(); st.rerun()
    st.stop()

# ==========================================
# 3. PANEL DE HERRAMIENTAS (MOSAICO 3x2)
# ==========================================
if st.session_state['step'] == 'HERRAMIENTAS':
    if st.session_state['herramienta'] == 'MENU':
        st.markdown(f"<h1 class='chrome-text' style='text-align:center;'>PANEL {st.session_state['modo']}</h1>", unsafe_allow_html=True)
        
        # Fila 1
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3502/3502601.png' width='80'></p>", unsafe_allow_html=True)
            if st.button("➕ SUBIR", key="m1"): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
        with m2:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/869/869121.png' width='80'></p>", unsafe_allow_html=True)
            if st.button("📱 GESTIÓN", key="m2"): st.session_state['herramienta'] = 'GESTION'; st.rerun()
        with m3:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3119/3119338.png' width='80'></p>", unsafe_allow_html=True)
            if st.button("🔔 COBRANZA", key="m3"): st.session_state['herramienta'] = 'COBRANZA'; st.rerun()
            
        # Fila 2
        m4, m5, m6 = st.columns(3)
        with m4:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/2454/2454282.png' width='80'></p>", unsafe_allow_html=True)
            if st.button("💰 FINANZAS", key="m4"): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
        with m5:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3221/3221803.png' width='80'></p>", unsafe_allow_html=True)
            if st.button("🗑️ BAJAS", key="m5"): st.session_state['herramienta'] = 'BAJAS'; st.rerun()
        with m6:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/9131/9131529.png' width='80'></p>", unsafe_allow_html=True)
            if st.button("👥 USUARIOS", key="m6"): st.session_state['herramienta'] = 'USUARIOS'; st.rerun()

        st.write("---")
        if st.button("⬅️ VOLVER AL MODO"): st.session_state['step'] = 'MODO'; st.rerun()

    # ==========================================
    # SUBMÓDULOS (SUBIR, GESTIÓN, ETC)
    # ==========================================
    elif st.session_state['herramienta'] == 'SUBIR':
        st.markdown("<div class='btn-volver'>", unsafe_allow_html=True)
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.header("🛒 REGISTRO DE CUENTAS")
        
        with st.form("f_reg"):
            c1, c2 = st.columns(2)
            plat = c1.selectbox("PLATAFORMA", ["NETFLIX","MAX","DISNEY","PRIME","VIX","CRUNCHY"])
            mail = c2.text_input("CORREO")
            clv = c1.text_input("CONTRASEÑA")
            cst = c2.number_input("COSTO PROVEEDOR S/", 0.0)
            vnc = st.date_input("VENCIMIENTO")
            if st.form_submit_button("🚀 ACTIVAR MAESTRA"):
                try:
                    conn.cursor().execute("INSERT INTO cuentas (tipo_negocio, plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?,?)",
                                         (st.session_state['modo'], plat, mail, clv, vnc.strftime("%d/%m/%Y"), cst, uid))
                    conn.commit(); st.success("CUENTA CARGADA EXITOSAMENTE"); st.rerun()
                except: st.error("CORREO YA EXISTE")

    elif st.session_state['herramienta'] == 'GESTION':
        st.markdown("<div class='btn-volver'>", unsafe_allow_html=True)
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.header("📱 ADMINISTRACIÓN")
        
        # Filtro por plataforma (BOTONES)
        col_p = st.columns(6)
        plats = [("NETFLIX","#E50914"), ("MAX","#7B2CBF"), ("PRIME","#00A8E1"), ("DISNEY","#006E99"), ("VIX","#FF5A00"), ("CRUNCHY","#F47521")]
        for i, (n, c) in enumerate(plats):
            if col_p[i].button(n, key=f"sel_{n}"): st.session_state['p_sel'] = n
        
        p_sel = st.session_state.get('p_sel', 'NETFLIX')
        st.info(f"GESTIONANDO: {p_sel}")
        
        df_ctas = pd.read_sql_query(f"SELECT email, password FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)
        for _, c in df_ctas.iterrows():
            with st.expander(f"📧 {c['email']}"):
                st.code(f"CLAVE: {c['password']}")
                if st.session_state['modo'] == 'PERFILES':
                    perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c['email']}'", conn)
                    for _, r in perfs.iterrows():
                        st.markdown(f"<div class='card-pro'><b>{r['estado']}</b> - {r['nombre']}</div>", unsafe_allow_html=True)
                        # Lógica de venta, renovar, cortar aquí...

    elif st.session_state['herramienta'] == 'FINANZAS':
        st.markdown("<div class='btn-volver'>", unsafe_allow_html=True)
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.header("💰 BALANCE FINANCIERO")
        eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
        st.metric("📉 EGRESOS TOTALES (PROVEEDORES)", moneda(eg))