import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAÚL STREAMING ELITE v11.0", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_final_v11.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT DEFAULT "PENDIENTE")')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, 
                       fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER, fecha_venta TEXT)''')
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN_GLOBAL')", (hash_pass('admin123'),))
    conn.commit()

init_db()

# --- ESTILOS CSS ULTRA PROFESIONALES (DARK NEÓN) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #050505; color: #ffffff; }
    
    /* Botones Gigantes Neón */
    .stButton>button {
        height: 120px !important;
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 20px !important;
        text-transform: uppercase !important;
        border: 2px solid #00ff00 !important;
        background-color: transparent !important;
        box-shadow: 0 0 15px rgba(0,255,0,0.2) !important;
        transition: 0.3s !important;
    }
    .stButton>button:hover {
        transform: scale(1.03) !important;
        box-shadow: 0 0 30px #00ff00 !important;
        color: #00ff00 !important;
        background-color: #000000 !important;
    }

    /* Tarjetas de Dashboard */
    div[data-testid="stMetric"] {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
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
if 'step' not in st.session_state: st.session_state['step'] = 'MENU_MODO'

# ==========================================
# 1. LOGIN RESTAURADO Y SEGURO
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png", width=200)
        st.markdown("</div>", unsafe_allow_html=True)
        st.title("🛡️ ACCESO SISTEMA VIP")
        u_input = st.text_input("Usuario")
        p_input = st.text_input("Contraseña", type="password")
        
        c1, c2 = st.columns(2)
        if c1.button("🚀 ENTRAR"):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u_input,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p_input):
                if res[1] == 'PENDIENTE': st.warning("CUENTA EN ESPERA.")
                else:
                    st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u_input, 'u_ran': res[1], 'step': 'MENU_MODO'})
                    st.rerun()
            else: st.error("DATOS INCORRECTOS")
        
        if c2.button("❓ OLVIDÉ CLAVE"):
            st.info("CONTACTA A SAÚL PARA RESTABLECER")
    st.stop()

# --- SIDEBAR ELITE ---
st.sidebar.markdown(f"<h2 style='text-transform:uppercase;'>👤 {st.session_state['u_nom']}</h2>", unsafe_allow_html=True)
if st.session_state['u_ran'] == 'ADMIN_GLOBAL':
    menu = st.sidebar.radio("Ir a:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "🗑️ ELIMINAR", "👥 USUARIOS GLOBALES", "🚪 SALIR"])
else:
    menu = st.sidebar.radio("Ir a:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "🚪 SALIR"])

conn = get_db(); uid = st.session_state['u_id']

# ==========================================
# 2. SELECTOR DE MODO (BOTONES GRANDES GIGANTES)
# ==========================================
if st.session_state['step'] == 'MENU_MODO':
    st.title(f"BIENVENIDO SOCIO VIP: {st.session_state['u_nom'].upper()}")
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3067/3067260.png' width='100'></p>", unsafe_allow_html=True)
        if st.button("📱 VENTA POR PERFILES", use_container_width=True):
            st.session_state['modo'] = "PERFILES"; st.rerun()
            
    with col2:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/5602/5602732.png' width='100'></p>", unsafe_allow_html=True)
        if st.button("📧 CUENTAS COMPLETAS", use_container_width=True):
            st.session_state['modo'] = "CUENTAS"; st.rerun()
    st.stop()

# --- LÓGICA DE MENÚS (RESTAURADA) ---
if menu == "🚪 SALIR":
    st.session_state.clear(); st.rerun()

elif menu == "📊 DASHBOARD":
    st.markdown("<h1 style='text-transform:uppercase;'>RESUMEN DEL NEGOCIO</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 CUENTAS MAESTRAS", pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0])
    c2.metric("✅ PERFILES VENDIDOS", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0])
    c3.metric("🔓 PERFILES LIBRES", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0])
    
    # Próximos a Vencer (Multi-inquilino)
    st.divider()
    df = pd.read_sql_query(f"SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True)

elif menu == "🌐 PLATAFORMAS":
    st.markdown("<h1 style='text-transform:uppercase;'>REGISTRO DE CUENTAS</h1>", unsafe_allow_html=True)
    with st.form("reg_master", clear_on_submit=True):
        col1, col2, col3 = st.columns([2,2,1])
        plat = col1.selectbox("PLATAFORMA", ["NETFLIX","MAX","PRIME","DISNEY","VIX","CRUNCHY"])
        mail = col2.text_input("CORREO ELECTRÓNICO")
        clv = col1.text_input("CONTRASEÑA")
        cst = col2.number_input("COSTO S/", 0.0)
        vnc = c3.date_input("VENCIMIENTO PROVEEDOR")
        if st.form_submit_button("🚀 ACTIVAR CUENTA MAESTRA"):
            try:
                conn.cursor().execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?)", (plat, mail, clv, vnc.strftime("%d/%m/%Y"), cst, uid))
                conn.commit(); st.success("CUENTA CREADA")
            except: st.error("DUPLICADO")

elif menu == "📱 GESTIÓN PERFILES":
    st.markdown("<h1 style='text-transform:uppercase;'>PANEL DE VENTAS</h1>", unsafe_allow_html=True)
    
    # Selector por botones de colores
    colp = st.columns(6)
    plats = [("NETFLIX","#E50914"), ("DISNEY","#006E99"), ("MAX","#7B2CBF"), ("PRIME","#00A8E1"), ("VIX","#FF5A00"), ("CRUNCHY","#F47521")]
    for i, (name, color) in enumerate(plats):
        if colp[i].button(name, key=f"btn_{name}"): st.session_state['p_sel'] = name
        
    p_sel = st.session_state.get('p_sel', 'NETFLIX')
    st.info(f"GESTIONANDO: {p_sel}")
    
    ctas = pd.read_sql_query(f"SELECT email, password FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)
    if not ctas.empty:
        for _, c in ctas.iterrows():
            with st.expander(f"📧 {c['email']}"):
                st.code(f"CLAVE: {c['password']}")
                perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c['email']}'", conn)
                for _, row in perfs.iterrows():
                    st.markdown(f"<div class='stMetric'><b>{row['estado']}</b> | Perfil: {row['nombre']} | PIN: {row['pin']}</div>", unsafe_allow_html=True)
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

elif menu == "💰 FINANZAS PRO":
    st.markdown("<h1 style='text-transform:uppercase;'>FINANZAS EN SOLES (S/)</h1>", unsafe_allow_html=True)
    eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
    st.metric("📉 EGRESOS TOTALES", moneda(eg))

elif menu == "👥 USUARIOS GLOBALES":
    if st.session_state['u_ran'] != 'ADMIN_GLOBAL': st.stop()
    st.markdown("<h1 style='text-transform:uppercase;'>APROBACIÓN DE SOCIOS VIP</h1>", unsafe_allow_html=True)
    pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
    for _, r in pends.iterrows():
        c1, c2 = st.columns(2)
        c1.write(f"Socio Solicitante: {r['user']}")
        if c2.button("✅ ACTIVAR COMO VIP", key=f"acc_{r['id']}"):
            conn.cursor().execute(f"UPDATE usuarios SET rango='SOCIO VIP' WHERE id={r['id']}")
            conn.commit(); st.rerun()