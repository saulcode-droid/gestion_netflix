import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Pro Streaming - Elite Partner Platform", page_icon="💻", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS MULTI-INQUILINO ---
DB_NAME = 'db_streaming_socio_v8.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

# Función para hashear contraseñas para mayor seguridad
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_db(); cursor = conn.cursor()
    # Tabla Usuarios con columna de estado
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                      (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT DEFAULT 'PENDIENTE')''')
    # Tabla Cuentas vinculada a un Socio (creador_id)
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, 
                       fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER, 
                       FOREIGN KEY(creador_id) REFERENCES usuarios(id))''')
    # Tabla Perfiles vinculada a un Socio (creador_id)
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER, 
                       FOREIGN KEY(creador_id) REFERENCES usuarios(id))''')
    
    # Crear admin maestro global por defecto si no existe (con clave hasheada)
    # Por defecto, el usuario es 'admin' y la clave 'admin123'
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", ('admin', hash_password('admin123'), 'ADMIN_GLOBAL'))
    conn.commit()

init_db()

# --- ESTILOS CSS PREMIUM NEÓN ---
st.markdown("""
    <style>
    /* Fondo y Base */
    .stApp { background-color: #0d0d0d; color: #e0e0e0; }
    
    /* Tarjetas de Dashboard Neón */
    [data-testid="stMetricValue"] { color: #00FF00; font-size: 32px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #aaaaaa; }
    div[data-testid="stMetric"] {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        box-shadow: 0 0 10px rgba(0,255,0,0.1);
        text-align: center;
    }

    /* Login Centrado Profesional */
    .login-box {
        background-color: #161616;
        padding: 3rem; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,255,0,0.2);
        border: 1px solid #00FF00; width: 420px; text-align: center;
    }

    /* Botones Neón */
    .stButton>button {
        background-color: transparent; color: #00FF00; font-weight: bold;
        border-radius: 5px; border: 2px solid #00FF00; width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #00FF00; color: black; box-shadow: 0 0 15px rgba(0,255,0,0.5); }

    /* Estilo de tablas */
    .stDataFrame { border: 1px solid #333; border-radius: 10px; background-color: #161616; }
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

# --- SISTEMA DE LOGIN Y REGISTRO ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png")
        st.markdown('<h1 style="text-align:center; color:#00FF00;">ACCESO SOCIO ELITE</h1>', unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔑 INGRESAR", "📝 REGISTRARSE COMO SOCIO"])
        with t1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Contraseña", type="password", key="l_p")
            if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
                res = cursor.fetchone()
                if res and res[2] == hash_password(p):
                    if res[1] == 'PENDIENTE': st.warning("⚠️ Su cuenta espera aprobación de Saúl.")
                    else:
                        st.session_state['autenticado'] = True
                        st.session_state['usuario_id'] = res[0]
                        st.session_state['usuario'] = u
                        st.session_state['rango'] = res[1]
                        st.rerun()
                else: st.error("❌ Datos incorrectos.")
        with t2:
            st.write("Complete sus datos para solicitar su panel de Socio VIP.")
            nu = st.text_input("Elegir Usuario")
            np = st.text_input("Elegir Clave", type="password")
            if st.button("SOLICITAR MI PANEL SOCIO VIP"):
                if nu and np:
                    try:
                        conn = get_db(); cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, hash_password(np)))
                        conn.commit(); st.success("✅ Solicitud enviada. Contacte a Saúl para activar su panel.")
                    except: st.error("❌ El usuario ya existe.")
                else: st.warning("Por favor complete todos los campos.")
    st.stop()

# --- MENÚ LATERAL Y RUTEO ---
st.sidebar.title(f"👤 {st.session_state['usuario'].upper()}")
st.sidebar.write(f"Panel: **{st.session_state['rango'].replace('_GLOBAL', '')}**")

# Definir menús compartidos (que usan ADMIN y SOCIO VIP)
menu_items = ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN DE PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "📅 PROVEEDORES", "🗑️ ELIMINAR CUENTAS", "🔑 CAMBIAR CLAVE"]

if st.session_state['rango'] == 'ADMIN_GLOBAL':
    # El admin global tiene un menú extra para usuarios
    menu = st.sidebar.radio("Ir a:", menu_items + ["👥 USUARIOS GLOBALES", "🚪 SALIR"])
else:
    menu = st.sidebar.radio("Ir a:", menu_items + ["🚪 SALIR"])

conn = get_db()
creador_id = st.session_state['usuario_id'] # ID para vincular inventario

# --- FUNCIONES DE LOS MENÚS ---
if menu == "🚪 SALIR":
    st.session_state['autenticado'] = False; st.rerun()

elif menu == "🔑 CAMBIAR CLAVE":
    st.title("🔑 Seguridad de Socio")
    u = st.session_state['usuario']
    old_p = st.text_input("Contraseña Actual", type="password")
    new_p = st.text_input("Nueva Contraseña", type="password")
    new_p_c = st.text_input("Confirmar Nueva Contraseña", type="password")
    if st.button("ACTUALIZAR CONTRASEÑA"):
        if new_p != new_p_c: st.error("❌ Las nuevas contraseñas no coinciden.")
        else:
            cur = conn.cursor(); cur.execute("SELECT password FROM usuarios WHERE user=?", (u,))
            if cur.fetchone()[0] == hash_password(old_p):
                cur.execute("UPDATE usuarios SET password=? WHERE user=?", (hash_password(new_p), u))
                conn.commit(); st.success("✅ Actualizada."); st.rerun()
            else: st.error("❌ Contraseña actual incorrecta.")

# --- 1. DASHBOARD (CONTEXTUAL) ---
elif menu == "📊 DASHBOARD":
    st.title("📊 Resumen de Mi Negocio")
    
    # Contexto: SOCIO ve lo suyo, ADMIN ve el global
    if st.session_state['rango'] == 'ADMIN_GLOBAL':
        st.info("Vista Global Administrador: Datos de todos los socios.")
        q_cta = "SELECT COUNT(*) as t FROM cuentas"
        q_ven = "SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'"
        q_lib = "SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'"
        df_clientes_q = "SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'"
    else:
        q_cta = f"SELECT COUNT(*) as t FROM cuentas WHERE creador_id={creador_id}"
        q_ven = f"SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO' AND creador_id={creador_id}"
        q_lib = f"SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE' AND creador_id={creador_id}"
        df_clientes_q = f"SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO' AND creador_id={creador_id}"
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas Maestras", pd.read_sql_query(q_cta, conn)['t'][0])
    c2.metric("✅ Perfiles Vendidos", pd.read_sql_query(q_ven, conn)['t'][0])
    c3.metric("🔓 Perfiles Libres", pd.read_sql_query(q_lib, conn)['t'][0])
    
    st.divider()
    st.subheader("🗓️ Próximos Vencimientos a Cobrar")
    df = pd.read_sql_query(df_clientes_q, conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True, hide_index=True)

# --- 2. PLATAFORMAS (VINCVULADO AL SOCIO) ---
elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Cuentas Maestras")
    plat = st.selectbox("Elegir Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_per = PLATAFORMAS_CONFIG[plat]
    with st.form("registro"):
        c1, c2, c3 = st.columns([2,2,1])
        m, p, cost = c1.text_input("📧 Correo"), c2.text_input("🔑 Clave"), c3.number_input("💵 Costo (S/)", 0.0, step=1.0)
        f_p = st.date_input("📅 Vencimiento Proveedor", format="DD/MM/YYYY")
        st.write("---")
        per_data = []
        c_a, c_b = st.columns(2)
        for i in range(num_per):
            with c_a: n = st.text_input(f"Perfil {i+1}", f"P{i+1}", key=f"n_{i}")
            with c_b: pi = st.text_input(f"PIN {i+1}", "0000", key=f"p_{i}")
            per_data.append((n, pi))
        if st.form_submit_button("✅ ACTIVAR CUENTA"):
            cur = conn.cursor()
            try:
                # Insertar cuenta vinculada al creador
                cur.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?)", (plat, m, p, f_p.strftime("%d/%m/%Y"), cost, creador_id))
                # Insertar perfiles vinculados al creador
                for nom, pin in per_data:
                    cur.execute("INSERT INTO perfiles (email, plataforma, nombre, pin, creador_id) VALUES (?,?,?,?,?)", (m, plat, nom, pin, creador_id))
                conn.commit(); st.success("¡Cuenta subida a su inventario!"); st.rerun()
            except Exception as e: st.error(f"Error: El correo ya existe o hubo un problema ({e}).")

# --- 3. GESTIÓN DE PERFILES (ENTREGA WHATSAPP PRO) ---
elif menu == "📱 GESTIÓN DE PERFILES":
    st.title("📱 Administración y Entregas Pro")
    
    # El socio solo gestiona SUS cuentas
    q_emails = f"SELECT email FROM cuentas WHERE creador_id={creador_id}"
    emails = pd.read_sql_query(q_emails, conn)['email'].tolist()
    
    if emails:
        sel = st.selectbox("Seleccionar Cuenta:", emails)
        cta = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel}'", conn).iloc[0]
        st.warning(f"🔑 **Acceso {cta['plataforma']}:** `{cta['password']}`")
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel}' AND creador_id={creador_id}", conn)
        for _, row in perfs.iterrows():
            stat = f"🔴 {row['whatsapp']}" if row['estado'] == 'VENDIDO' else "🟢 LIBRE"
            with st.expander(f"{row['nombre']} | PIN: {row['pin']} | {stat}"):
                c1, c2 = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("WhatsApp Cliente (ej: 51930...):", key=f"wa_{row['id']}")
                    pv = c2.number_input("Precio Venta S/", value=10.0, step=1.0, key=f"pv_{row['id']}")
                    if st.button("🛒 Confirmar Venta", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} (**{d} días restantes**)")
                    
                    # FORMATO ELEGANTE CON EMOJIS (MODIFICADO COMO PEDISTE)
                    msg = (
                        f"💎 *ENTREGA DE SERVICIO* 💎\n\n"
                        f"🎬 *Plataforma:* {row['plataforma']}\n"
                        f"📧 *Correo:* `{sel}`\n"
                        f"🔑 *Contraseña:* `{cta['password']}`\n"
                        f"👤 *Perfil:* {row['nombre']}\n"
                        f"📌 *PIN:* `{row['pin']}`\n"
                        f"📅 *Vence:* {row['fecha_vence']}\n\n"
                        "🚀 *¡Gracias por tu confianza, disfruta tu servicio!* 🎬"
                    )
                    url_entrega = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg)}"
                    
                    # Botón profesional de WhatsApp
                    c1.markdown(f'<a href="{url_entrega}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; padding:10px; border-radius:5px; width:100%; border:none; font-weight:bold; cursor:pointer;">🚀 ENVIAR POR WHATSAPP</button></a>', unsafe_allow_html=True)
                    
                    st.write("")
                    cb1, cb2 = st.columns(2)
                    if cb1.button("🔄 Renovar (+30d)", key=f"r_{row['id']}"):
                        nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if cb2.button("✂️ Cortar Servicio", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()
    else: st.info("No tienes cuentas subidas. Ve a PLATAFORMAS.")

# --- 4. FINANZAS PRO (REAL SOCIO O GLOBAL ADMIN) ---
elif menu == "💰 FINANZAS PRO":
    st.title("💰 Reporte de Caja (Soles S/) ")
    
    # Contexto: SOCIO ve lo suyo, ADMIN ve el global
    if st.session_state['rango'] == 'ADMIN_GLOBAL':
        st.info("Vista Global Administrador: Balance acumulado de todos los socios.")
        q_costo = "SELECT SUM(costo) as t FROM cuentas"
        q_venta = "SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'"
    else:
        q_costo = f"SELECT SUM(costo) as t FROM cuentas WHERE creador_id={creador_id}"
        q_venta = f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND creador_id={creador_id}"

    e = pd.read_sql_query(q_costo, conn)['t'][0] or 0
    i = pd.read_sql_query(q_venta, conn)['t'][0] or 0
    gan = i - e
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1: st.markdown(f'<div class="metric-card" style="border-left-color:#ff4b4b;"><h3>📉 EGRESOS (Proveedores)</h3><h2>{moneda(e)}</h2></div>', unsafe_allow_html=True)
    with col_t2: st.markdown(f'<div class="metric-card" style="border-left-color:#25D366;"><h3>📈 INGRESOS (Ventas)</h3><h2>{moneda(i)}</h2></div>', unsafe_allow_html=True)
    color_gan = "#25D366" if gan >= 0 else "#ff4b4b"
    with col_t3: st.markdown(f'<div class="metric-card" style="border-left-color:{color_gan};"><h3>🤑 GANANCIA NETA</h3><h2>{moneda(gan)}</h2></div>', unsafe_allow_html=True)
    
    # Tabla resumen
    st.divider()
    resumen = []
    # Usar dict para filtrar creador en el bucle
    for p in PLATAFORMAS_CONFIG.keys():
        if st.session_state['rango'] == 'ADMIN_GLOBAL':
            q_ep = f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}'"
            q_ip = f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}'"
        else:
            q_ep = f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}' AND creador_id={creador_id}"
            q_ip = f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}' AND creador_id={creador_id}"
            
        ep = pd.read_sql_query(q_ep, conn)['t'][0] or 0
        ip = pd.read_sql_query(q_ip, conn)['t'][0] or 0
        resumen.append({"Plataforma": p, "Egresos": ep, "Ingresos": ip, "Ganancia": ip-ep})
    st.table(pd.DataFrame(resumen))

# --- RESTO DE MENÚS (REMODELADOS ÉLITE Y CONTEXTUALES) ---
elif menu == "🔔 NOTIFICACIONES":
    st.title("🔔 Central de Cobranza (3 Días)")
    # El socio solo cobra a SUS clientes
    df_n = pd.read_sql_query(f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND creador_id={creador_id}", conn)
    for _, r in df_n.iterrows():
        d = calcular_dias(r['fecha_vence'])
        if d <= 3:
            col1, col2 = st.columns([3,1])
            col1.warning(f"⚠️ {r['nombre']} ({r['plataforma']}) vence en {max(0, d)} días ({r['fecha_vence']})")
            msg = f"👋 Hola {r['nombre']}, recordatorio de *{st.session_state['usuario']} Streaming* 🎬. Tu perfil de {r['plataforma']} vence pronto. ¿Deseas renovar?"
            col2.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#008CBA; color:white; padding:10px; border-radius:5px; border:none; width:100%; cursor:pointer;">🔔 RECORDAR</button></a>', unsafe_allow_html=True)

elif menu == "🗑️ ELIMINAR CUENTAS":
    st.title("🗑️ Borrar Cuentas y Perfiles")
    st.error("¡Cuidado! Esta acción borra la cuenta y sus perfiles de su inventario.")
    # El socio solo borra SUS cuentas
    df_del = pd.read_sql_query(f"SELECT id, plataforma, email FROM cuentas WHERE creador_id={creador_id}", conn)
    for _, r in df_del.iterrows():
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"📺 **{r['plataforma']}** | `{r['email']}`")
        if c2.button("🗑️", key=f"d_{r['id']}"):
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
            cursor.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
            conn.commit(); st.rerun()

elif menu == "📅 PROVEEDORES":
    st.title("📅 Vencimientos Maestros (Mi Inventario)")
    st.dataframe(pd.read_sql_query(f"SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas WHERE creador_id={creador_id}", conn), use_container_width=True)

# --- MENÚ EXCLUSIVO ADMIN GLOBAL (GESTIÓN DE SOCIOS) ---
elif menu == "👥 USUARIOS GLOBALES":
    st.title("👥 Solicitudes y Usuarios Saúl Elite")
    st.subheader("⏳ Socios Pendientes de Activación")
    conn = get_db(); cursor = conn.cursor()
    pends = pd.read_sql_query("SELECT id, user, password FROM usuarios WHERE rango='PENDIENTE'", conn)
    if not pends.empty:
        for _, r in pends.iterrows():
            c1, c2 = st.columns([4,1])
            c1.write(f"👤 Solicitud de: **{r['user']}** (Pass: {r['password']})")
            if c2.button("✅ ACTIVAR COMO SOCIO VIP", key=f"u_{r['id']}"):
                cursor.execute(f"UPDATE usuarios SET rango='SOCIO VIP' WHERE id={r['id']}")
                conn.commit(); st.rerun()
    else: st.info("No hay solicitudes pendientes.")
    st.divider()
    st.subheader("👥 Lista General de Socios")
    st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)