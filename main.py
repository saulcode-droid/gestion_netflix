import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAÚL STREAMING ULTIMATE V13", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_ultra_v13.db'

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
                      (id INTEGER PRIMARY KEY, email TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER, fecha_venta TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN')", (hash_pass('admin123'),))
    conn.commit()

init_db()

# --- ESTILOS CSS PROFESIONALES ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #0d1117; color: white; }
    
    /* Botones de Mosaico Grandes con Imágenes */
    .stButton>button {
        border-radius: 15px !important;
        font-weight: bold !important;
        transition: 0.3s !important;
    }
    
    /* Botones de Navegación Gigantes */
    .big-btn button { height: 150px !important; font-size: 20px !important; }
    
    /* Botones de Salida Pequeños */
    .small-btn button { height: 40px !important; font-size: 14px !important; border-radius: 8px !important; }

    /* Estilo de Tarjetas de Perfil */
    .card-pro { background: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #30363d; margin-bottom: 10px; }
    
    /* Input de Login centrado */
    .login-box { max-width: 400px; margin: 0 auto; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(v): return f"S/ {v:,.2f}"
def calcular_dias(f_str):
    try:
        f = datetime.strptime(f_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

# --- ESTADO DE SESIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'step' not in st.session_state: st.session_state['step'] = 'LOGIN'
if 'negocio' not in st.session_state: st.session_state['negocio'] = None
if 'publico' not in st.session_state: st.session_state['publico'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'
if 'p_sel' not in st.session_state: st.session_state['p_sel'] = 'NETFLIX'

# ==========================================
# 1. LOGIN PROFESIONAL
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'><img src='https://cdn-icons-png.flaticon.com/512/924/924915.png' width='100'></div>", unsafe_allow_html=True)
        st.title("SISTEMA ELITE")
        u = st.text_input("USUARIO")
        p = st.text_input("CONTRASEÑA", type="password")
        c1, c2 = st.columns(2)
        if c1.button("🚀 ENTRAR", use_container_width=True):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p):
                st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'step': 'MODO_NEGOCIO'})
                st.rerun()
            else: st.error("ERROR DE ACCESO")
        if c2.button("❓ OLVIDÉ CLAVE", use_container_width=True):
            st.info("CONTACTE A SAÚL PARA RESTABLECER")
    st.stop()

conn = get_db(); uid = st.session_state['u_id']

# ==========================================
# 2. SELECTOR MODO (GIGANTE CON IMÁGENES)
# ==========================================
if st.session_state['step'] == 'MODO_NEGOCIO':
    st.title(f"BIENVENIDO, {st.session_state['u_nom'].upper()}")
    c1, c2 = st.columns(2)
    with c1:
        st.image("https://img.freepik.com/vector-premium/ilustracion-vector-concepto-abstracto-servicio-transmision-video_107173-25547.jpg", use_container_width=True)
        if st.button("📱 VENTA POR PERFILES", key="btn_perf", use_container_width=True):
            st.session_state.update({'negocio': 'PERFILES', 'step': 'MODO_PUBLICO'}); st.rerun()
    with c2:
        st.image("https://img.freepik.com/vector-premium/acceso-seguro-al-correo-electronico-ilustracion-vector-concepto-abstracto-inicio-sesion-usuario_107173-25530.jpg", use_container_width=True)
        if st.button("📧 CUENTAS COMPLETAS", key="btn_ctas", use_container_width=True):
            st.session_state.update({'negocio': 'CUENTAS', 'step': 'MODO_PUBLICO'}); st.rerun()
    
    st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
    if st.button("🚪 CERRAR SESIÓN"): st.session_state.clear(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 3. SELECTOR PÚBLICO (GIGANTE CON IMÁGENES)
# ==========================================
if st.session_state['step'] == 'MODO_PUBLICO':
    st.title(f"MODO: {st.session_state['negocio']}")
    c1, c2 = st.columns(2)
    with c1:
        st.image("https://img.freepik.com/vector-premium/ilustracion-vector-concepto-abstracto-cliente-satisfecho_107173-25515.jpg", use_container_width=True)
        if st.button("👥 CLIENTES FINALES", use_container_width=True):
            st.session_state.update({'publico': 'FINALES', 'step': 'PANEL_CONTROL'}); st.rerun()
    with c2:
        st.image("https://img.freepik.com/vector-premium/ilustracion-vector-concepto-abstracto-programa-afiliados_107173-25531.jpg", use_container_width=True)
        if st.button("💼 COMISIONISTAS", use_container_width=True):
            st.session_state.update({'publico': 'COMISIONISTAS', 'step': 'PANEL_CONTROL'}); st.rerun()
    
    st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
    if st.button("⬅️ VOLVER AL INICIO"): st.session_state['step'] = 'MODO_NEGOCIO'; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. PANEL CENTRAL (MOSAICO PROFESIONAL)
# ==========================================
neg, pub = st.session_state['negocio'], st.session_state['publico']

if st.session_state['step'] == 'PANEL_CONTROL':
    if st.session_state['herramienta'] == 'MENU':
        st.title(f"💎 {neg} | {pub}")
        st.write("---")
        
        # Mosaico con Imágenes Pequeñas e Iconos
        m1, m2, m3 = st.columns(3)
        with m1:
            st.image("https://cdn-icons-png.flaticon.com/512/3502/3502601.png", width=80)
            if st.button("➕ SUBIR PLATAFORMA", use_container_width=True): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
        with m2:
            st.image("https://cdn-icons-png.flaticon.com/512/869/869121.png", width=80)
            if st.button("📱 GESTIÓN Y VENTAS", use_container_width=True): st.session_state['herramienta'] = 'GESTION'; st.rerun()
        with m3:
            st.image("https://cdn-icons-png.flaticon.com/512/3119/3119338.png", width=80)
            if st.button("🔔 COBRANZAS", use_container_width=True): st.session_state['herramienta'] = 'COBRANZA'; st.rerun()
            
        m4, m5, m6 = st.columns(3)
        with m4:
            st.image("https://cdn-icons-png.flaticon.com/512/2454/2454282.png", width=80)
            if st.button("💰 FINANZAS PRO", use_container_width=True): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
        with m5:
            st.image("https://cdn-icons-png.flaticon.com/512/3221/3221803.png", width=80)
            if st.button("🗑️ ELIMINAR", use_container_width=True): st.session_state['herramienta'] = 'ELIMINAR'; st.rerun()
        with m6:
            st.image("https://cdn-icons-png.flaticon.com/512/9131/9131529.png", width=80)
            if st.button("👤 MI CUENTA", use_container_width=True): st.session_state['herramienta'] = 'USUARIOS'; st.rerun()

        st.markdown("<div class='small-btn' style='margin-top:50px;'>", unsafe_allow_html=True)
        if st.button("⬅️ CAMBIAR MERCADO"): st.session_state['step'] = 'MODO_PUBLICO'; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- HERRAMIENTA: SUBIR ---
    elif st.session_state['herramienta'] == 'SUBIR':
        st.header("🛒 REGISTRO DE CUENTAS")
        if st.button("⬅️ VOLVER AL PANEL"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        
        with st.form("f_reg"):
            c1, c2 = st.columns(2)
            plat = c1.selectbox("PLATAFORMA", ["NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"])
            mail = c2.text_input("CORREO")
            clv = c1.text_input("CLAVE")
            cst = c2.number_input("COSTO PROVEEDOR S/", 0.0)
            venc = st.date_input("VENCE PROVEEDOR")
            
            if st.form_submit_button("🚀 GUARDAR CUENTA MAESTRA"):
                try:
                    conn.cursor().execute("INSERT INTO cuentas (tipo_negocio, sub_tipo, plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?,?,?)",
                                         (neg, pub, plat, mail, clv, venc.strftime("%d/%m/%Y"), cst, uid))
                    conn.commit(); st.success("✅ CUENTA REGISTRADA"); st.rerun()
                except: st.error("ERROR: CORREO DUPLICADO")
        
        if neg == 'PERFILES':
            st.subheader("➕ AGREGAR PERFILES A CUENTA EXISTENTE")
            ctas_dispo = pd.read_sql_query(f"SELECT email FROM cuentas WHERE creador_id={uid}", conn)['email'].tolist()
            if ctas_dispo:
                target_add = st.selectbox("ELEGIR CUENTA", ctas_dispo)
                with st.form("add_per"):
                    n_p = st.text_input("NOMBRE PERFIL")
                    p_p = st.text_input("PIN")
                    if st.form_submit_button("➕ AGREGAR"):
                        conn.cursor().execute("INSERT INTO perfiles (email, nombre, pin, creador_id) VALUES (?,?,?,?)", (target_add, n_p, p_p, uid))
                        conn.commit(); st.success("PERFIL AGREGADO")
    
    # --- HERRAMIENTA: GESTION ---
    elif st.session_state['herramienta'] == 'GESTION':
        st.header("📱 PANEL DE VENTAS")
        if st.button("⬅️ VOLVER AL PANEL"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        
        # Selector por Botones de Colores
        cols = st.columns(6)
        plats = [("NETFLIX","#E50914"), ("DISNEY","#006E99"), ("MAX","#FFFFFF"), ("PRIME","#00A8E1"), ("VIX","#FF5A00"), ("CRUNCHY","#F47521")]
        for i, (name, color) in enumerate(plats):
            if cols[i].markdown(f'<button style="background:{color}; color:{"black" if name=="MAX" else "white"}; border:none; width:100%; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer;">{name}</button>', unsafe_allow_html=True):
                # Usamos un hack de Streamlit para detectar el click
                if st.button(f"SELECCIONAR {name}", key=f"sel_{name}"): st.session_state['p_sel'] = name
        
        st.subheader(f"PLATAFORMA: {st.session_state['p_sel']}")
        df_ctas = pd.read_sql_query(f"SELECT email, password FROM cuentas WHERE plataforma='{st.session_state['p_sel']}' AND creador_id={uid} AND sub_tipo='{pub}'", conn)
        
        if not df_ctas.empty:
            for _, c in df_ctas.iterrows():
                st.info(f"📧 CUENTA: {c['email']} | 🔑 CLAVE: {c['password']}")
                if neg == 'PERFILES':
                    perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c['email']}'", conn)
                    for _, row in perfs.iterrows():
                        with st.container():
                            st.markdown(f"<div class='card-pro'><b>{row['estado']}</b> - Perfil: {row['nombre']}</div>", unsafe_allow_html=True)
                            if row['estado'] == 'LIBRE':
                                c1, c2 = st.columns(2)
                                wa = c1.text_input("WhatsApp", key=f"wa_{row['id']}")
                                pv = c2.number_input("Precio", 10.0, key=f"pv_{row['id']}")
                                if st.button("🛒 VENDER", key=f"v_{row['id']}"):
                                    fv = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                    conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', precio_venta={pv}, fecha_vence='{fv}', fecha_venta='{datetime.now().strftime('%d/%m/%Y')}' WHERE id={row['id']}")
                                    conn.commit(); st.rerun()
                            else:
                                c1, c2, c3 = st.columns(3)
                                # BOTONES GRANDES Y PRECISOS
                                if c1.button("🔄 RENOVAR", key=f"r_{row['id']}", use_container_width=True):
                                    fv_n = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                                    conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{fv_n}' WHERE id={row['id']}")
                                    conn.commit(); st.success("RENOVADO"); st.rerun()
                                if c2.button("✂️ CORTAR", key=f"ct_{row['id']}", use_container_width=True):
                                    conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, precio_venta=0 WHERE id={row['id']}")
                                    conn.commit(); st.rerun()
                                msg = f"*ENTREGA - {st.session_state['p_sel']}*\n- Correo: {c['email']}\n- Clave: {c['password']}\n- Perfil: {row['nombre']}\n- PIN: {row['pin']}"
                                c3.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background:#25D366; color:white; width:100%; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer;">🚀 WHATSAPP</button></a>', unsafe_allow_html=True)
                else:
                    st.success("CUENTA COMPLETA - LISTA PARA ENTREGA")

    # --- HERRAMIENTA: COBRANZA ---
    elif st.session_state['herramienta'] == 'COBRANZA':
        st.header("🔔 CENTRAL DE COBRANZA")
        if st.button("⬅️ VOLVER AL PANEL"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        df_cob = pd.read_sql_query(f"SELECT p.*, c.plataforma FROM perfiles p JOIN cuentas c ON p.email = c.email WHERE p.estado='VENDIDO' AND p.creador_id={uid}", conn)
        if not df_cob.empty:
            df_cob['dias'] = df_cob['fecha_vence'].apply(calcular_dias)
            for _, r in df_cob.sort_values('dias').iterrows():
                with st.container():
                    st.markdown(f"<div class='card-pro'>🚨 {r['plataforma']} | {r['nombre']} - Vence en {r['dias']} días</div>", unsafe_allow_html=True)
                    if st.button(f"🔔 AVISAR A {r['nombre']}", key=f"av_{r['id']}"):
                        st.info("MENSAJE ENVIADO (Simulado)")
        else: st.success("SIN PENDIENTES")

    # --- HERRAMIENTA: FINANZAS ---
    elif st.session_state['herramienta'] == 'FINANZAS':
        st.header("💰 BALANCE FINANCIERO")
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        col1, col2 = st.columns(2)
        ini = col1.date_input("FECHA INICIO", datetime.now() - timedelta(days=7))
        fin = col2.date_input("FECHA FIN", datetime.now())
        
        eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
        df_v = pd.read_sql_query(f"SELECT * FROM perfiles WHERE creador_id={uid} AND estado='VENDIDO'", conn)
        df_v['fecha_venta'] = pd.to_datetime(df_v['fecha_venta'], format="%d/%m/%Y")
        ventas = df_v[(df_v['fecha_venta'] >= pd.Timestamp(ini)) & (df_v['fecha_venta'] <= pd.Timestamp(fin))]['precio_venta'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📉 EGRESOS", moneda(eg))
        c2.metric("📈 INGRESOS", moneda(ventas))
        c3.metric("🤑 GANANCIA", moneda(ventas - eg))

    # --- HERRAMIENTA: ELIMINAR ---
    elif st.session_state['herramienta'] == 'ELIMINAR':
        st.header("🗑️ ELIMINAR CUENTAS")
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        df_d = pd.read_sql_query(f"SELECT id, plataforma, email FROM cuentas WHERE creador_id={uid}", conn)
        for _, r in df_d.iterrows():
            c1, c2 = st.columns([5,1])
            c1.write(f"{r['plataforma']} | {r['email']}")
            if c2.button("🗑️", key=f"d_{r['id']}"):
                conn.cursor().execute(f"DELETE FROM cuentas WHERE id={r['id']}"); conn.commit(); st.rerun()

    # --- HERRAMIENTA: MI CUENTA ---
    elif st.session_state['herramienta'] == 'USUARIOS':
        st.header("👤 MI PERFIL")
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.info(f"USUARIO: {st.session_state['u_nom']} | RANGO: {st.session_state['u_ran']}")
        if st.button("CAMBIAR MI CLAVE"):
            st.text_input("NUEVA CLAVE", type="password")