import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming Pro V5.5", page_icon="🎬", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_v54.db'

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

# --- SISTEMA DE LOGIN CENTRADO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def login():
    # Estilo para centrar el login
    st.markdown("""
        <style>
        .stApp { display: flex; align-items: center; justify-content: center; }
        .login-box { border: 1px solid #4B4B4B; padding: 2rem; border-radius: 10px; background-color: #1E1E1E; width: 400px; }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.title("🔐 Acceso VIP")
        
        tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])
        
        with tab1:
            u = st.text_input("Usuario", key="l_user")
            p = st.text_input("Contraseña", type="password", key="l_pass")
            if st.button("🚀 ENTRAR AL PANEL", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT rango FROM usuarios WHERE user=? AND password=?", (u, p))
                res = cursor.fetchone()
                if res:
                    if res[0] == 'PENDIENTE':
                        st.warning("⚠️ Tu cuenta espera activación del administrador.")
                    else:
                        st.session_state['autenticado'] = True
                        st.session_state['usuario'] = u
                        st.session_state['rango'] = res[0]
                        st.rerun()
                else: st.error("❌ Usuario o contraseña incorrectos.")
            
            if st.button("❓ Olvidé mi contraseña", use_container_width=True):
                st.info("ℹ️ Contacta a Saúl por WhatsApp para restablecer tu contraseña.")

        with tab2:
            st.write("Crea tu cuenta de cliente.")
            new_u = st.text_input("Nuevo Usuario", key="r_user")
            new_p = st.text_input("Nueva Contraseña", type="password", key="r_pass")
            if st.button("📩 SOLICITAR ACCESO", use_container_width=True):
                if new_u and new_p:
                    conn = get_db(); cursor = conn.cursor()
                    try:
                        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", (new_u, new_p, 'PENDIENTE'))
                        conn.commit(); st.success("✅ Solicitud enviada.")
                    except: st.error("❌ El usuario ya existe.")
                else: st.warning("Completa todos los campos.")
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state['autenticado']:
    login()
    st.stop()

# --- MENÚ LATERAL ---
st.sidebar.title(f"👤 {st.session_state['usuario']}")
if st.session_state['rango'] == 'ADMIN':
    menu = st.sidebar.radio("Menú:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "💰 Finanzas Pro", "📅 Proveedores", "🗑️ Eliminar Cuentas", "👥 Usuarios", "🔑 Cambiar Mi Clave", "🚪 Salir"])
else:
    menu = st.sidebar.radio("Menú:", ["📱 Mis Servicios", "🔑 Cambiar Mi Clave", "🚪 Salir"])

if menu == "🚪 Salir":
    st.session_state['autenticado'] = False; st.rerun()

# --- 🌐 REGISTRO DE PLATAFORMAS (LÓGICA LIMPIA) ---
elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Cuentas")
    plat_sel = st.selectbox("Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_per = PLATAFORMAS_CONFIG[plat_sel]
    
    with st.form("reg_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([2,2,1])
        mail = c1.text_input("📧 Correo")
        pasw = c2.text_input("🔑 Clave")
        costo = c3.number_input("💵 Costo (S/)", min_value=0.0)
        f_p = st.date_input("📅 Vence Proveedor", format="DD/MM/YYYY")
        
        per_list = []
        cols = st.columns(2)
        for i in range(num_per):
            with cols[0]: n = st.text_input(f"Nombre P{i+1}", f"P{i+1}", key=f"n_{i}")
            with cols[1]: p = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
            per_list.append((n, p))
            
        if st.form_submit_button("🚀 GUARDAR PLATAFORMA"):
            if not mail or not pasw:
                st.warning("⚠️ Por favor completa el correo y la clave.")
            else:
                conn = get_db(); cursor = conn.cursor()
                # Verificar existencia antes de insertar
                cursor.execute("SELECT id FROM cuentas WHERE email=?", (mail,))
                if cursor.fetchone():
                    st.error(f"❌ Error: El correo '{mail}' ya está registrado.")
                else:
                    try:
                        cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", (plat_sel, mail, pasw, f_p.strftime("%d/%m/%Y"), costo))
                        for nom, pin in per_list:
                            cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", (mail, plat_sel, nom, pin))
                        conn.commit()
                        st.success(f"✅ ¡Plataforma {plat_sel} registrada con éxito!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Hubo un problema al guardar: {e}")

# --- 📊 RESTO DE FUNCIONES (DASHBOARD, GESTIÓN, ETC.) ---
elif menu == "📊 Dashboard":
    st.title("📊 Resumen")
    conn = get_db()
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas", pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0])
    c2.metric("✅ Vendidos", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0])
    c3.metric("🔓 Libres", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0])
    df = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True)

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
                    if st.button("🛒 Confirmar Venta", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} (**{d} días**)")
                    msg = f"💎 *ENTREGA {row['plataforma']}*\n📧 `{sel_m}`\n🔑 `{cta['password']}`\n👤 {row['nombre']}\n📌 {row['pin']}"
                    st.markdown(f'[🚀 ENVIAR WHATSAPP](https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)})')
                    if st.button("✂️ Cortar Servicio", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

elif menu == "💰 Finanzas Pro":
    st.title("💰 Balance")
    conn = get_db()
    e = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    i = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    c1, c2, c3 = st.columns(3)
    c1.metric("📉 Egresos", f"S/ {e:.2f}")
    c2.metric("📈 Ingresos", f"S/ {i:.2f}")
    c3.metric("🤑 Ganancia", f"S/ {i-e:.2f}")

elif menu == "🔑 Cambiar Mi Clave":
    st.title("🔑 Nueva Contraseña")
    old_p = st.text_input("Clave Actual", type="password")
    new_p = st.text_input("Nueva Clave", type="password")
    if st.button("Actualizar"):
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("SELECT password FROM usuarios WHERE user=?", (st.session_state['usuario'],))
        if cursor.fetchone()[0] == old_p:
            cursor.execute("UPDATE usuarios SET password=? WHERE user=?", (new_p, st.session_state['usuario']))
            conn.commit(); st.success("✅ Cambiada.")
        else: st.error("Incorrecta.")

# (Resto de menús se mantienen con su funcionalidad actual...)