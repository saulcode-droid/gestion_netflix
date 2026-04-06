import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming Pro V5.2", page_icon="🎬", layout="wide")

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
    # Crear admin maestro si no existe
    cursor.execute("INSERT OR IGNORE INTO usuarios (user, password, rango) VALUES ('admin', 'admin123', 'ADMIN')")
    conn.commit()

init_db()

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def login():
    st.title("🔐 Acceso Saúl Streaming")
    tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])
    
    with tab1:
        u = st.text_input("Usuario", key="login_user")
        p = st.text_input("Contraseña", type="password", key="login_pass")
        if st.button("Entrar"):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT rango FROM usuarios WHERE user=? AND password=?", (u, p))
            res = cursor.fetchone()
            if res:
                if res[0] == 'PENDIENTE':
                    st.warning("⚠️ Tu cuenta aún no ha sido activada por Saúl.")
                else:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.session_state['rango'] = res[0]
                    st.rerun()
            else:
                st.error("Credenciales incorrectas")

    with tab2:
        st.write("Crea tu cuenta para acceder a tus servicios.")
        new_u = st.text_input("Elige un Usuario", key="reg_user")
        new_p = st.text_input("Elige una Contraseña", type="password", key="reg_pass")
        if st.button("Solicitar Registro"):
            if new_u and new_p:
                conn = get_db(); cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", (new_u, new_p, 'PENDIENTE'))
                    conn.commit()
                    st.success("✅ Solicitud enviada. Contacta a Saúl para activar tu acceso.")
                except: st.error("❌ El usuario ya existe.")
            else: st.warning("Completa todos los campos.")

if not st.session_state['autenticado']:
    login()
    st.stop()

# --- UTILIDADES ---
def calcular_dias(fecha_vence_str):
    try:
        f_vence = datetime.strptime(fecha_vence_str, "%d/%m/%Y")
        diff = (f_vence - datetime.now()).days + 1
        return diff
    except: return 0

# --- MENÚ LATERAL ---
st.sidebar.title(f"👤 {st.session_state['usuario']}")
st.sidebar.write(f"Rango: **{st.session_state['rango']}**")

if st.session_state['rango'] == 'ADMIN':
    menu = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "💰 Finanzas Pro", "🗑️ Eliminar Cuentas", "👥 Gestionar Usuarios", "🚪 Cerrar Sesión"])
else:
    menu = st.sidebar.radio("Ir a:", ["📱 Mis Servicios", "🚪 Cerrar Sesión"])

if menu == "🚪 Cerrar Sesión":
    st.session_state['autenticado'] = False
    st.rerun()

# --- NUEVO: GESTIONAR USUARIOS (DONDE TE LLEGAN LAS SOLICITUDES) ---
if menu == "👥 Gestionar Usuarios":
    st.title("👥 Solicitudes y Usuarios")
    conn = get_db(); cursor = conn.cursor()
    
    st.subheader("⏳ Solicitudes Pendientes")
    pendientes = pd.read_sql_query("SELECT id, user, rango FROM usuarios WHERE rango='PENDIENTE'", conn)
    
    if pendientes.empty:
        st.info("No hay solicitudes nuevas por ahora.")
    else:
        for _, row in pendientes.iterrows():
            col1, col2, col3 = st.columns([2,1,1])
            col1.write(f"👤 **{row['user']}**")
            if col2.button("✅ ACTIVAR", key=f"act_{row['id']}"):
                cursor.execute("UPDATE usuarios SET rango='CLIENTE' WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()
            if col3.button("❌ RECHAZAR", key=f"rech_{row['id']}"):
                cursor.execute("DELETE FROM usuarios WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()
    
    st.divider()
    st.subheader("👥 Usuarios Activos")
    activos = pd.read_sql_query("SELECT id, user, rango FROM usuarios WHERE rango != 'PENDIENTE'", conn)
    st.dataframe(activos, use_container_width=True)

# --- DASHBOARD (CON COLUMNA DÍAS) ---
elif menu == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    conn = get_db()
    total_ctas = pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0]
    total_vendidos = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0]
    total_libres = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0]

    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas Stock", total_ctas)
    c2.metric("✅ Vendidos", total_vendidos)
    c3.metric("🔓 Libres", total_libres)

    st.subheader("👥 Clientes y Días Restantes")
    df = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True)

# --- VISTA CLIENTE ---
elif menu == "📱 Mis Servicios":
    st.title("📱 Mis Servicios Activos")
    conn = get_db()
    # Filtra perfiles donde el WhatsApp o el Nombre coincidan con el usuario logueado
    u = st.session_state['usuario']
    df_mismas = pd.read_sql_query(f"SELECT plataforma, nombre, pin, fecha_vence FROM perfiles WHERE (whatsapp LIKE '%{u}%' OR nombre LIKE '%{u}%') AND estado='VENDIDO'", conn)
    if not df_mismas.empty:
        df_mismas['Días Restantes'] = df_mismas['fecha_vence'].apply(calcular_dias)
        st.table(df_mismas)
    else:
        st.info("Aún no tienes perfiles asignados. Contacta a Saúl.")

# [Mantener el resto de funciones: PLATAFORMAS, Gestión de Perfiles, Finanzas, Proveedores, etc.]