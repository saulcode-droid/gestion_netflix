import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAÚL STREAMING ELITE v14", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_final_v14.db'

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
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN')", (hash_pass('admin123'),))
    conn.commit()

init_db()

# --- ESTILOS CSS ULTRA PROFESIONALES ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #0b0e14; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Centrado General */
    .centered { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
    
    /* Botones Gigantes Neón */
    .stButton>button {
        background-color: #1a1e26 !important;
        color: white !important;
        border: 2px solid #00ff00 !important;
        border-radius: 20px !important;
        padding: 30px !important;
        font-size: 22px !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        width: 100% !important;
        box-shadow: 0 0 15px rgba(0,255,0,0.3) !important;
        transition: 0.4s !important;
    }
    .stButton>button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 30px #00ff00 !important;
        color: #00ff00 !important;
        background-color: #000000 !important;
    }

    /* Iconos Centrados arriba de botones */
    .icon-container { display: flex; justify-content: center; margin-bottom: -15px; }

    /* Titulos Cromados */
    .title-elite {
        font-size: 45px !important;
        font-weight: 900;
        background: linear-gradient(0deg, #888, #fff, #888);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 3px;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- ESTADOS ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'step' not in st.session_state: st.session_state['step'] = 'LOGIN'
if 'modo' not in st.session_state: st.session_state['modo'] = None
if 'publico' not in st.session_state: st.session_state['publico'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'

# ==========================================
# 1. LOGIN (CENTRADO Y PROFESIONAL)
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div class='centered'><img src='https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png' width='220'></div>", unsafe_allow_html=True)
        st.markdown("<h1 class='title-elite' style='text-align:center;'>ACCESS SYSTEM</h1>", unsafe_allow_html=True)
        u = st.text_input("USUARIO", key="u_log")
        p = st.text_input("CONTRASEÑA", type="password", key="p_log")
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("🚀 ENTRAR"):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p):
                st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'step': 'MODO'})
                st.rerun()
            else: st.error("DATOS INCORRECTOS")
        if c2.button("❓ OLVIDÉ"): st.info("CONTACTA AL ADMIN")
    st.stop()

# ==========================================
# 2. SELECTOR DE MODO (BOTONES GRANDES CUADRADOS)
# ==========================================
conn = get_db(); uid = st.session_state['u_id']

if st.session_state['step'] == 'MODO':
    st.markdown(f"<h1 class='title-elite' style='text-align:center;'>BIENVENIDO {st.session_state['u_nom'].upper()}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:20px;'>SELECCIONE EL TIPO DE ADMINISTRACIÓN</p>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/3067/3067260.png' width='110'></div>", unsafe_allow_html=True)
        if st.button("📱 VENTA POR PERFILES", use_container_width=True):
            st.session_state.update({'modo': 'PERFILES', 'step': 'PUBLICO'}); st.rerun()
    with col2:
        st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/5602/5602732.png' width='110'></div>", unsafe_allow_html=True)
        if st.button("📧 CUENTAS COMPLETAS", use_container_width=True):
            st.session_state.update({'modo': 'CUENTAS', 'step': 'PUBLICO'}); st.rerun()
            
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 CERRAR SESIÓN TOTAL"):
        st.session_state.clear(); st.rerun()
    st.stop()

# ==========================================
# 3. SELECTOR PÚBLICO
# ==========================================
if st.session_state['step'] == 'PUBLICO':
    st.markdown(f"<h1 class='title-elite' style='text-align:center;'>MODO: {st.session_state['modo']}</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/2102/2102647.png' width='100'></div>", unsafe_allow_html=True)
        if st.button("👥 CLIENTES FINALES", use_container_width=True):
            st.session_state.update({'publico': 'FINALES', 'step': 'PANEL'}); st.rerun()
    with col2:
        st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/1256/1256650.png' width='100'></div>", unsafe_allow_html=True)
        if st.button("💼 COMISIONISTAS", use_container_width=True):
            st.session_state.update({'publico': 'COMISIONISTAS', 'step': 'PANEL'}); st.rerun()
    if st.button("⬅️ VOLVER AL MODO"): st.session_state['step'] = 'MODO'; st.rerun()
    st.stop()

# ==========================================
# 4. PANEL DE HERRAMIENTAS (MOSAICO 3x2)
# ==========================================
if st.session_state['step'] == 'PANEL':
    modo, pub = st.session_state['modo'], st.session_state['publico']
    
    if st.session_state['herramienta'] == 'MENU':
        st.markdown(f"<h1 class='title-elite' style='text-align:center;'>PANEL {modo} - {pub}</h1>", unsafe_allow_html=True)
        st.write("---")
        
        # Fila 1
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/3502/3502601.png' width='80'></div>", unsafe_allow_html=True)
            if st.button("➕ SUBIR"): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
        with c2:
            st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/869/869121.png' width='80'></div>", unsafe_allow_html=True)
            if st.button("📱 GESTIÓN"): st.session_state['herramienta'] = 'GESTION'; st.rerun()
        with c3:
            st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/3119/3119338.png' width='80'></div>", unsafe_allow_html=True)
            if st.button("🔔 COBRANZA"): st.session_state['herramienta'] = 'COBRANZA'; st.rerun()
            
        # Fila 2
        c4, c5, c6 = st.columns(3)
        with c4:
            st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/2454/2454282.png' width='80'></div>", unsafe_allow_html=True)
            if st.button("💰 FINANZAS"): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
        with c5:
            st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/3221/3221803.png' width='80'></div>", unsafe_allow_html=True)
            if st.button("🗑️ BAJAS"): st.session_state['herramienta'] = 'ELIMINAR'; st.rerun()
        with c6:
            st.markdown("<div class='icon-container'><img src='https://cdn-icons-png.flaticon.com/512/9131/9131529.png' width='80'></div>", unsafe_allow_html=True)
            if st.button("👤 PERFIL"): st.session_state['herramienta'] = 'USUARIOS'; st.rerun()

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("⬅️ CAMBIAR MERCADO"): st.session_state['step'] = 'PUBLICO'; st.rerun()

    # --- SUBIR PLATAFORMA ---
    elif st.session_state['herramienta'] == 'SUBIR':
        if st.button("⬅️ VOLVER AL PANEL"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.markdown("<h2 class='title-elite'>SUBIR CUENTA</h2>", unsafe_allow_html=True)
        
        acc = st.radio("ACCION:", ["NUEVA CUENTA", "AGREGAR PERFILES A EXISTENTE"], horizontal=True)
        
        if acc == "NUEVA CUENTA":
            with st.form("form_n"):
                c1, c2 = st.columns(2)
                plat = c1.selectbox("PLATAFORMA", ["NETFLIX","PRIME","MAX","DISNEY","VIX","CRUNCHY"])
                mail = c2.text_input("CORREO")
                clv = c1.text_input("CLAVE")
                cst = c2.number_input("COSTO S/", 0.0)
                venc = st.date_input("FECHA VENCIMIENTO PROVEEDOR")
                if st.form_submit_button("🚀 ACTIVAR MAESTRA"):
                    try:
                        conn.cursor().execute("INSERT INTO cuentas (tipo_negocio, sub_tipo, plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?,?,?)",
                                             (modo, pub, plat, mail, clv, venc.strftime("%d/%m/%Y"), cst, uid))
                        conn.commit(); st.success("¡SUBIDA EXITOSA!"); st.rerun()
                    except: st.error("CORREO REPETIDO")
        else:
            df_exist = pd.read_sql_query(f"SELECT email FROM cuentas WHERE creador_id={uid} AND tipo_negocio='{modo}'", conn)
            if not df_exist.empty:
                mail_sel = st.selectbox("CUENTA:", df_exist['email'].tolist())
                with st.form("form_p"):
                    n_p = st.text_input("NOMBRE PERFIL")
                    p_p = st.text_input("PIN")
                    if st.form_submit_button("➕ AGREGAR PERFIL"):
                        conn.cursor().execute("INSERT INTO perfiles (email, nombre, pin, creador_id) VALUES (?,?,?,?)", (mail_sel, n_p, p_p, uid))
                        conn.commit(); st.success("PERFIL AGREGADO")

    # --- GESTIÓN DE VENTAS ---
    elif st.session_state['herramienta'] == 'GESTION':
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.markdown("<h2 class='title-elite'>GESTIÓN POR PLATAFORMA</h2>", unsafe_allow_html=True)
        
        col_p = st.columns(6)
        plats = [("NETFLIX","#E50914"), ("PRIME","#00A8E1"), ("MAX","#7B2CBF"), ("DISNEY","#006E99"), ("VIX","#FF5A00"), ("CRUNCHY","#F47521")]
        for i, (n, c) in enumerate(plats):
            if col_p[i].button(n, key=f"btn_{n}"): st.session_state['p_sel'] = n
        
        p_sel = st.session_state.get('p_sel', 'NETFLIX')
        st.info(f"GESTIONANDO: {p_sel}")
        
        ctas = pd.read_sql_query(f"SELECT email, password FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid} AND sub_tipo='{pub}'", conn)
        if not ctas.empty:
            for _, c_row in ctas.iterrows():
                with st.expander(f"📧 {c_row['email']}"):
                    st.code(f"CLAVE: {c_row['password']}")
                    if modo == 'PERFILES':
                        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c_row['email']}'", conn)
                        for _, r in perfs.iterrows():
                            st.write(f"**{r['estado']}** - {r['nombre']} (PIN: {r['pin']})")
                            if r['estado'] == 'LIBRE':
                                c1, c2 = st.columns(2)
                                wa = c1.text_input("WhatsApp", key=f"w_{r['id']}")
                                pv = c2.number_input("Precio S/", 10.0, key=f"p_{r['id']}")
                                if st.button("🛒 VENDER", key=f"v_{r['id']}"):
                                    fv = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                    conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', precio_venta={pv}, fecha_vence='{fv}', fecha_venta='{datetime.now().strftime('%d/%m/%Y')}' WHERE id={r['id']}")
                                    conn.commit(); st.rerun()
                            else:
                                st.write(f"📅 Vence: {r['fecha_vence']}")
                                c1, c2, c3 = st.columns(3)
                                if c1.button("🔄 RENOVAR", key=f"r_{r['id']}"):
                                    nv = (datetime.strptime(r['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                                    conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nv}' WHERE id={r['id']}")
                                    conn.commit(); st.rerun()
                                if c2.button("✂️ CORTAR", key=f"c_{r['id']}"):
                                    conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, precio_venta=0 WHERE id={r['id']}")
                                    conn.commit(); st.rerun()
                                msg = f"*ENTREGA - {p_sel}*\n- Correo: {c_row['email']}\n- Perfil: {r['nombre']}\n- PIN: {r['pin']}"
                                c3.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background:#25D366; color:white; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer; width:100%;">🚀 WHATSAPP</button></a>', unsafe_allow_html=True)

    # --- FINANZAS CON FILTRO ---
    elif st.session_state['herramienta'] == 'FINANZAS':
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.markdown("<h2 class='title-elite'>REPORTE FINANCIERO</h2>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        ini = col1.date_input("INICIO", datetime.now() - timedelta(days=7))
        fin = col2.date_input("FIN", datetime.now())
        
        eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
        df_v = pd.read_sql_query(f"SELECT precio_venta, fecha_venta FROM perfiles WHERE creador_id={uid} AND estado='VENDIDO'", conn)
        df_v['fecha_venta'] = pd.to_datetime(df_v['fecha_venta'], format="%d/%m/%Y", errors='coerce')
        ventas = df_v[(df_v['fecha_venta'] >= pd.Timestamp(ini)) & (df_v['fecha_venta'] <= pd.Timestamp(fin))]['precio_venta'].sum()
        
        st.markdown(f"### BALANCE EN SOLES PERUANOS (S/)")
        c1, c2, c3 = st.columns(3)
        c1.metric("📉 EGRESOS TOTALES", f"S/ {eg:,.2f}")
        c2.metric("📈 INGRESOS PERIODO", f"S/ {ventas:,.2f}")
        c3.metric("🤑 GANANCIA", f"S/ {(ventas - eg):,.2f}")

    # --- OTROS MÓDULOS (BAJAS, USUARIOS, COBRANZA) ---
    elif st.session_state['herramienta'] in ['COBRANZA', 'ELIMINAR', 'USUARIOS']:
        if st.button("⬅️ VOLVER AL PANEL"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.write(f"Módulo {st.session_state['herramienta']} activado correctamente.")