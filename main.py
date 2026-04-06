import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAÚL STREAMING ELITE V7.0", page_icon="💎", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_final.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT DEFAULT "CLIENTE")')
    cursor.execute('CREATE TABLE IF NOT EXISTS cuentas (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT, costo REAL DEFAULT 0)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, precio_venta REAL DEFAULT 0)''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (user, password, rango) VALUES ('admin', 'admin123', 'ADMIN')")
    conn.commit()

init_db()

# --- ESTILOS CSS ELITE ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #30363d; }
    .card-finanzas {
        background: rgba(255, 255, 255, 0.05);
        padding: 25px; border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    .btn-delete { background-color: #ff4b4b; color: white; border-radius: 10px; }
    .btn-approve { background-color: #25D366; color: white; border-radius: 10px; }
    h1, h2, h3 { text-transform: uppercase; letter-spacing: 2px; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def calcular_dias(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

def moneda(valor):
    return f"S/ {valor:,.2f}"

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png")
        st.markdown('<h1 style="text-align:center; color:#00FF00;">ACCESO AL SISTEMA</h1>', unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔑 ENTRAR", "📝 REGISTRO"])
        with t1:
            u = st.text_input("USUARIO")
            p = st.text_input("CONTRASEÑA", type="password")
            if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT rango FROM usuarios WHERE user=? AND password=?", (u, p))
                res = cursor.fetchone()
                if res:
                    if res[0] == 'PENDIENTE': st.warning("SU CUENTA ESTÁ EN ESPERA DE ACTIVACIÓN.")
                    else:
                        st.session_state['autenticado'], st.session_state['usuario'], st.session_state['rango'] = True, u, res[0]
                        st.rerun()
                else: st.error("USUARIO O CLAVE INCORRECTOS.")
            if st.button("🔐 OLVIDÉ MI CONTRASEÑA", use_container_width=True):
                st.info("CONTACTE AL ADMINISTRADOR SAÚL PARA REESTABLECER SU ACCESO.")
        with t2:
            nu = st.text_input("NUEVO USUARIO")
            np = st.text_input("NUEVA CLAVE", type="password")
            if st.button("SOLICITAR ACCESO"):
                try:
                    conn = get_db(); cursor = conn.cursor()
                    cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, np))
                    conn.commit(); st.success("SOLICITUD ENVIADA.")
                except: st.error("EL USUARIO YA EXISTE.")
    st.stop()

# --- MENÚ LATERAL ---
st.sidebar.title(f"👤 {st.session_state['usuario'].upper()}")
if st.session_state['rango'] == 'ADMIN':
    menu = st.sidebar.radio("MENÚ ADMINISTRADOR:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN DE PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "📅 PROVEEDORES", "🗑️ ELIMINAR CUENTAS", "👥 CONTROL DE USUARIOS", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])
else:
    menu = st.sidebar.radio("MENÚ CLIENTE:", ["📱 MIS SERVICIOS", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])

conn = get_db()

# --- LÓGICA DE MENÚS ---
if menu == "🚪 SALIR":
    st.session_state['autenticado'] = False; st.rerun()

elif menu == "📊 DASHBOARD":
    st.title("📊 RESUMEN EJECUTIVO")
    c1, c2, c3 = st.columns(3)
    val1 = pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0]
    val2 = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0]
    val3 = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0]
    with c1: st.metric("📦 CUENTAS MAESTRAS", val1)
    with c2: st.metric("✅ PERFILES VENDIDOS", val2)
    with c3: st.metric("🔓 PERFILES LIBRES", val3)
    st.divider()
    st.subheader("👥 CLIENTES PRÓXIMOS A VENCER")
    df = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True, hide_index=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 REGISTRO DE CUENTAS")
    plat = st.selectbox("SELECCIONA PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    with st.form("reg"):
        col1, col2, col3 = st.columns([2,2,1])
        m, p, cost = col1.text_input("CORREO"), col2.text_input("CLAVE"), col3.number_input("COSTO S/", 0.0)
        f = st.date_input("VENCIMIENTO PROVEEDOR", format="DD/MM/YYYY")
        st.write("---")
        per_data = []
        c_a, c_b = st.columns(2)
        for i in range(PLATAFORMAS_CONFIG[plat]):
            with c_a: n = st.text_input(f"NOMBRE P{i+1}", f"P{i+1}", key=f"n_{i}")
            with c_b: pi = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
            per_data.append((n, pi))
        if st.form_submit_button("✅ GUARDAR Y ACTIVAR"):
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", (plat, m, p, f.strftime("%d/%m/%Y"), cost))
                for nom, pin in per_data:
                    cur.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", (m, plat, nom, pin))
                conn.commit(); st.success("CUENTA CARGADA CORRECTAMENTE."); st.rerun()
            except: st.error("ERROR: EL CORREO YA EXISTE.")

elif menu == "📱 GESTIÓN DE PERFILES":
    st.title("📱 ADMINISTRACIÓN POR PLATAFORMA")
    p_sel = st.selectbox("FILTRAR POR PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    emails = pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{p_sel}'", conn)['email'].tolist()
    if emails:
        target = st.selectbox("SELECCIONAR CUENTA:", emails)
        cta = pd.read_sql_query(f"SELECT password FROM cuentas WHERE email='{target}'", conn).iloc[0]
        st.warning(f"🔑 CLAVE {p_sel}: `{cta['password']}`")
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{target}'", conn)
        for _, row in perfs.iterrows():
            color = "🔴" if row['estado'] == 'VENDIDO' else "🟢"
            with st.expander(f"{color} {row['nombre']} | PIN: {row['pin']} | {row['estado']}"):
                c1, c2 = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("WHATSAPP:", key=f"wa_{row['id']}")
                    pv = c2.number_input("PRECIO VENTA S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("🛒 CONFIRMAR VENTA", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 VENCE: {row['fecha_vence']} ({d} DÍAS)")
                    msg = f"💎 *ENTREGA {row['plataforma']}* 💎\n📧 `{target}`\n🔑 `{cta['password']}`\n👤 {row['nombre']}\n📌 {row['pin']}"
                    st.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; width:100%; border:none; padding:10px; border-radius:10px; cursor:pointer; font-weight:bold;">🚀 ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)
                    st.write("")
                    cb1, cb2 = st.columns(2)
                    if cb1.button("🔄 RENOVACIÓN (+30D)", key=f"r_{row['id']}"):
                        nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if cb2.button("✂️ CORTAR SERVICIO", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()
    else: st.info("NO HAY CUENTAS CARGADAS EN ESTA PLATAFORMA.")

elif menu == "💰 FINANZAS PRO":
    st.title("💰 BALANCE FINANCIERO ELITE")
    eg = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    in_g = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    gan = in_g - eg
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1: st.markdown(f'<div class="card-finanzas"><h3 style="color:#ff4b4b;">📉 EGRESOS</h3><h1>{moneda(eg)}</h1></div>', unsafe_allow_html=True)
    with col_t2: st.markdown(f'<div class="card-finanzas"><h3 style="color:#25D366;">📈 INGRESOS</h3><h1>{moneda(in_g)}</h1></div>', unsafe_allow_html=True)
    color_gan = "#25D366" if gan >= 0 else "#ff4b4b"
    with col_t3: st.markdown(f'<div class="card-finanzas"><h3 style="color:{color_gan};">🤑 GANANCIA NETA</h3><h1>{moneda(gan)}</h1></div>', unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📊 DESGLOSE PROFESIONAL POR SERVICIO")
    res = []
    for p in PLATAFORMAS_CONFIG.keys():
        ep = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}'", conn)['t'][0] or 0
        ip = pd.read_sql_query(f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}'", conn)['t'][0] or 0
        res.append({"PLATAFORMA": p, "EGRESOS": moneda(ep), "INGRESOS": moneda(ip), "GANANCIA": moneda(ip-ep)})
    st.table(pd.DataFrame(res))

elif menu == "🗑️ ELIMINAR CUENTAS":
    st.title("🗑️ GESTIÓN DE BAJAS")
    st.error("¡ATENCIÓN! ESTA ACCIÓN BORRA LA CUENTA Y TODOS SUS PERFILES.")
    df_d = pd.read_sql_query("SELECT id, plataforma, email FROM cuentas", conn)
    for _, r in df_d.iterrows():
        with st.container():
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"#### 📺 {r['plataforma']} — `{r['email']}`")
            if c2.button("🗑️ BORRAR", key=f"d_{r['id']}"):
                cur = conn.cursor()
                cur.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
                cur.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
                conn.commit(); st.rerun()
            st.divider()

elif menu == "👥 CONTROL DE USUARIOS":
    st.title("👥 ADMINISTRACIÓN DE PERSONAL")
    st.subheader("⏳ SOLICITUDES DE ACCESO")
    pends = pd.read_sql_query("SELECT id, user, password FROM usuarios WHERE rango='PENDIENTE'", conn)
    if not pends.empty:
        for _, r in pends.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"👤 NUEVO USUARIO: **{r['user']}** (CLAVE: {r['password']})")
            if c2.button("✅ ACTIVAR", key=f"u_{r['id']}"):
                conn.cursor().execute(f"UPDATE usuarios SET rango='CLIENTE' WHERE id={r['id']}")
                conn.commit(); st.rerun()
    else: st.info("NO HAY SOLICITUDES PENDIENTES.")
    st.divider()
    st.subheader("👥 LISTA COMPLETA DE USUARIOS")
    st.dataframe(pd.read_sql_query("SELECT user as USUARIO, password as CONTRASEÑA, rango as RANGO FROM usuarios", conn), use_container_width=True)

elif menu == "🔑 CAMBIAR CLAVE":
    st.title("🔑 SEGURIDAD DE CUENTA")
    with st.container():
        cp = st.text_input("CLAVE ACTUAL", type="password")
        np = st.text_input("NUEVA CLAVE", type="password")
        if st.button("ACTUALIZAR CREDENCIALES"):
            cur = conn.cursor()
            cur.execute("SELECT password FROM usuarios WHERE user=?", (st.session_state['usuario'],))
            if cur.fetchone()[0] == cp:
                cur.execute("UPDATE usuarios SET password=? WHERE user=?", (np, st.session_state['usuario']))
                conn.commit(); st.success("¡CONTRASEÑA ACTUALIZADA!"); st.rerun()
            else: st.error("LA CLAVE ACTUAL ES INCORRECTA.")

elif menu == "📅 PROVEEDORES":
    st.title("📅 CONTROL DE VENCIMIENTOS MAESTROS")
    st.dataframe(pd.read_sql_query("SELECT plataforma as PLATAFORMA, email as CORREO, password as CLAVE, fecha_proveedor as VENCE, costo as COSTO FROM cuentas", conn), use_container_width=True)

elif menu == "🔔 NOTIFICACIONES":
    st.title("🔔 CENTRAL DE COBRANZA")
    df_not = pd.read_sql_query("SELECT * FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df_not.empty:
        df_not['DÍAS'] = df_not['fecha_vence'].apply(calcular_dias)
        v_list = df_not[df_not['DÍAS'] <= 3].sort_values('DÍAS')
        if v_list.empty: st.success("✅ NO HAY COBROS PENDIENTES PARA HOY.")
        for _, r in v_list.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.warning(f"⚠️ {r['plataforma']} | {r['nombre']} vence en {r['DÍAS']} días")
            msg = f"Hola {r['nombre']}, recordatorio de Saúl Streaming 🎬. Tu perfil de {r['plataforma']} vence el {r['fecha_vence']}. ¿Renovamos?"
            c2.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#008CBA; color:white; width:100%; border:none; padding:10px; border-radius:5px; cursor:pointer;">🔔 AVISAR</button></a>', unsafe_allow_html=True)
            st.divider()

elif menu == "📱 MIS SERVICIOS":
    st.title("📱 MIS CUENTAS ACTIVAS")
    u = st.session_state['usuario']
    df_m = pd.read_sql_query(f"SELECT plataforma, nombre, pin, fecha_vence FROM perfiles WHERE (whatsapp LIKE '%{u}%' OR nombre LIKE '%{u}%') AND estado='VENDIDO'", conn)
    if not df_m.empty:
        df_m['DÍAS RESTANTES'] = df_m['fecha_vence'].apply(calcular_dias)
        st.table(df_m)
    else: st.info("NO TIENES SERVICIOS VINCULADOS A ESTA CUENTA.")