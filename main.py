import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="PERUVIAN STREAMING - NEON PRO", page_icon="💎", layout="wide")

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
                      (id INTEGER PRIMARY KEY, tipo_negocio TEXT, plataforma TEXT, email TEXT UNIQUE, 
                       password TEXT, fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER, fecha_venta TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN_GLOBAL')", (hash_pass('admin123'),))
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

    /* Botones Neón */
    .stButton>button {
        background-color: transparent !important;
        color: white !important;
        border: 2px solid #00ff00 !important;
        border-radius: 12px !important;
        box-shadow: 0 0 10px rgba(0,255,0,0.2);
        transition: 0.3s;
        text-transform: uppercase;
        font-weight: bold;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px #00ff00;
        transform: scale(1.02);
        color: #00ff00 !important;
    }
    
    /* Botones de colores para plataformas */
    .btn-netflix>button { border-color: #E50914 !important; color: #E50914 !important; }
    .btn-disney>button { border-color: #006E99 !important; color: #006E99 !important; }

    /* Tarjetas de Dashboard */
    div[data-testid="stMetric"] {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    
    /* Login Centered Hacker Image */
    .hacker-img { display: block; margin: 0 auto 20px; border-radius: 50%; box-shadow: 0 0 30px #00ff00; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(valor): return f"S/ {valor:,.2f}"
def calcular_dias(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

# --- NAVEGACIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'modo' not in st.session_state: st.session_state['modo'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'

# ==========================================
# 1. LOGIN HACKER PRO
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'><img src='https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png' class='hacker-img' width='250'></div>", unsafe_allow_html=True)
        st.markdown("<h1 class='chrome-text' style='text-align:center;'>SISTEMA VIP</h1>", unsafe_allow_html=True)
        u = st.text_input("USUARIO", key="user_in")
        p = st.text_input("CONTRASEÑA", type="password", key="pass_in")
        if st.button("🚀 ENTRAR AL SISTEMA", use_container_width=True):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p):
                st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'modo': None, 'herramienta': 'MENU'})
                st.rerun()
            else: st.error("ACCESO DENEGADO")
        if st.button("❓ OLVIDÉ MI CONTRASEÑA", type="secondary"):
            st.info("CONTACTA A SAÚL PARA REINICIAR CREDENCIALES")
    st.stop()

# --- SIDEBAR ELITE ---
st.sidebar.markdown(f"<h2 class='chrome-text'>👤 {st.session_state['u_nom'].upper()}</h2>", unsafe_allow_html=True)
if st.session_state['u_ran'] == 'ADMIN_GLOBAL':
    menu = st.sidebar.radio("Ir a:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "🗑️ ELIMINAR", "👥 USUARIOS GLOBALES", "🚪 SALIR"])
else:
    menu = st.sidebar.radio("Ir a:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])

conn = get_db(); uid = st.session_state['u_id']

# ==========================================
# 2. SELECTOR DE MODO (GIGANTES IGUALES v11.0)
# ==========================================
if st.session_state['modo'] is None:
    st.markdown("<h1 class='chrome-text'>SELECCIONE MODO DE TRABAJO</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        # Icono grande y visible arriba del texto
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3067/3067260.png' width='100'></p>", unsafe_allow_html=True)
        if st.button("📱 VENTA POR PERFILES", use_container_width=True):
            st.session_state['modo'] = "PERFILES"; st.rerun()
            
    with col2:
        # Icono grande y visible arriba del texto
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/5602/5602732.png' width='100'></p>", unsafe_allow_html=True)
        if st.button("📧 CUENTAS COMPLETAS", use_container_width=True):
            st.session_state['modo'] = "CUENTAS"; st.rerun()
    st.stop()

# ==========================================
# 3. GESTIÓN DE PERFILES (WHATSAPP PRO)
# ==========================================
elif menu == "📱 GESTIÓN PERFILES":
    st.markdown("<h1 class='chrome-text'>PANEL DE VENTAS</h1>", unsafe_allow_html=True)
    
    # Selector por botones de colores
    colp = st.columns(6)
    plats = [("NETFLIX","#E50914"), ("MAX","#7B2CBF"), ("PRIME","#00A8E1"), ("DISNEY","#006E99"), ("VIX","#FF5A00"), ("CRUNCHY","#F47521")]
    for i, (name, color) in enumerate(plats):
        if colp[i].button(name, key=f"btn_{name}"): st.session_state['p_sel'] = name
        
    p_sel = st.session_state.get('p_sel', 'NETFLIX')
    st.markdown(f"### ADMINISTRANDO: {p_sel}", unsafe_allow_html=True)
    
    ctas = pd.read_sql_query(f"SELECT email, password FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)
    if not ctas.empty:
        for _, c in ctas.iterrows():
            with st.expander(f"📧 {c['email']}"):
                st.code(f"CLAVE MAESTRA: {c['password']}")
                perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c['email']}' AND creador_id={uid}", conn)
                for _, row in perfs.iterrows():
                    st.markdown(f"<div class='stMetric'><b>{row['estado']}</b> | Perfil: {row['nombre']} | PIN: {row['pin']}</div>", unsafe_allow_html=True)
                    if row['estado'] == 'LIBRE':
                        c1, c2 = st.columns(2)
                        wa = c1.text_input("WhatsApp", key=f"wa_{row['id']}")
                        if c2.button("🛒 VENDER", key=f"v_{row['id']}"):
                            v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                            conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}' WHERE id={row['id']}")
                            conn.commit(); st.rerun()
                    else:
                        d = calcular_dias(row['fecha_vence'])
                        st.write(f"📅 Vence: {row['fecha_vence']} (**{d} días**)")
                        
                        cb1, cb2, cb3 = st.columns(3)
                        if cb1.button("🔄 RENOVAR", key=f"r_{row['id']}", use_container_width=True):
                            nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                            conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                            conn.commit(); st.rerun()
                        if cb2.button("✂️ CORTAR", key=f"c_{row['id']}", use_container_width=True):
                            conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, precio_venta=0 WHERE id={row['id']}")
                            conn.commit(); st.rerun()
                        msg = f"*ENTREGA {p_sel}*\n- Correo: {c['email']}\n- Clave: {c['password']}\n- Perfil: {row['nombre']}\n- PIN: {row['pin']}\n- Vence: {row['fecha_vence']}"
                        cb3.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:10px; width:100%;">🚀 WHATSAPP</button></a>', unsafe_allow_html=True)

# --- MENÚS DE DASHBOARD Y PLATAFORMAS (RESTO DEL CÓDIGO v11.0) ---
elif menu == "📊 DASHBOARD":
    st.markdown("<h1 class='chrome-text'>RESUMEN DE NEGOCIO</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 CUENTAS MAESTRAS", pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0])
    c2.metric("✅ PERFILES VENDIDOS", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0])
    c3.metric("🔓 PERFILES LIBRES", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0])

elif menu == "🌐 PLATAFORMAS":
    st.markdown("<h1 class='chrome-text'>REGISTRO DE CUENTAS</h1>", unsafe_allow_html=True)
    with st.form("reg_mas"):
        c1, c2, c3 = st.columns([2,2,1])
        plat = c1.selectbox("PLATAFORMA", ["NETFLIX","MAX","PRIME","DISNEY","VIX","CRUNCHY"])
        mail = c2.text_input("CORREO ELECTRÓNICO")
        clv = c1.text_input("CONTRASEÑA")
        cst = c2.number_input("COSTO S/", 0.0)
        vnc = c3.date_input("VENCIMIENTO PROVEEDOR")
        if st.form_submit_button("🚀 ACTIVAR MAESTRA"):
            try:
                conn.cursor().execute("INSERT INTO cuentas (tipo_negocio, plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES ('SOCIO VIP',?,?,?,?,?,?)", (plat, mail, clv, vnc.strftime("%d/%m/%Y"), cst, uid))
                conn.commit(); st.success("CUENTA CREADA")
            except: st.error("DUPLICADO")