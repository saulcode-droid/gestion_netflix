import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming VIP V5.1", page_icon="🎬", layout="wide")

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
    # Tabla Usuarios (Login)
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                      (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT DEFAULT 'CLIENTE')''')
    # Tabla Cuentas
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT, costo REAL)''')
    # Tabla Perfiles
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, precio_venta REAL DEFAULT 0)''')
    
    # Crear usuario administrador por defecto si no existe
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
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT rango FROM usuarios WHERE user=? AND password=?", (u, p))
            res = cursor.fetchone()
            if res:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = u
                st.session_state['rango'] = res[0]
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

    with tab2:
        st.write("Crea tu cuenta. El administrador deberá activarte.")
        new_u = st.text_input("Nuevo Usuario")
        new_p = st.text_input("Nueva Contraseña", type="password")
        if st.button("Solicitar Registro"):
            conn = get_db(); cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", (new_u, new_p, 'PENDIENTE'))
                conn.commit()
                st.success("Solicitud enviada. Contacta a Saúl para activar tu acceso.")
            except: st.error("El usuario ya existe.")

if not st.session_state['autenticado']:
    login()
    st.stop()

# --- LÓGICA DE DÍAS RESTANTES ---
def calcular_dias(fecha_vence_str):
    try:
        f_vence = datetime.strptime(fecha_vence_str, "%d/%m/%Y")
        f_hoy = datetime.now()
        diferencia = (f_vence - f_hoy).days + 1
        return diferencia
    except: return 0

# --- MENÚ LATERAL ---
st.sidebar.title(f"👤 {st.session_state['usuario']}")
st.sidebar.write(f"Rango: {st.session_state['rango']}")

if st.session_state['rango'] == 'ADMIN':
    menu = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "💰 Finanzas Pro", "🗑️ Eliminar Cuentas", "🚪 Cerrar Sesión"])
else:
    menu = st.sidebar.radio("Ir a:", ["📱 Mis Cuentas", "🚪 Cerrar Sesión"])

if menu == "🚪 Cerrar Sesión":
    st.session_state['autenticado'] = False
    st.rerun()

# --- 1. DASHBOARD (CON COLUMNA VENCE DÍAS) ---
if menu == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    conn = get_db()
    
    # Métricas
    total_ctas = pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0]
    total_vendidos = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0]
    total_libres = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0]

    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas Stock", total_ctas)
    c2.metric("✅ Vendidos", total_vendidos)
    c3.metric("🔓 Libres", total_libres)

    st.divider()
    st.subheader("👥 Clientes Activos y Días Restantes")
    df_clientes = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    
    if not df_clientes.empty:
        # Aplicar cálculo de días
        df_clientes['VENCE (DÍAS)'] = df_clientes['fecha_vence'].apply(calcular_dias)
        # Reordenar columnas para que DÍAS esté visible
        df_clientes = df_clientes[['plataforma', 'email', 'nombre', 'whatsapp', 'fecha_vence', 'VENCE (DÍAS)']]
        st.dataframe(df_clientes.style.highlight_between(left=-999, right=2, subset=['VENCE (DÍAS)'], color='#ff4b4b'), use_container_width=True)
    else:
        st.write("No hay perfiles vendidos.")

# --- 2. PLATAFORMAS ---
elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Plataformas")
    plat_sel = st.selectbox("Selecciona la Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_perfiles = PLATAFORMAS_CONFIG[plat_sel]
    
    with st.form("reg_plat"):
        c1, c2, c3 = st.columns([2,2,1])
        mail = c1.text_input("Correo")
        pasw = c2.text_input("Clave")
        costo = c3.number_input("Costo S/", min_value=0.0)
        f_prov = st.date_input("Vence Proveedor", format="DD/MM/YYYY")
        
        perfiles_lista = []
        cols = st.columns(2)
        for i in range(num_perfiles):
            with cols[0]: n = st.text_input(f"Perfil {i+1}", f"P{i+1}", key=f"n_{i}")
            with cols[1]: p = st.text_input(f"PIN {i+1}", "0000", key=f"p_{i}")
            perfiles_lista.append((n, p))
        
        if st.form_submit_button("Guardar"):
            conn = get_db(); cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", 
                               (plat_sel, mail, pasw, f_prov.strftime("%d/%m/%Y"), costo))
                for nom, pin in perfiles_lista:
                    cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", (mail, plat_sel, nom, pin))
                conn.commit(); st.success("Registrado"); st.rerun()
            except: st.error("El correo ya existe.")

# --- 3. GESTIÓN DE PERFILES ---
elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Panel de Ventas")
    conn = get_db()
    emails = pd.read_sql_query("SELECT email FROM cuentas", conn)['email'].tolist()
    if emails:
        sel_mail = st.selectbox("Cuenta:", emails)
        cta = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel_mail}'", conn).iloc[0]
        perfiles = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_mail}'", conn)
        st.info(f"🔑 Clave {cta['plataforma']}: `{cta['password']}`")
        for _, row in perfiles.iterrows():
            status = f"🔴 {row['whatsapp']}" if row['estado'] == 'VENDIDO' else "🟢 LIBRE"
            with st.expander(f"{row['nombre']} | {status}"):
                if row['estado'] == 'LIBRE':
                    wa = st.text_input("WhatsApp:", key=f"wa_{row['id']}")
                    pv = st.number_input("Precio S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("Vender", key=f"btn_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    dias_q = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} (**{dias_q} días restantes**)")
                    msg = f"✅ *ENTREGA {row['plataforma']}*\n📧 `{sel_mail}`\n🔑 `{cta['password']}`\n👤 {row['nombre']}\n📌 {row['pin']}"
                    st.markdown(f'[🚀 ENVIAR WHATSAPP](https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg)})')
                    if st.button("✂️ Cortar", key=f"cut_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

# --- 4. MIS CUENTAS (VISTA CLIENTE) ---
elif menu == "📱 Mis Cuentas":
    st.title("📱 Mis Servicios Comprados")
    conn = get_db()
    # Aquí buscamos por el nombre de usuario (asumiendo que el usuario es su WhatsApp o nombre)
    u = st.session_state['usuario']
    # En una versión avanzada, el cliente debería estar vinculado a su número de WhatsApp
    st.info("Aquí aparecerán los perfiles vinculados a tu cuenta una vez que el administrador los asigne.")
    df_mismas = pd.read_sql_query(f"SELECT plataforma, nombre, pin, fecha_vence FROM perfiles WHERE whatsapp LIKE '%{u}%'", conn)
    if not df_mismas.empty:
        df_mismas['Días Libres'] = df_mismas['fecha_vence'].apply(calcular_dias)
        st.table(df_mismas)
    else:
        st.write("No tienes servicios activos.")

# --- RESTO DE MENÚS (FINANZAS, ELIMINAR, ETC) ---
# [Mismo código de Finanzas y Proveedores de la v5.0]