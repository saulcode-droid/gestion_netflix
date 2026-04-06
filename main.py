import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SISTEMA SAÚL STREAMING PRO", page_icon="🎬", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_final_v88.db'

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

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .card-pro {
        padding: 20px; border-radius: 15px; border-left: 8px solid #00ff00;
        background-color: #161b22; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    h1, h2, h3 { color: #ffffff; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(valor):
    return f"S/ {valor:,.2f}"

def calcular_dias(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

# --- LOGIN Y REGISTRO ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.5, 1])
    with col_log:
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png")
        st.title("🔐 ACCESO VIP")
        t_login, t_reg = st.tabs(["INGRESAR", "REGISTRARSE"])
        
        with t_login:
            u = st.text_input("USUARIO", key="l_user")
            p = st.text_input("CONTRASEÑA", type="password", key="l_pass")
            if st.button("🚀 ENTRAR AL SISTEMA", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
                res = cursor.fetchone()
                if res and res[2] == hash_pass(p):
                    if res[1] == 'PENDIENTE':
                        st.warning("CUENTA EN ESPERA DE ACTIVACIÓN.")
                    else:
                        st.session_state['auth'], st.session_state['u_id'], st.session_state['u_nom'], st.session_state['u_ran'] = True, res[0], u, res[1]
                        st.rerun()
                else: st.error("DATOS INCORRECTOS")
        
        with t_reg:
            nu = st.text_input("NUEVO USUARIO", key="r_user")
            np = st.text_input("NUEVA CONTRASEÑA", type="password", key="r_pass")
            if st.button("📩 SOLICITAR ACCESO", use_container_width=True):
                if nu and np:
                    try:
                        conn = get_db(); cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, hash_pass(np)))
                        conn.commit(); st.success("SOLICITUD ENVIADA CON ÉXITO.")
                    except: st.error("EL USUARIO YA EXISTE.")
                else: st.warning("COMPLETA LOS CAMPOS.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state['u_nom'].upper()}")
menu = st.sidebar.radio("MENÚ:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN DE PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "🗑️ ELIMINAR CUENTAS", "👥 USUARIOS", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])

conn = get_db()
uid = st.session_state['u_id']

# --- MENÚS ---
if menu == "🚪 SALIR":
    st.session_state['auth'] = False; st.rerun()

elif menu == "🔑 CAMBIAR CLAVE":
    st.title("🔑 CAMBIAR CONTRASEÑA")
    old = st.text_input("CONTRASEÑA ACTUAL", type="password")
    new = st.text_input("NUEVA CONTRASEÑA", type="password")
    if st.button("ACTUALIZAR"):
        cur = conn.cursor(); cur.execute("SELECT password FROM usuarios WHERE id=?", (uid,))
        if cur.fetchone()[0] == hash_pass(old):
            cur.execute("UPDATE usuarios SET password=? WHERE id=?", (hash_pass(new), uid))
            conn.commit(); st.success("CLAVE ACTUALIZADA.")
        else: st.error("CLAVE ACTUAL INCORRECTA.")

elif menu == "📊 DASHBOARD":
    st.title("📊 RESUMEN GENERAL")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 CUENTAS", pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0])
    c2.metric("✅ VENDIDOS", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0])
    c3.metric("🔓 LIBRES", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0])
    df = pd.read_sql_query(f"SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True, hide_index=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 REGISTRO DE CUENTAS")
    plat = st.selectbox("PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    with st.form("f_reg", clear_on_submit=True):
        col1, col2, col3 = st.columns([2,2,1])
        m, p, c = col1.text_input("CORREO"), col2.text_input("CONTRASEÑA"), col3.number_input("COSTO S/", 0.0)
        f = st.date_input("VENCIMIENTO PROVEEDOR", format="DD/MM/YYYY")
        per_data = []
        ca, cb = st.columns(2)
        for i in range(PLATAFORMAS_CONFIG[plat]):
            with ca: n = st.text_input(f"Nombre P{i+1}", f"P{i+1}", key=f"n_{i}")
            with cb: pi = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
            per_data.append((n, pi))
        if st.form_submit_button("🚀 ACTIVAR CUENTA"):
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?)", (plat, m, p, f.strftime("%d/%m/%Y"), c, uid))
                for nom, pin in per_data:
                    cur.execute("INSERT INTO perfiles (email, plataforma, nombre, pin, creador_id) VALUES (?,?,?,?,?)", (m, plat, nom, pin, uid))
                conn.commit(); st.success("CUENTA CREADA."); st.rerun()
            except: st.error("EL CORREO YA EXISTE.")

elif menu == "📱 GESTIÓN DE PERFILES":
    st.title("📱 GESTIÓN POR PLATAFORMA")
    p_sel = st.selectbox("PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    emails = pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)['email'].tolist()
    if emails:
        target = st.selectbox("CUENTA:", emails)
        cta = pd.read_sql_query(f"SELECT password FROM cuentas WHERE email='{target}'", conn).iloc[0]
        st.info(f"🔑 CLAVE: {cta['password']}")
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{target}' AND creador_id={uid}", conn)
        for _, row in perfs.iterrows():
            stat = "🟢" if row['estado'] == 'LIBRE' else "🔴"
            with st.expander(f"{stat} {row['nombre']} | {row['estado']}"):
                if row['estado'] == 'LIBRE':
                    wa = st.text_input("WhatsApp:", key=f"wa_{row['id']}")
                    pv = st.number_input("Precio S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("🛒 VENDER", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    # MENSAJE LIMPIO SIN EMOJIS PARA WHATSAPP
                    msg = (f"*ENTREGA DE SERVICIO - {row['plataforma']}*\n\n"
                           f"• *Correo:* {target}\n"
                           f"• *Contraseña:* {cta['password']}\n"
                           f"• *Perfil:* {row['nombre']}\n"
                           f"• *PIN:* {row['pin']}\n"
                           f"• *Vencimiento:* {row['fecha_vence']}\n\n"
                           f"*¡Disfruta tu servicio!* Saúl Streaming")
                    st.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; width:100%; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer;">🚀 ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)
                    st.write("")
                    c_b1, c_b2 = st.columns(2)
                    if c_b1.button("🔄 RENOVAR (+30D)", key=f"r_{row['id']}"):
                        nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if c_b2.button("✂️ CORTAR", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

elif menu == "💰 FINANZAS PRO":
    st.title("💰 BALANCE DE CAJA")
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
        res.append({"PLATAFORMA": p, "EGRESOS": moneda(ep), "INGRESOS": moneda(ip), "GANANCIA": moneda(ip-ep)})
    st.table(pd.DataFrame(res))

elif menu == "🔔 NOTIFICACIONES":
    st.title("🔔 COBRANZA")
    df_n = pd.read_sql_query(f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
    if not df_n.empty:
        df_n['DÍAS'] = df_n['fecha_vence'].apply(calcular_dias)
        for _, r in df_n[df_n['DÍAS'] <= 3].iterrows():
            st.warning(f"⚠️ {r['nombre']} ({r['plataforma']}) vence en {r['DÍAS']} días")
            msg_n = f"Hola {r['nombre']}, recordatorio de Saúl Streaming. Vence el {r['fecha_vence']}."
            st.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg_n)}" target="_blank"><button style="background-color:#008CBA; color:white; padding:8px; border-radius:5px; border:none; cursor:pointer;">🔔 AVISAR</button></a>', unsafe_allow_html=True)

elif menu == "👥 USUARIOS":
    st.title("👥 GESTIÓN DE SOCIOS")
    if st.session_state['u_ran'] == 'ADMIN':
        pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
        for _, r in pends.iterrows():
            col1, col2 = st.columns([4,1])
            col1.write(f"👤 SOLICITUD: {r['user']}")
            if col2.button("✅ ACTIVAR", key=f"acc_{r['id']}"):
                conn.cursor().execute(f"UPDATE usuarios SET rango='SOCIO' WHERE id={r['id']}")
                conn.commit(); st.rerun()
        st.write("USUARIOS:")
        st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)
    else: st.error("SÓLO EL ADMIN PUEDE VER ESTO.")

elif menu == "🗑️ ELIMINAR CUENTAS":
    st.title("🗑️ ELIMINAR")
    df_d = pd.read_sql_query(f"SELECT id, plataforma, email FROM cuentas WHERE creador_id={uid}", conn)
    for _, r in df_d.iterrows():
        c1, c2 = st.columns([5,1])
        c1.write(f"📺 {r['plataforma']} | {r['email']}")
        if c2.button("🗑️", key=f"del_{r['id']}"):
            cur = conn.cursor()
            cur.execute(f"DELETE FROM cuentas WHERE id={r['id']}"); cur.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
            conn.commit(); st.rerun()