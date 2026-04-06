import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Saúl Streaming Pro V5.6", page_icon="🎬", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS BLINDADA ---
DB_NAME = 'db_streaming_saul_final.db'

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                      (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT DEFAULT 'CLIENTE')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT, costo REAL DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, precio_venta REAL DEFAULT 0)''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (user, password, rango) VALUES ('admin', 'admin123', 'ADMIN')")
    conn.commit()

init_db()

# --- UTILIDADES ---
def calcular_dias(fecha_vence_str):
    try:
        f_vence = datetime.strptime(fecha_vence_str, "%d/%m/%Y")
        diff = (f_vence - datetime.now()).days + 1
        return diff
    except: return 0

# --- LOGIN SYSTEM ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<style>.stApp { display: flex; align-items: center; justify-content: center; }</style>", unsafe_allow_html=True)
    with st.container():
        st.title("🔐 Acceso VIP Saúl")
        t1, t2 = st.tabs(["Ingresar", "Registrarse"])
        with t1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Contraseña", type="password", key="l_p")
            if st.button("🚀 ENTRAR", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT rango FROM usuarios WHERE user=? AND password=?", (u, p))
                res = cursor.fetchone()
                if res:
                    if res[0] == 'PENDIENTE': st.warning("Esperando activación.")
                    else:
                        st.session_state['autenticado'] = True
                        st.session_state['usuario'] = u
                        st.session_state['rango'] = res[0]
                        st.rerun()
                else: st.error("Datos incorrectos.")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Clave", type="password")
            if st.button("SOLICITAR ACCESO"):
                try:
                    conn = get_db(); cursor = conn.cursor()
                    cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, np))
                    conn.commit(); st.success("Solicitud enviada.")
                except: st.error("El usuario ya existe.")
    st.stop()

# --- MENÚ LATERAL ---
st.sidebar.title(f"👤 {st.session_state['usuario']}")
if st.session_state['rango'] == 'ADMIN':
    menu = st.sidebar.radio("Menú:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "💰 Finanzas Pro", "📅 Proveedores", "🗑️ Eliminar Cuentas", "👥 Usuarios", "🔑 Cambiar Clave", "🚪 Salir"])
else:
    menu = st.sidebar.radio("Menú:", ["📱 Mis Servicios", "🔑 Cambiar Clave", "🚪 Salir"])

conn = get_db()

# --- LÓGICA DE MENÚS ---
if menu == "🚪 Salir":
    st.session_state['autenticado'] = False
    st.rerun()

elif menu == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas", pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0])
    c2.metric("✅ Vendidos", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0])
    c3.metric("🔓 Libres", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0])
    df = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Cuentas")
    plat = st.selectbox("Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    with st.form("f_reg"):
        c1, c2, c3 = st.columns([2,2,1])
        mail = c1.text_input("Correo")
        pasw = c2.text_input("Clave")
        costo = c3.number_input("Costo S/", min_value=0.0)
        f_v = st.date_input("Vence Proveedor", format="DD/MM/YYYY")
        st.write("---")
        cols = st.columns(2)
        for i in range(PLATAFORMAS_CONFIG[plat]):
            with cols[0]: n = st.text_input(f"Nombre P{i+1}", f"P{i+1}", key=f"n_{i}")
            with cols[1]: p = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
        if st.form_submit_button("🚀 GUARDAR"):
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", (plat, mail, pasw, f_v.strftime("%d/%m/%Y"), costo))
                for i in range(PLATAFORMAS_CONFIG[plat]):
                    cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", (mail, plat, st.session_state[f"n_{i}"], st.session_state[f"p_{i}"]))
                conn.commit(); st.success("Registrado."); st.rerun()
            except: st.error("Error: Correo ya existe.")

elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Panel de Ventas")
    emails = pd.read_sql_query("SELECT email FROM cuentas", conn)['email'].tolist()
    if emails:
        sel_m = st.selectbox("Cuenta:", emails)
        cta = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel_m}'", conn).iloc[0]
        st.info(f"🔑 Clave {cta['plataforma']}: `{cta['password']}`")
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_m}'", conn)
        for _, row in perfs.iterrows():
            stat = f"🔴 {row['whatsapp']}" if row['estado'] == 'VENDIDO' else "🟢 LIBRE"
            with st.expander(f"{row['nombre']} | {stat}"):
                c1, c2 = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("WhatsApp:", key=f"wa_{row['id']}")
                    pv = c2.number_input("Precio S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("🛒 Confirmar Venta", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} (**{d} días**)")
                    msg = f"💎 *ENTREGA {row['plataforma']}*\n📧 `{sel_m}`\n🔑 `{cta['password']}`\n👤 {row['nombre']}\n📌 {row['pin']}\n📅 Vence: {row['fecha_vence']}"
                    st.markdown(f'[🚀 ENVIAR WHATSAPP](https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)})')
                    if st.button("🔄 Renovar (+30d)", key=f"r_{row['id']}"):
                        fv = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{fv}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if st.button("✂️ Cortar Servicio", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

elif menu == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza")
    df_n = pd.read_sql_query("SELECT * FROM perfiles WHERE estado='VENDIDO'", conn)
    for _, r in df_n.iterrows():
        d = calcular_dias(r['fecha_vence'])
        if d <= 3:
            col1, col2 = st.columns([3,1])
            col1.warning(f"⚠️ {r['nombre']} ({r['plataforma']}) vence en {d} días.")
            msg = f"Hola {r['nombre']}, tu perfil de {r['plataforma']} vence el {r['fecha_vence']}. ¿Renovamos?"
            col2.markdown(f'[🔔 AVISAR](https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg)})')

elif menu == "💰 Finanzas Pro":
    st.title("💰 Reporte Real")
    e = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    i = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    c1, c2, c3 = st.columns(3)
    c1.metric("📉 Egresos", f"S/ {e:.2f}")
    c2.metric("📈 Ingresos", f"S/ {i:.2f}")
    c3.metric("🤑 Ganancia", f"S/ {i-e:.2f}")
    st.divider()
    resumen = []
    for p in PLATAFORMAS_CONFIG.keys():
        ep = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}'", conn)['t'][0] or 0
        ip = pd.read_sql_query(f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}'", conn)['t'][0] or 0
        resumen.append({"Plataforma": p, "Egresos": ep, "Ingresos": ip, "Ganancia": ip-ep})
    st.table(pd.DataFrame(resumen))

elif menu == "🗑️ Eliminar Cuentas":
    st.title("🗑️ Borrar Cuentas")
    df_d = pd.read_sql_query("SELECT id, plataforma, email FROM cuentas", conn)
    for _, r in df_d.iterrows():
        col1, col2 = st.columns([4,1])
        col1.write(f"📺 {r['plataforma']} | {r['email']}")
        if col2.button("🗑️", key=f"d_{r['id']}"):
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
            cursor.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
            conn.commit(); st.rerun()

elif menu == "👥 Usuarios":
    st.title("👥 Gestión de Usuarios")
    pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
    for _, r in pends.iterrows():
        col1, col2 = st.columns([3,1])
        col1.write(f"👤 {r['user']}")
        if col2.button("✅", key=f"acc_{r['id']}"):
            conn.cursor().execute(f"UPDATE usuarios SET rango='CLIENTE' WHERE id={r['id']}")
            conn.commit(); st.rerun()
    st.divider()
    st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)

elif menu == "🔑 Cambiar Clave":
    st.title("🔑 Nueva Contraseña")
    cp = st.text_input("Clave Actual", type="password")
    np = st.text_input("Nueva Clave", type="password")
    if st.button("Actualizar"):
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM usuarios WHERE user=?", (st.session_state['usuario'],))
        if cursor.fetchone()[0] == cp:
            cursor.execute("UPDATE usuarios SET password=? WHERE user=?", (np, st.session_state['usuario']))
            conn.commit(); st.success("✅ Actualizada.")
        else: st.error("Clave incorrecta.")

elif menu == "📅 Proveedores":
    st.title("📅 Lista de Proveedores")
    st.dataframe(pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas", conn), use_container_width=True)

elif menu == "📱 Mis Servicios":
    st.title("📱 Mis Servicios")
    u = st.session_state['usuario']
    df_m = pd.read_sql_query(f"SELECT plataforma, nombre, pin, fecha_vence FROM perfiles WHERE (whatsapp LIKE '%{u}%' OR nombre LIKE '%{u}%') AND estado='VENDIDO'", conn)
    if not df_m.empty:
        df_m['Días'] = df_m['fecha_vence'].apply(calcular_dias)
        st.table(df_m)
    else: st.info("Sin servicios activos.")