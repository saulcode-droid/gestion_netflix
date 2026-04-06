import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming VIP V5.3", page_icon="🎬", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
def get_db():
    conn = sqlite3.connect('db_saul_streaming_v5.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                      (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT DEFAULT 'CLIENTE')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT, costo REAL)''')
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

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acceso Saúl Streaming")
    tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])
    
    with tab1:
        u = st.text_input("Usuario", key="l_user")
        p = st.text_input("Contraseña", type="password", key="l_pass")
        if st.button("Entrar"):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT rango FROM usuarios WHERE user=? AND password=?", (u, p))
            res = cursor.fetchone()
            if res:
                if res[0] == 'PENDIENTE':
                    st.warning("⚠️ Tu cuenta espera activación de Saúl.")
                else:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.session_state['rango'] = res[0]
                    st.rerun()
            else: st.error("Usuario o clave incorrectos")

    with tab2:
        st.write("Crea tu cuenta para ver tus servicios.")
        new_u = st.text_input("Nuevo Usuario", key="r_user")
        new_p = st.text_input("Nueva Contraseña", type="password", key="r_pass")
        if st.button("Solicitar Registro"):
            if new_u and new_p:
                conn = get_db(); cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", (new_u, new_p, 'PENDIENTE'))
                    conn.commit(); st.success("✅ Solicitud enviada.")
                except: st.error("El usuario ya existe.")
    st.stop()

# --- MENÚ LATERAL ---
st.sidebar.title(f"👤 {st.session_state['usuario']}")
st.sidebar.write(f"Rango: **{st.session_state['rango']}**")

if st.session_state['rango'] == 'ADMIN':
    menu = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "💰 Finanzas Pro", "📅 Proveedores", "🗑️ Eliminar Cuentas", "👥 Usuarios", "🚪 Salir"])
else:
    menu = st.sidebar.radio("Ir a:", ["📱 Mis Servicios", "🚪 Salir"])

# --- FUNCIONES DE LOS MENÚS ---

if menu == "🚪 Salir":
    st.session_state['autenticado'] = False
    st.rerun()

elif menu == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    conn = get_db()
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas", pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0])
    c2.metric("✅ Vendidos", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0])
    c3.metric("🔓 Libres", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0])
    
    st.subheader("👥 Clientes y Días Restantes")
    df = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Cuentas")
    plat_sel = st.selectbox("Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_per = PLATAFORMAS_CONFIG[plat_sel]
    with st.form("reg"):
        c1, c2, c3 = st.columns([2,2,1])
        mail = c1.text_input("Correo")
        pasw = c2.text_input("Clave")
        costo = c3.number_input("Costo S/", min_value=0.0)
        f_p = st.date_input("Vence Proveedor", format="DD/MM/YYYY")
        per_list = []
        st.write("---")
        cols = st.columns(2)
        for i in range(num_per):
            with cols[0]: n = st.text_input(f"Nombre P{i+1}", f"P{i+1}", key=f"n_{i}")
            with cols[1]: p = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
            per_list.append((n, p))
        if st.form_submit_button("Guardar"):
            conn = get_db(); cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", (plat_sel, mail, pasw, f_p.strftime("%d/%m/%Y"), costo))
                for nom, pin in per_list:
                    cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", (mail, plat_sel, nom, pin))
                conn.commit(); st.success("✅ Cuenta Creada"); st.rerun()
            except: st.error("Error: El correo ya existe.")

elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Panel de Ventas")
    conn = get_db()
    emails = pd.read_sql_query("SELECT email FROM cuentas", conn)['email'].tolist()
    if emails:
        sel_m = st.selectbox("Cuenta:", emails)
        cta = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel_m}'", conn).iloc[0]
        st.info(f"🔑 Clave {cta['plataforma']}: `{cta['password']}`")
        perfiles = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_m}'", conn)
        for _, row in perfiles.iterrows():
            stat = f"🔴 {row['whatsapp']}" if row['estado'] == 'VENDIDO' else "🟢 LIBRE"
            with st.expander(f"{row['nombre']} | {stat}"):
                c1, c2 = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("WhatsApp:", key=f"wa_{row['id']}")
                    pv = c2.number_input("Precio S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("Vender", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} (**{d} días**)")
                    msg = f"✅ *ENTREGA {row['plataforma']}*\n📧 `{sel_m}`\n🔑 `{cta['password']}`\n👤 {row['nombre']}\n📌 {row['pin']}"
                    st.markdown(f'[🚀 ENVIAR](https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg)})')
                    if st.button("✂️ Cortar", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

elif menu == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza")
    conn = get_db()
    df_n = pd.read_sql_query("SELECT * FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df_n.empty:
        for _, r in df_n.iterrows():
            d = calcular_dias(r['fecha_vence'])
            if d <= 3:
                c1, c2 = st.columns([3,1])
                c1.warning(f"⚠️ {r['nombre']} ({r['plataforma']}) vence en {d} días.")
                msg = f"Hola {r['nombre']}, tu perfil de {r['plataforma']} vence pronto. ¿Renovamos?"
                c2.markdown(f'[🔔 AVISAR](https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg)})')
    else: st.success("Sin pendientes.")

elif menu == "💰 Finanzas Pro":
    st.title("💰 Balance Financiero")
    conn = get_db()
    e = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    i = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    c1, c2, c3 = st.columns(3)
    c1.metric("📉 Egresos", f"S/ {e:.2f}")
    c2.metric("📈 Ingresos", f"S/ {i:.2f}")
    c3.metric("🤑 Ganancia", f"S/ {i-e:.2f}")

elif menu == "🗑️ Eliminar Cuentas":
    st.title("🗑️ Borrar Cuentas")
    conn = get_db()
    df_d = pd.read_sql_query("SELECT id, plataforma, email FROM cuentas", conn)
    for _, r in df_d.iterrows():
        c1, c2 = st.columns([4,1])
        c1.write(f"📺 {r['plataforma']} | {r['email']}")
        if c2.button("🗑️", key=f"d_{r['id']}"):
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
            cursor.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
            conn.commit(); st.rerun()

elif menu == "👥 Usuarios":
    st.title("👥 Gestión de Usuarios")
    conn = get_db(); cursor = conn.cursor()
    pendientes = pd.read_sql_query("SELECT id, user, rango FROM usuarios WHERE rango='PENDIENTE'", conn)
    if not pendientes.empty:
        for _, r in pendientes.iterrows():
            c1, c2 = st.columns([3,1])
            c1.write(f"👤 {r['user']}")
            if c2.button("✅", key=f"a_{r['id']}"):
                cursor.execute(f"UPDATE usuarios SET rango='CLIENTE' WHERE id={r['id']}")
                conn.commit(); st.rerun()
    st.write("---")
    st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)

elif menu == "📱 Mis Servicios":
    st.title("📱 Mis Servicios")
    conn = get_db()
    u = st.session_state['usuario']
    df_m = pd.read_sql_query(f"SELECT plataforma, nombre, pin, fecha_vence FROM perfiles WHERE (whatsapp LIKE '%{u}%' OR nombre LIKE '%{u}%') AND estado='VENDIDO'", conn)
    if not df_m.empty:
        df_m['Días'] = df_m['fecha_vence'].apply(calcular_dias)
        st.table(df_m)
    else: st.info("No tienes perfiles activos.")

elif menu == "📅 Proveedores":
    st.title("📅 Vencimientos Proveedor")
    conn = get_db()
    st.dataframe(pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor FROM cuentas", conn), use_container_width=True)