import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAÚL STREAMING - NEON PRO", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_neon_v13.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, tipo_negocio TEXT, sub_tipo TEXT, plataforma TEXT, email TEXT UNIQUE, 
                       password TEXT, fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER, fecha_venta TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN')", (hash_pass('admin123'),))
    conn.commit()

init_db()

# --- ESTILOS CSS AVANZADOS (NEÓN Y CROMADO) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* Efecto Cromado en Títulos */
    .chrome-text {
        background: linear-gradient(0deg, #7a7a7a 0%, #ffffff 50%, #7a7a7a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-transform: uppercase;
        filter: drop-shadow(0 0 2px rgba(255,255,255,0.5));
    }

    /* Botones con Brillo Neón */
    .stButton>button {
        background: #111 !important;
        color: white !important;
        border: 2px solid #00ff00 !important;
        border-radius: 15px !important;
        box-shadow: 0 0 10px #00ff00;
        transition: 0.3s;
        text-transform: uppercase;
        font-weight: bold;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px #00ff00;
        transform: scale(1.02);
        color: #00ff00 !important;
    }

    /* Estilo para tarjetas de gestión */
    .card-pro {
        background: #121212;
        padding: 25px;
        border-radius: 20px;
        border: 1px solid #333;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.7);
    }
    
    /* Login Centered Hacker Image */
    .hacker-img { display: block; margin: 0 auto 20px; border-radius: 50%; box-shadow: 0 0 30px #00ff00; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(v): return f"S/ {v:,.2f}"

# --- NAVEGACIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'step' not in st.session_state: st.session_state['step'] = 'LOGIN'
if 'negocio' not in st.session_state: st.session_state['negocio'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'

# ==========================================
# 1. LOGIN HACKER PRO
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'><img src='https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png' class='hacker-img' width='250'></div>", unsafe_allow_html=True)
        st.markdown("<h1 class='chrome-text' style='text-align:center;'>ACCESS SYSTEM</h1>", unsafe_allow_html=True)
        u = st.text_input("USUARIO", key="user_in")
        p = st.text_input("CONTRASEÑA", type="password", key="pass_in")
        if st.button("🚀 ENTRAR AL SISTEMA", use_container_width=True):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p):
                st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'step': 'MODO_NEGOCIO'})
                st.rerun()
            else: st.error("ACCESO DENEGADO")
        if st.button("❓ OLVIDÉ MI CONTRASEÑA", type="secondary"):
            st.info("CONTACTA A SAÚL PARA REINICIAR CREDENCIALES")
    st.stop()

# ==========================================
# 2. SELECTOR DE MODO (BOTONES GRANDES)
# ==========================================
uid = st.session_state['u_id']
conn = get_db()

if st.session_state['step'] == 'MODO_NEGOCIO':
    st.markdown(f"<h2 class='chrome-text'>BIENVENIDO {st.session_state['u_nom']}</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div style='text-align:center;'><img src='https://cdn-icons-png.flaticon.com/512/3067/3067260.png' width='80'></div>", unsafe_allow_html=True)
        if st.button("📱 VENTA POR PERFILES", use_container_width=True):
            st.session_state.update({'negocio': 'PERFILES', 'step': 'PANEL_CONTROL'}); st.rerun()
    with col2:
        st.markdown("<div style='text-align:center;'><img src='https://cdn-icons-png.flaticon.com/512/5602/5602732.png' width='80'></div>", unsafe_allow_html=True)
        if st.button("📧 CUENTAS COMPLETAS", use_container_width=True):
            st.session_state.update({'negocio': 'CUENTAS', 'step': 'PANEL_CONTROL'}); st.rerun()
    
    st.write("---")
    if st.button("🚪 CERRAR SESIÓN"): st.session_state.clear(); st.rerun()
    st.stop()

# ==========================================
# 3. PANEL DE HERRAMIENTAS (MOSAICO NEÓN)
# ==========================================
neg = st.session_state['negocio']

if st.session_state['step'] == 'PANEL_CONTROL':
    if st.session_state['herramienta'] == 'MENU':
        st.markdown(f"<h2 class='chrome-text'>ADMIN: {neg}</h2>", unsafe_allow_html=True)
        
        # Mosaico 3x2 con Iconos nítidos
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3502/3502601.png' width='60'></p>", unsafe_allow_html=True)
            if st.button("➕ SUBIR"): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
        with m2:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/869/869121.png' width='60'></p>", unsafe_allow_html=True)
            if st.button("📱 GESTIÓN"): st.session_state['herramienta'] = 'GESTION'; st.rerun()
        with m3:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3119/3119338.png' width='60'></p>", unsafe_allow_html=True)
            if st.button("🔔 COBRANZA"): st.session_state['herramienta'] = 'COBRANZA'; st.rerun()
            
        m4, m5, m6 = st.columns(3)
        with m4:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/2454/2454282.png' width='60'></p>", unsafe_allow_html=True)
            if st.button("💰 FINANZAS"): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
        with m5:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3221/3221803.png' width='60'></p>", unsafe_allow_html=True)
            if st.button("🗑️ BAJAS"): st.session_state['herramienta'] = 'ELIMINAR'; st.rerun()
        with m6:
            st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/9131/9131529.png' width='60'></p>", unsafe_allow_html=True)
            if st.button("👤 PERFIL"): st.session_state['herramienta'] = 'PERFIL'; st.rerun()

        st.write("---")
        if st.button("⬅️ CAMBIAR MODO"): st.session_state['step'] = 'MODO_NEGOCIO'; st.rerun()

    # --- HERRAMIENTA GESTIÓN (PLATAFORMAS POR BOTONES) ---
    elif st.session_state['herramienta'] == 'GESTION':
        st.markdown("<h2 class='chrome-text'>GESTIÓN DE VENTAS</h2>", unsafe_allow_html=True)
        if st.button("⬅️ VOLVER AL PANEL"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        
        # Botones de plataforma con colores Neón
        colp = st.columns(6)
        plats = [("NETFLIX","#E50914"), ("MAX","#7B2CBF"), ("PRIME","#00A8E1"), ("DISNEY","#006E99"), ("VIX","#FF5A00"), ("CRUNCHY","#F47521")]
        for i, (name, color) in enumerate(plats):
            if colp[i].button(name, key=f"btn_{name}"): st.session_state['p_sel'] = name
            
        p_sel = st.session_state.get('p_sel', 'NETFLIX')
        st.markdown(f"### ADMINISTRANDO: <span style='color:{next(c for n,c in plats if n==p_sel)};'>{p_sel}</span>", unsafe_allow_html=True)
        
        ctas = pd.read_sql_query(f"SELECT email, password FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)
        if not ctas.empty:
            for _, c in ctas.iterrows():
                with st.expander(f"📧 {c['email']}"):
                    st.code(f"CLAVE: {c['password']}")
                    if neg == 'PERFILES':
                        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c['email']}'", conn)
                        for _, row in perfs.iterrows():
                            st.markdown(f"<div class='card-pro'><b>{row['estado']}</b> | Perfil: {row['nombre']} | PIN: {row['pin']}</div>", unsafe_allow_html=True)
                            c1, c2, c3 = st.columns(3)
                            if row['estado'] == 'LIBRE':
                                wa = c1.text_input("WhatsApp", key=f"wa_{row['id']}")
                                if c2.button("🛒 VENDER", key=f"v_{row['id']}"):
                                    v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                    conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}' WHERE id={row['id']}")
                                    conn.commit(); st.rerun()
                            else:
                                if c1.button("🔄 RENOVAR", key=f"r_{row['id']}"):
                                    nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                                    conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                                    conn.commit(); st.rerun()
                                if c2.button("✂️ CORTAR", key=f"c_{row['id']}"):
                                    conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, precio_venta=0 WHERE id={row['id']}")
                                    conn.commit(); st.rerun()
                                msg = f"*ENTREGA {p_sel}*\n- Correo: {c['email']}\n- Clave: {c['password']}\n- Perfil: {row['nombre']}\n- PIN: {row['pin']}"
                                c3.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:10px; width:100%;">🚀 WHATSAPP</button></a>', unsafe_allow_html=True)

    # --- HERRAMIENTA SUBIR ---
    elif st.session_state['herramienta'] == 'SUBIR':
        st.markdown("<h2 class='chrome-text'>REGISTRO DE CUENTAS</h2>", unsafe_allow_html=True)
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        
        with st.form("reg_master"):
            c1, c2 = st.columns(2)
            plat = c1.selectbox("PLATAFORMA", ["NETFLIX","MAX","PRIME","DISNEY","VIX","CRUNCHY"])
            mail = c2.text_input("CORREO")
            clv = c1.text_input("CONTRASEÑA")
            cst = c2.number_input("COSTO PROVEEDOR S/", 0.0)
            if st.form_submit_button("🚀 ACTIVAR MAESTRA"):
                try:
                    conn.cursor().execute("INSERT INTO cuentas (tipo_negocio, plataforma, email, password, costo, creador_id) VALUES (?,?,?,?,?,?)", (neg, plat, mail, clv, cst, uid))
                    conn.commit(); st.success("CUENTA CARGADA")
                except: st.error("DUPLICADO")
        
        if neg == 'PERFILES':
            st.write("---")
            st.subheader("➕ AGREGAR PERFILES")
            ctas_l = pd.read_sql_query(f"SELECT email FROM cuentas WHERE creador_id={uid}", conn)['email'].tolist()
            if ctas_l:
                target = st.selectbox("ELEGIR CUENTA", ctas_l)
                with st.form("add_p"):
                    n, p = st.columns(2)
                    nom = n.text_input("NOMBRE")
                    pin = p.text_input("PIN")
                    if st.form_submit_button("➕ AGREGAR"):
                        conn.cursor().execute("INSERT INTO perfiles (email, nombre, pin, creador_id) VALUES (?,?,?,?)", (target, nom, pin, uid))
                        conn.commit(); st.success("PERFIL LISTO")

    # --- FINANZAS (FILTRO DÍA/MES/AÑO) ---
    elif st.session_state['herramienta'] == 'FINANZAS':
        st.markdown("<h2 class='chrome-text'>FINANZAS PRO</h2>", unsafe_allow_html=True)
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.info("Formato de Moneda: Soles (S/)")
        # Aquí puedes añadir un selector de fechas si guardas la fecha de venta en la tabla perfiles
        eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
        st.metric("📉 EGRESOS TOTALES", moneda(eg))

    # --- (NOTIFICACIONES / ELIMINAR / PERFIL SIGUEN LA MISMA LÓGICA DE HERRAMIENTA) ---
    else:
        if st.button("⬅️ VOLVER AL PANEL"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.write("Módulo en mantenimiento neón...")