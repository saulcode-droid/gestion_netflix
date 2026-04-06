import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAÚL STREAMING ELITE - v13.8", page_icon="💎", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_v138.db'

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
    # Crear admin maestro global por defecto si no existe
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", ('admin', hash_pass('admin123'), 'ADMIN_GLOBAL'))
    conn.commit()

init_db()

# --- ESTILOS CSS ULTRA PREMIUM (NEÓN & CHROME) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #0d0d0d; color: #e0e0e0; }
    
    /* Efecto Cromado en Títulos */
    .chrome-text {
        background: linear-gradient(0deg, #888 0%, #fff 50%, #888 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        text-transform: uppercase;
        filter: drop-shadow(0 0 2px rgba(255,255,255,0.3));
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
# 1. LOGIN RESTAURADO CON HACKER
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'><img src='https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png' width='200'></div>", unsafe_allow_html=True)
        st.markdown("<h2 class='chrome-text' style='text-align:center;'>SISTEMA VIP</h2>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔑 INGRESAR", "📝 REGISTRO"])
        
        with t1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Contraseña", type="password", key="l_p")
            
            c1, c2 = st.columns(2)
            if c1.button("🚀 ENTRAR", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
                res = cursor.fetchone()
                if res and res[2] == hash_pass(p):
                    if res[1] == 'PENDIENTE': st.warning("CUENTA EN ESPERA.")
                    else:
                        st.session_state['auth'], st.session_state['u_id'], st.session_state['u_nom'], st.session_state['u_ran'] = True, res[0], u, res[1]
                        st.rerun()
                else: st.error("DATOS INCORRECTOS")
            
            if c2.button("❓ OLVIDÉ CLAVE", use_container_width=True):
                st.info("CONTACTA A SAÚL POR WHATSAPP.")
        
        with t2:
            nu = st.text_input("NUEVO USUARIO")
            np = st.text_input("NUEVA CONTRASEÑA", type="password")
            if st.button("SOLICITAR ACCESO", use_container_width=True):
                if nu and np:
                    try:
                        conn = get_db(); cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, hash_pass(np)))
                        conn.commit(); st.success("SOLICITUD ENVIADA.")
                    except: st.error("EL USUARIO YA EXISTE.")
                else: st.warning("COMPLETA LOS CAMPOS.")
    st.stop()

# --- SIDEBAR PROFESIONAL ---
st.sidebar.markdown(f"<h2 class='chrome-text'>{st.session_state['u_nom'].upper()}</h2>", unsafe_allow_html=True)
if st.session_state['rango'] == 'ADMIN_GLOBAL':
    menu = st.sidebar.radio("Ir a:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN PERFILES", "💰 FINANZAS PRO", "🗑️ ELIMINAR", "👥 USUARIOS", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])
else:
    menu = st.sidebar.radio("Ir a:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN PERFILES", "💰 FINANZAS PRO", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])

conn = get_db(); uid = st.session_state['u_id']

# ==========================================
# 2. SELECTOR DE MODO (GIGANTES IGUALES v13.8)
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
# 3. PANEL DE HERRAMIENTAS (MOSAICO 3x2 v13.8)
# ==========================================
neg = st.session_state['modo']

if st.session_state['herramienta'] == 'MENU':
    st.markdown(f"<h2 class='chrome-text'>ADMINISTRACIÓN: {neg}</h2>", unsafe_allow_html=True)
    
    # Mosaico 3 columnas x 2 filas, con iconos visibles nítidos
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3502/3502601.png' width='70'></p>", unsafe_allow_html=True)
        if st.button("➕ SUBIR"): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
    with m2:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/869/869121.png' width='70'></p>", unsafe_allow_html=True)
        if st.button("📱 GESTIÓN"): st.session_state['herramienta'] = 'GESTION'; st.rerun()
    with m3:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3119/3119338.png' width='70'></p>", unsafe_allow_html=True)
        if st.button("🔔 COBRANZA"): st.session_state['herramienta'] = 'COBRANZA'; st.rerun()
        
    m4, m5, m6 = st.columns(3)
    with m4:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/2454/2454282.png' width='70'></p>", unsafe_allow_html=True)
        if st.button("💰 FINANZAS"): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
    with m5:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/3221/3221803.png' width='70'></p>", unsafe_allow_html=True)
        if st.button("🗑️ BAJAS"): st.session_state['herramienta'] = 'ELIMINAR'; st.rerun()
    with m6:
        st.markdown("<p align='center'><img src='https://cdn-icons-png.flaticon.com/512/9131/9131529.png' width='70'></p>", unsafe_allow_html=True)
        if st.button("👤 MI CUENTA"): st.session_state['herramienta'] = 'PERFIL'; st.rerun()

    st.write("---")
    if st.button("🔄 CAMBIAR MODO"): st.session_state['modo'] = None; st.rerun()

# ==========================================
# 4. GESTIÓN DE PERFILES (WHATSAPP PRO)
# ==========================================
elif st.session_state['herramienta'] == 'GESTION':
    st.markdown("<h2 class='chrome-text'>GESTIÓN DE VENTAS</h2>", unsafe_allow_html=True)
    if st.button("⬅️ VOLVER AL PANEL"): st.session_state['herramienta'] = 'MENU'; st.rerun()
    
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
                if neg == 'PERFILES':
                    perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c['email']}' AND creador_id={uid}", conn)
                    for _, row in perfs.iterrows():
                        st.markdown(f"<div class='stMetric'><b>{row['estado']}</b> | Perfil: {row['nombre']} | PIN: {row['pin']}</div>", unsafe_allow_html=True)
                        if row['estado'] == 'LIBRE':
                            c1, c2 = st.columns(2)
                            wa = c1.text_input("WhatsApp Cliente:", key=f"wa_{row['id']}")
                            if c2.button("🛒 CONFIRMAR VENTA", key=f"v_{row['id']}", use_container_width=True):
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
                            msg = (f"*ENTREGA - {p_sel}*\n- Correo: {c['email']}\n- Clave: {c['password']}\n- Perfil: {row['nombre']}\n- PIN: {row['pin']}\n- Vence: {row['fecha_vence']}")
                            cb3.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:10px; width:100%;">🚀 WHATSAPP</button></a>', unsafe_allow_html=True)
                else:
                    st.success("CUENTA COMPLETA - LISTA PARA ENTREGA")

# --- MENÚS DE DASHBOARD Y PLATAFORMAS (RESTO DEL CÓDIGO v13.8) ---
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