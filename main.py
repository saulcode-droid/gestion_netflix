import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SAÚL STREAMING ENTERPRISE", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_enterprise_v10.db'

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
                       precio_venta REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", ('admin', hash_pass('admin123'), 'ADMIN'))
    conn.commit()

init_db()

# --- ESTILOS CSS PROFESIONALES ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #0b0e14; }
    
    /* Botones de Mosaico */
    .menu-card {
        background: linear-gradient(145deg, #1e2530, #141a24);
        border: 1px solid #2d3748;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        transition: 0.3s;
        cursor: pointer;
        margin-bottom: 20px;
    }
    .menu-card:hover { border-color: #00ff00; transform: translateY(-5px); }
    
    /* Botón Volver */
    .stButton>button { border-radius: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(v): return f"S/ {v:,.2f}"

# --- GESTIÓN DE SESIÓN Y NAVEGACIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'step' not in st.session_state: st.session_state['step'] = 'LOGIN'
if 'negocio' not in st.session_state: st.session_state['negocio'] = None # PERFILES / CUENTAS
if 'publico' not in st.session_state: st.session_state['publico'] = None # FINALES / COMISIONISTAS
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'

# --- 1. LOGIN ---
if st.session_state['step'] == 'LOGIN' and not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.5, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'><img src='https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png' width='150'></div>", unsafe_allow_html=True)
        st.title("🛡️ ACCESO SISTEMA VIP")
        t1, t2 = st.tabs(["INGRESAR", "REGISTRARSE"])
        with t1:
            u = st.text_input("USUARIO")
            p = st.text_input("CONTRASEÑA", type="password")
            if st.button("🚀 ENTRAR", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
                res = cursor.fetchone()
                if res and res[2] == hash_pass(p):
                    st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'step': 'MODO_NEGOCIO'})
                    st.rerun()
                else: st.error("DATOS INCORRECTOS")
    st.stop()

# --- 2. SELECTOR MODO NEGOCIO ---
if st.session_state['step'] == 'MODO_NEGOCIO':
    st.title(f"BIENVENIDO, {st.session_state['u_nom'].upper()}")
    st.subheader("Selecciona el tipo de administración:")
    c1, c2 = st.columns(2)
    if c1.button("📱\n\nADMINISTRAR POR PERFILES", use_container_width=True, help="Venta de pantallas"):
        st.session_state.update({'negocio': 'PERFILES', 'step': 'MODO_PUBLICO'}); st.rerun()
    if c2.button("📧\n\nADMINISTRAR CUENTAS COMPLETAS", use_container_width=True, help="Venta de correos completos"):
        st.session_state.update({'negocio': 'CUENTAS', 'step': 'MODO_PUBLICO'}); st.rerun()
    if st.button("🚪 SALIR"): st.session_state.clear(); st.rerun()
    st.stop()

# --- 3. SELECTOR PÚBLICO ---
if st.session_state['step'] == 'MODO_PUBLICO':
    st.title(f"MODO: {st.session_state['negocio']}")
    st.subheader("Selecciona tu mercado:")
    c1, c2 = st.columns(2)
    if c1.button("👥\n\nCLIENTES FINALES", use_container_width=True):
        st.session_state.update({'publico': 'FINALES', 'step': 'PANEL_CONTROL'}); st.rerun()
    if c2.button("💼\n\nCOMISIONISTAS / REVENDEDORES", use_container_width=True):
        st.session_state.update({'publico': 'COMISIONISTAS', 'step': 'PANEL_CONTROL'}); st.rerun()
    if st.button("⬅️ VOLVER"): st.session_state['step'] = 'MODO_NEGOCIO'; st.rerun()
    st.stop()

# --- 4. PANEL DE CONTROL (MOSAICO) ---
conn = get_db(); uid = st.session_state['u_id']
neg = st.session_state['negocio']
pub = st.session_state['publico']

if st.session_state['step'] == 'PANEL_CONTROL':
    if st.session_state['herramienta'] == 'MENU':
        st.title(f"💎 {neg} - {pub}")
        st.write("---")
        
        # Mosaico de Herramientas
        cols = st.columns(3)
        with cols[0]:
            if st.button("➕ SUBIR PLATAFORMA\n(Carrito)", use_container_width=True): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
        with cols[1]:
            if st.button("📱 GESTIÓN Y VENTAS\n(Móvil)", use_container_width=True): st.session_state['herramienta'] = 'GESTION'; st.rerun()
        with cols[2]:
            if st.button("🔔 COBRANZAS\n(Campana)", use_container_width=True): st.session_state['herramienta'] = 'NOTIFICAR'; st.rerun()
        
        cols2 = st.columns(3)
        with cols2[0]:
            if st.button("💰 FINANZAS PRO\n(Bolsa)", use_container_width=True): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
        with cols2[1]:
            if st.button("🗑️ BAJAS / ELIMINAR\n(Papelera)", use_container_width=True): st.session_state['herramienta'] = 'ELIMINAR'; st.rerun()
        with cols2[2]:
            if st.button("👥 USUARIOS\n(Persona)", use_container_width=True): st.session_state['herramienta'] = 'USUARIOS'; st.rerun()
            
        st.write("---")
        if st.button("⬅️ CAMBIAR MODO DE MERCADO"): st.session_state['step'] = 'MODO_PUBLICO'; st.rerun()

    # --- HERRAMIENTA: SUBIR PLATAFORMA ---
    elif st.session_state['herramienta'] == 'SUBIR':
        if st.button("⬅️ VOLVER AL MENÚ"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("➕ Registrar Nueva Cuenta")
        
        with st.form("form_reg"):
            c1, c2, c3 = st.columns([2,2,1])
            plat = c1.selectbox("Plataforma", ["NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"])
            mail = c2.text_input("Correo")
            pasw = c1.text_input("Clave")
            cost = c3.number_input("Costo S/", 0.0)
            venc = c2.date_input("Vence con Proveedor")
            
            per_list = []
            if neg == 'PERFILES':
                st.write("---")
                st.subheader("👥 Configuración de Perfiles")
                # Lógica dinámica: Guardamos perfiles en una lista temporal en session_state
                if 'temp_perfiles' not in st.session_state: st.session_state.temp_perfiles = [{"n": "P1", "p": "0000"}]
                
                for i, p in enumerate(st.session_state.temp_perfiles):
                    ca, cb = st.columns(2)
                    p['n'] = ca.text_input(f"Nombre Perfil {i+1}", p['n'], key=f"nom_{i}")
                    p['p'] = cb.text_input(f"PIN Perfil {i+1}", p['p'], key=f"pin_{i}")

            if st.form_submit_button("🚀 GUARDAR TODO"):
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO cuentas (tipo_negocio, sub_tipo, plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?,?,?)",
                                (neg, pub, plat, mail, pasw, venc.strftime("%d/%m/%Y"), cost, uid))
                    if neg == 'PERFILES':
                        for p in st.session_state.temp_perfiles:
                            cur.execute("INSERT INTO perfiles (email, nombre, pin, creador_id) VALUES (?,?,?,?)", (mail, p['n'], p['p'], uid))
                    conn.commit(); st.success("✅ REGISTRADO"); st.session_state.temp_perfiles = [{"n": "P1", "p": "0000"}]; st.rerun()
                except: st.error("ERROR: CORREO DUPLICADO")
        
        if neg == 'PERFILES':
            if st.button("➕ AGREGAR OTRO PERFIL"):
                st.session_state.temp_perfiles.append({"n": f"P{len(st.session_state.temp_perfiles)+1}", "p": "0000"})
                st.rerun()

    # --- HERRAMIENTA: GESTIÓN Y VENTAS ---
    elif st.session_state['herramienta'] == 'GESTION':
        if st.button("⬅️ VOLVER AL MENÚ"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("📱 Administración de Ventas")
        
        query = f"SELECT email, plataforma FROM cuentas WHERE tipo_negocio='{neg}' AND sub_tipo='{pub}' AND creador_id={uid}"
        ctas = pd.read_sql_query(query, conn)
        
        if not ctas.empty:
            sel_cta = st.selectbox("Seleccionar Cuenta", ctas['email'].tolist())
            datos_cta = pd.read_sql_query(f"SELECT * FROM cuentas WHERE email='{sel_cta}'", conn).iloc[0]
            
            if neg == 'PERFILES':
                perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_cta}'", conn)
                for _, row in perfs.iterrows():
                    with st.expander(f"{row['estado']} - {row['nombre']} (PIN: {row['pin']})"):
                        if row['estado'] == 'LIBRE':
                            wa = st.text_input("WhatsApp Cliente", key=f"w_{row['id']}")
                            pre = st.number_input("Precio Venta", 10.0, key=f"p_{row['id']}")
                            if st.button("🛒 VENDER", key=f"b_{row['id']}"):
                                fv = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', precio_venta={pre}, fecha_vence='{fv}' WHERE id={row['id']}")
                                conn.commit(); st.rerun()
                        else:
                            st.write(f"Vence: {row['fecha_vence']}")
                            # Botones Editar Perfil
                            new_n = st.text_input("Editar Nombre", row['nombre'], key=f"en_{row['id']}")
                            new_p = st.text_input("Editar PIN", row['pin'], key=f"ep_{row['id']}")
                            if st.button("💾 GUARDAR CAMBIOS", key=f"sv_{row['id']}"):
                                conn.cursor().execute(f"UPDATE perfiles SET nombre='{new_n}', pin='{new_p}' WHERE id={row['id']}")
                                conn.commit(); st.success("Actualizado"); st.rerun()
                            
                            if st.button("✂️ CORTAR", key=f"c_{row['id']}"):
                                conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, precio_venta=0 WHERE id={row['id']}")
                                conn.commit(); st.rerun()
            else:
                st.info(f"CLAVE: {datos_cta['password']}")
                st.write("Modo Cuenta Completa: Gestión directa de entrega.")

    # --- HERRAMIENTA: FINANZAS PRO ---
    elif st.session_state['herramienta'] == 'FINANZAS':
        if st.button("⬅️ VOLVER AL MENÚ"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("💰 Balance Real")
        eg = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE tipo_negocio='{neg}' AND sub_tipo='{pub}' AND creador_id={uid}", conn)['t'][0] or 0
        in_g = pd.read_sql_query(f"SELECT SUM(precio_venta) as t FROM perfiles WHERE creador_id={uid}", conn)['t'][0] or 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📉 EGRESOS", moneda(eg))
        c2.metric("📈 INGRESOS", moneda(in_g))
        c3.metric("🤑 GANANCIA", moneda(in_g - eg))
        st.divider()
        st.write("Resumen detallado por plataforma activo.")

    # --- (Resto de herramientas: Usuarios, Notificar, Eliminar con la misma lógica de Volver) ---
    else:
        if st.button("⬅️ VOLVER AL MENÚ"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.write("Esta sección está siendo procesada con el nuevo diseño...")