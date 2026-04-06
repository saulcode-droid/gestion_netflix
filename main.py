import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# ==========================================
# 1. CAMBIA AQUÍ EL NOMBRE DE TU APLICACIÓN
# ==========================================
NOMBRE_APP = "GESTION DE CUENTAS" 
# ==========================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=NOMBRE_APP, page_icon="🎬", layout="wide")

# --- ESTILOS CSS PARA OCULTAR ICONOS DE STREAMLIT ---
st.markdown("""
    <style>
    /* Ocultar iconos de la parte inferior derecha y menús de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stStatusWidget"] {display: none;}
    .stAppDeployButton {display: none;}
    
    /* Estilos Dark Elite */
    .stApp { background-color: #0b0e14; }
    .card-pro {
        padding: 25px; border-radius: 15px; border: 1px solid #1e2530;
        background: linear-gradient(145deg, #141a24, #0b0e14);
        box-shadow: 5px 5px 15px #05070a, -5px -5px 15px #11171e;
        margin-bottom: 20px;
    }
    .stMetric { background-color: #141a24; padding: 15px; border-radius: 12px; border: 1px solid #1e2530; }
    h1, h2, h3 { text-transform: uppercase; letter-spacing: 1px; color: #ffffff; }
    .stButton>button { border-radius: 8px; font-weight: bold; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_final_v9.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, 
                       fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", ('admin', hash_pass('admin123'), 'ADMIN'))
    conn.commit()

init_db()

# --- UTILIDADES ---
def moneda(valor):
    return f"S/ {valor:,.2f}"

def calcular_dias(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

# --- SISTEMA DE LOGIN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.5, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png", width=180)
        st.markdown("</div>", unsafe_allow_html=True)
        st.title(f"🛡️ {NOMBRE_APP}")
        t_login, t_reg = st.tabs(["INGRESAR", "REGISTRARSE"])
        
        with t_login:
            u = st.text_input("USUARIO", placeholder="Ingrese su usuario")
            p = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")
            if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
                res = cursor.fetchone()
                if res and res[2] == hash_pass(p):
                    if res[1] == 'PENDIENTE': st.warning("CUENTA EN ESPERA.")
                    else:
                        st.session_state['auth'], st.session_state['u_id'], st.session_state['u_nom'], st.session_state['u_ran'] = True, res[0], u, res[1]
                        st.rerun()
                else: st.error("DATOS INCORRECTOS")
            
            if st.button("❓ OLVIDÉ MI CONTRASEÑA", use_container_width=True):
                st.info(f"CONTACTE A SOPORTE PARA RESTABLECER SU CLAVE.")
        
        with t_reg:
            nu = st.text_input("NUEVO USUARIO")
            np = st.text_input("NUEVA CONTRASEÑA", type="password")
            if st.button("📩 SOLICITAR ACCESO", use_container_width=True):
                if nu and np:
                    try:
                        conn = get_db(); cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, hash_pass(np)))
                        conn.commit(); st.success("SOLICITUD ENVIADA.")
                    except: st.error("EL USUARIO YA EXISTE.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state['u_nom'].upper()}")
st.sidebar.subheader(NOMBRE_APP)
menu = st.sidebar.radio("MENÚ PRINCIPAL:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN DE PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "📅 PROVEEDORES", "🗑️ ELIMINAR CUENTAS", "👥 USUARIOS", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])

conn = get_db()
uid = st.session_state['u_id']

# --- LÓGICA DE MENÚS (RESTAURADA) ---
if menu == "🚪 SALIR":
    st.session_state['auth'] = False; st.rerun()

elif menu == "📊 DASHBOARD":
    st.title("📊 Resumen del Negocio")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 CUENTAS", pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0])
    c2.metric("✅ VENDIDOS", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0])
    c3.metric("🔓 LIBRES", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0])
    df = pd.read_sql_query(f"SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.subheader("👥 PRÓXIMOS VENCIMIENTOS")
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True, hide_index=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Nuevas Cuentas")
    plat = st.selectbox("PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    with st.form("f_reg", clear_on_submit=True):
        col1, col2, col3 = st.columns([2,2,1])
        m, p, c = col1.text_input("CORREO"), col2.text_input("CLAVE"), col3.number_input("COSTO (S/)", min_value=0.0)
        f = st.date_input("VENCE PROVEEDOR", format="DD/MM/YYYY")
        per_data = []
        ca, cb = st.columns(2)
        for i in range(PLATAFORMAS_CONFIG[plat]):
            with ca: n = st.text_input(f"Nombre P{i+1}", f"P{i+1}", key=f"n_{i}")
            with cb: pi = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
            per_data.append((n, pi))
        if st.form_submit_button("🚀 ACTIVAR PLATAFORMA"):
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?)", (plat, m, p, f.strftime("%d/%m/%Y"), c, uid))
                for nom, pin in per_data:
                    cur.execute("INSERT INTO perfiles (email, plataforma, nombre, pin, creador_id) VALUES (?,?,?,?,?)", (m, plat, nom, pin, uid))
                conn.commit(); st.success("✅ CUENTA SUBIDA"); st.rerun()
            except: st.error("ERROR AL GUARDAR")

elif menu == "📱 GESTIÓN DE PERFILES":
    st.title("📱 Administración")
    p_sel = st.selectbox("FILTRAR PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    emails = pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)['email'].tolist()
    if emails:
        target = st.selectbox("CUENTA:", emails)
        cta = pd.read_sql_query(f"SELECT password FROM cuentas WHERE email='{target}'", conn).iloc[0]
        st.info(f"🔑 CLAVE: {cta['password']}")
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{target}' AND creador_id={uid}", conn)
        for _, row in perfs.iterrows():
            stat = "🟢" if row['estado'] == 'LIBRE' else "🔴"
            with st.expander(f"{stat} {row['nombre']}"):
                col_i, col_d = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = col_i.text_input("WhatsApp:", key=f"wa_{row['id']}")
                    pv = col_d.number_input("Precio S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("🛒 CONFIRMAR VENTA", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 VENCE: {row['fecha_vence']} ({d} días)")
                    msg = (f"*ENTREGA DE SERVICIO - {row['plataforma']}*\n\n• *Correo:* {target}\n• *Contraseña:* {cta['password']}\n• *Perfil:* {row['nombre']}\n• *PIN:* {row['pin']}\n• *Vencimiento:* {row['fecha_vence']}")
                    st.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; width:100%; border:none; padding:10px; border-radius:10px; cursor:pointer; font-weight:bold;">🚀 ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)
                    st.write("---")
                    c_b1, c_b2 = st.columns(2)
                    if c_b1.button("🔄 RENOVAR (+30D)", key=f"r_{row['id']}"):
                        nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if c_b2.button("✂️ CORTAR", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

elif menu == "💰 FINANZAS PRO":
    st.title("💰 Balance Real")
    eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
    in_g = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0] or 0
    c1, c2, c3 = st.columns(3)
    c1.metric("📉 EGRESOS", moneda(eg))
    c2.metric("📈 INGRESOS", moneda(in_g))
    c3.metric("🤑 GANANCIA", moneda(in_g - eg))
    st.divider()
    res = []
    for p in PLATAFORMAS_CONFIG.keys():
        ep = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE plataforma='{p}' AND creador_id={uid}", conn).iloc[0,0] or 0
        ip = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}' AND creador_id={uid}", conn).iloc[0,0] or 0
        res.append({"PLATAFORMA": p, "EGRESOS": moneda(ep), "INGRESOS": moneda(ip), "GANANCIA": moneda(ip - ep)})
    st.table(pd.DataFrame(res))

elif menu == "🔔 NOTIFICACIONES":
    st.title("🔔 Cobranza")
    df_n = pd.read_sql_query(f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
    if not df_n.empty:
        df_n['DÍAS'] = df_n['fecha_vence'].apply(calcular_dias)
        for _, r in df_n[df_n['DÍAS'] <= 3].sort_values('DÍAS').iterrows():
            col1, col2 = st.columns([3, 1])
            col1.warning(f"⚠️ {r['nombre']} ({r['plataforma']}) vence en {r['DÍAS']} días")
            msg_n = f"Hola {r['nombre']}, recordatorio de renovación. Vence el {r['fecha_vence']}."
            col2.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg_n)}" target="_blank"><button style="background-color:#008CBA; color:white; padding:8px; border:none; border-radius:5px; cursor:pointer; width:100%;">🔔 RECORDAR</button></a>', unsafe_allow_html=True)
            st.divider()

elif menu == "🗑️ ELIMINAR CUENTAS":
    st.title("🗑️ Bajas")
    df_d = pd.read_sql_query(f"SELECT id, plataforma, email FROM cuentas WHERE creador_id={uid}", conn)
    for _, r in df_d.iterrows():
        c1, c2 = st.columns([5,1])
        c1.write(f"📺 {r['plataforma']} | {r['email']}")
        if c2.button("🗑️", key=f"del_{r['id']}"):
            cur = conn.cursor()
            cur.execute(f"DELETE FROM cuentas WHERE id={r['id']}"); cur.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
            conn.commit(); st.rerun()

elif menu == "👥 USUARIOS":
    st.title("👥 Socios")
    if st.session_state['u_ran'] == 'ADMIN':
        pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
        for _, r in pends.iterrows():
            c1, c2 = st.columns([4,1])
            c1.write(f"👤 SOLICITUD: {r['user']}")
            if c2.button("✅", key=f"acc_{r['id']}"):
                conn.cursor().execute(f"UPDATE usuarios SET rango='SOCIO' WHERE id={r['id']}")
                conn.commit(); st.rerun()
        st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)
    else: st.error("SOLO ADMIN")

elif menu == "🔑 CAMBIAR CLAVE":
    st.title("🔑 Seguridad")
    old = st.text_input("CLAVE ACTUAL", type="password")
    new = st.text_input("NUEVA CLAVE", type="password")
    if st.button("ACTUALIZAR"):
        cur = conn.cursor(); cur.execute("SELECT password FROM usuarios WHERE id=?", (uid,))
        if cur.fetchone()[0] == hash_pass(old):
            cur.execute("UPDATE usuarios SET password=? WHERE id=?", (hash_pass(new), uid))
            conn.commit(); st.success("CAMBIADA")

elif menu == "📅 PROVEEDORES":
    st.title("📅 Vencimientos")
    st.dataframe(pd.read_sql_query(f"SELECT plataforma, email, password, fecha_proveedor FROM cuentas WHERE creador_id={uid}", conn), use_container_width=True)