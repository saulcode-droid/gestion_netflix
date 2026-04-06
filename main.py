import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAÚL STREAMING EXTREME ELITE", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_saul_extreme_v12.db'

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

# --- ESTILOS CSS ULTRA PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #050505; color: #ffffff; }
    
    /* Botones Gigantes de Navegación */
    .stButton>button {
        height: 120px !important;
        font-size: 24px !important;
        font-weight: bold !important;
        border-radius: 20px !important;
        text-transform: uppercase !important;
        margin-bottom: 15px !important;
        border: 2px solid #2d2d2d !important;
        transition: 0.3s !important;
    }
    
    /* Colores por Plataforma */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { border-color: #E50914 !important; } /* Netflix Rojo */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { border-color: #006E99 !important; } /* Disney Azul */
    
    .card-finanzas {
        background: #111;
        padding: 30px;
        border-radius: 20px;
        border-left: 10px solid #00ff00;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(v): return f"S/ {v:,.2f}"
def calcular_dias(f_str):
    try:
        f = datetime.strptime(f_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

# --- NAVEGACIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'step' not in st.session_state: st.session_state['step'] = 'LOGIN'
if 'negocio' not in st.session_state: st.session_state['negocio'] = None
if 'publico' not in st.session_state: st.session_state['publico'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'

# --- LOGIN ---
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png", width=200)
        st.title("🛡️ ACCESO SISTEMA VIP")
        u = st.text_input("USUARIO")
        p = st.text_input("CONTRASEÑA", type="password")
        if st.button("🚀 ENTRAR AL SISTEMA", use_container_width=True):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p):
                st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'step': 'MODO_NEGOCIO'})
                st.rerun()
            else: st.error("DATOS INCORRECTOS")
    st.stop()

conn = get_db(); uid = st.session_state['u_id']

# --- SELECTOR 1: MODO NEGOCIO ---
if st.session_state['step'] == 'MODO_NEGOCIO':
    st.title(f"BIENVENIDO: {st.session_state['u_nom'].upper()}")
    c1, c2 = st.columns(2)
    if c1.button("📱\nADMINISTRAR POR PERFILES", use_container_width=True):
        st.session_state.update({'negocio': 'PERFILES', 'step': 'MODO_PUBLICO'}); st.rerun()
    if c2.button("📧\nADMINISTRAR CUENTAS COMPLETAS", use_container_width=True):
        st.session_state.update({'negocio': 'CUENTAS', 'step': 'MODO_PUBLICO'}); st.rerun()
    if st.button("🚪 SALIR"): st.session_state.clear(); st.rerun()
    st.stop()

# --- SELECTOR 2: PÚBLICO ---
if st.session_state['step'] == 'MODO_PUBLICO':
    st.title(f"MODO: {st.session_state['negocio']}")
    c1, c2 = st.columns(2)
    if c1.button("👥\nCLIENTES FINALES", use_container_width=True):
        st.session_state.update({'publico': 'FINALES', 'step': 'PANEL_CONTROL'}); st.rerun()
    if c2.button("💼\nCOMISIONISTAS", use_container_width=True):
        st.session_state.update({'publico': 'COMISIONISTAS', 'step': 'PANEL_CONTROL'}); st.rerun()
    if st.button("⬅️ VOLVER"): st.session_state['step'] = 'MODO_NEGOCIO'; st.rerun()
    st.stop()

# --- SELECTOR 3: HERRAMIENTAS (MOSAICO) ---
if st.session_state['step'] == 'PANEL_CONTROL':
    neg, pub = st.session_state['negocio'], st.session_state['publico']
    
    if st.session_state['herramienta'] == 'MENU':
        st.title(f"💎 {neg} - {pub}")
        st.write("---")
        
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ SUBIR PLATAFORMA", use_container_width=True): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
        if c2.button("📱 GESTIÓN Y VENTAS", use_container_width=True): st.session_state['herramienta'] = 'GESTION'; st.rerun()
        if c3.button("🔔 COBRANZAS", use_container_width=True): st.session_state['herramienta'] = 'COBRANZA'; st.rerun()
        
        c4, c5, c6 = st.columns(3)
        if c4.button("💰 FINANZAS PRO", use_container_width=True): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
        if c5.button("🗑️ ELIMINAR CUENTAS", use_container_width=True): st.session_state['herramienta'] = 'ELIMINAR'; st.rerun()
        if c6.button("👤 MI CUENTA / SOCIOS", use_container_width=True): st.session_state['herramienta'] = 'USUARIOS'; st.rerun()
        
        if st.button("⬅️ CAMBIAR MODO DE MERCADO"): st.session_state['step'] = 'MODO_PUBLICO'; st.rerun()

    # --- 🛒 SUBIR PLATAFORMA ---
    elif st.session_state['herramienta'] == 'SUBIR':
        st.header("➕ REGISTRO DE CUENTAS")
        if st.button("⬅️ VOLVER AL MENÚ"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        
        modo_subir = st.radio("TIPO DE CARGA:", ["NUEVA CUENTA", "AGREGAR PERFILES A EXISTENTE"], horizontal=True)
        
        if modo_subir == "NUEVA CUENTA":
            with st.form("form_n"):
                c1, c2, c3 = st.columns([2,2,1])
                plat = c1.selectbox("PLATAFORMA", ["NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"])
                mail = c2.text_input("CORREO")
                clv = c1.text_input("CONTRASEÑA")
                cst = c3.number_input("COSTO S/", 0.0)
                venc = st.date_input("VENCE CON PROVEEDOR")
                if st.form_submit_button("🚀 ACTIVAR CUENTA GIGANTE"):
                    try:
                        conn.cursor().execute("INSERT INTO cuentas (tipo_negocio, sub_tipo, plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?,?,?)",
                                             (neg, pub, plat, mail, clv, venc.strftime("%d/%m/%Y"), cst, uid))
                        conn.commit(); st.success("✅ ¡REGISTRADO!"); st.rerun()
                    except: st.error("CORREO YA EXISTE")
        else:
            ctas = pd.read_sql_query(f"SELECT email, plataforma FROM cuentas WHERE creador_id={uid}", conn)
            if not ctas.empty:
                sel = st.selectbox("ELEGIR CUENTA:", ctas['email'].tolist())
                with st.form("add_p"):
                    n_p = st.text_input("NOMBRE PERFIL")
                    p_p = st.text_input("PIN")
                    if st.form_submit_button("➕ AGREGAR PERFIL"):
                        conn.cursor().execute("INSERT INTO perfiles (email, plataforma, nombre, pin, creador_id) VALUES (?,?, ?, ?, ?)",
                                             (sel, ctas[ctas['email']==sel]['plataforma'].iloc[0], n_p, p_p, uid))
                        conn.commit(); st.success("PERFIL AGREGADO"); st.rerun()

    # --- 📱 GESTIÓN Y VENTAS ---
    elif st.session_state['herramienta'] == 'GESTION':
        st.header("📱 PANEL DE VENTAS")
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        
        # Botones de Filtro Grandes
        col_f = st.columns(6)
        plats = ["NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"]
        colors = ["#E50914","#006E99","#FFFFFF","#00A8E1","#FF5A00","#F47521"]
        for i, p in enumerate(plats):
            if col_f[i].button(p): st.session_state['p_sel'] = p
            
        p_sel = st.session_state.get('p_sel', 'NETFLIX')
        st.subheader(f"ADMINISTRANDO: {p_sel}")
        
        ctas = pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)['email'].tolist()
        if ctas:
            target = st.selectbox("CUENTA:", ctas)
            cta_dat = pd.read_sql_query(f"SELECT password FROM cuentas WHERE email='{target}'", conn).iloc[0]
            st.warning(f"🔑 CLAVE MAESTRA: {cta_dat['password']}")
            
            perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{target}'", conn)
            for _, row in perfs.iterrows():
                with st.expander(f"{row['estado']} - {row['nombre']}"):
                    if row['estado'] == 'LIBRE':
                        wa = st.text_input("WHATSAPP CLIENTE:", key=f"w_{row['id']}")
                        pv = st.number_input("PRECIO S/", 10.0, key=f"p_{row['id']}")
                        if st.button("🛒 CONFIRMAR VENTA", key=f"v_{row['id']}", use_container_width=True):
                            fv = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                            fa = datetime.now().strftime("%d/%m/%Y")
                            conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', precio_venta={pv}, fecha_vence='{fv}', fecha_venta='{fa}' WHERE id={row['id']}")
                            conn.commit(); st.rerun()
                    else:
                        st.write(f"📅 VENCE: {row['fecha_vence']}")
                        n_nom = st.text_input("EDITAR NOMBRE", row['nombre'], key=f"en_{row['id']}")
                        n_pin = st.text_input("EDITAR PIN", row['pin'], key=f"ep_{row['id']}")
                        
                        c1, c2, c3 = st.columns(3)
                        if c1.button("💾 ACTUALIZAR", key=f"up_{row['id']}"):
                            conn.cursor().execute(f"UPDATE perfiles SET nombre='{n_nom}', pin='{n_pin}' WHERE id={row['id']}")
                            conn.commit(); st.rerun()
                        if c2.button("🔄 RENOVAR +30D", key=f"rn_{row['id']}"):
                            nueva_v = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                            conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva_v}' WHERE id={row['id']}")
                            conn.commit(); st.rerun()
                        if c3.button("✂️ CORTAR", key=f"ct_{row['id']}"):
                            conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, precio_venta=0 WHERE id={row['id']}")
                            conn.commit(); st.rerun()
                        
                        msg = (f"*ENTREGA - {p_sel}*\n\n- Correo: {target}\n- Clave: {cta_dat['password']}\n- Perfil: {row['nombre']}\n- PIN: {row['pin']}\n- Vence: {row['fecha_vence']}")
                        st.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background:#25D366; color:white; width:100%; border-radius:10px; border:none; padding:15px; font-weight:bold;">🚀 ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)

    # --- 💰 FINANZAS PRO ---
    elif st.session_state['herramienta'] == 'FINANZAS':
        st.header("💰 BALANCE DE GANANCIAS")
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        
        col_f1, col_f2 = st.columns(2)
        ini = col_f1.date_input("DESDE:", datetime.now() - timedelta(days=7))
        fin = col_f2.date_input("HASTA:", datetime.now())
        
        eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
        df_v = pd.read_sql_query(f"SELECT precio_venta, fecha_venta FROM perfiles WHERE creador_id={uid} AND estado='VENDIDO'", conn)
        df_v['fecha_venta'] = pd.to_datetime(df_v['fecha_venta'], format="%d/%m/%Y")
        ventas = df_v[(df_v['fecha_venta'] >= pd.Timestamp(ini)) & (df_v['fecha_venta'] <= pd.Timestamp(fin))]['precio_venta'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📉 EGRESOS", moneda(eg))
        c2.metric("📈 INGRESOS PERIODO", moneda(ventas))
        c3.metric("🤑 GANANCIA", moneda(ventas - eg))

    # --- 🗑️ ELIMINAR ---
    elif st.session_state['herramienta'] == 'ELIMINAR':
        st.header("🗑️ BAJAS")
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        for p in ["NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"]:
            with st.expander(f"CUENTAS {p}"):
                df_d = pd.read_sql_query(f"SELECT id, email FROM cuentas WHERE plataforma='{p}' AND creador_id={uid}", conn)
                for _, r in df_d.iterrows():
                    c1, c2 = st.columns([4,1])
                    c1.write(r['email'])
                    if c2.button("🗑️", key=f"d_{r['id']}"):
                        conn.cursor().execute(f"DELETE FROM cuentas WHERE id={r['id']}"); conn.commit(); st.rerun()

    # --- 👤 USUARIOS / MI CUENTA ---
    elif st.session_state['herramienta'] == 'USUARIOS':
        st.header("👤 MI PERFIL / SOCIOS")
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        
        st.subheader("MIS DATOS")
        st.info(f"USUARIO: {st.session_state['u_nom']} | ID: {uid}")
        
        new_clave = st.text_input("CAMBIAR MI CONTRASEÑA", type="password")
        if st.button("💾 ACTUALIZAR CLAVE"):
            conn.cursor().execute("UPDATE usuarios SET password=? WHERE id=?", (hash_pass(new_clave), uid))
            conn.commit(); st.success("CLAVE ACTUALIZADA")
            
        if st.session_state['u_ran'] == 'ADMIN':
            st.divider()
            st.subheader("APROBAR SOCIOS")
            pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
            for _, r in pends.iterrows():
                c1, c2 = st.columns(2)
                c1.write(r['user'])
                if c2.button("✅ ACTIVAR", key=f"act_{r['id']}"):
                    conn.cursor().execute(f"UPDATE usuarios SET rango='SOCIO' WHERE id={r['id']}")
                    conn.commit(); st.rerun()