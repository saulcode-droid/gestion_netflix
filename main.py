import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Pro Streaming - Sistema VIP", page_icon="💻", layout="wide")

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

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    /* Tarjetas de Dashboard */
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00FF00;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    /* Login Centrado */
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 40px;
        background: #111;
        border-radius: 20px;
        border: 1px solid #333;
        text-align: center;
    }
    /* Botón WhatsApp */
    .btn-wa {
        background-color: #25D366;
        color: white !important;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        width: 100%;
        text-align: center;
    }
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
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png") # Imagen Hacker
        st.markdown('<h1 style="text-align:center; color:#00FF00;">SISTEMA SAÚL PRO</h1>', unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔑 INGRESAR", "📝 REGISTRO"])
        
        with t1:
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.button("🚀 ENTRAR AL SISTEMA", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT rango FROM usuarios WHERE user=? AND password=?", (u, p))
                res = cursor.fetchone()
                if res:
                    if res[0] == 'PENDIENTE': st.warning("Cuenta pendiente de activación.")
                    else:
                        st.session_state['autenticado'], st.session_state['usuario'], st.session_state['rango'] = True, u, res[0]
                        st.rerun()
                else: st.error("Acceso denegado.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔐 Olvidé mi contraseña", use_container_width=True):
                st.info("ℹ️ Solicita el restablecimiento a Saúl vía WhatsApp indicando tu usuario.")
        
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Clave", type="password")
            if st.button("SOLICITAR ACCESO"):
                try:
                    conn = get_db(); cursor = conn.cursor()
                    cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, np))
                    conn.commit(); st.success("Solicitud enviada con éxito.")
                except: st.error("Ese usuario ya existe.")
    st.stop()

# --- MENÚ PRINCIPAL ---
st.sidebar.title(f"👤 {st.session_state['usuario']}")
if st.session_state['rango'] == 'ADMIN':
    menu = st.sidebar.radio("Menú Administrador:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "💰 Finanzas Pro", "📅 Proveedores", "🗑️ Eliminar Cuentas", "👥 Usuarios", "🔑 Cambiar Clave", "🚪 Salir"])
else:
    menu = st.sidebar.radio("Menú Cliente:", ["📱 Mis Servicios", "🔑 Cambiar Clave", "🚪 Salir"])

conn = get_db()

# --- LÓGICA DE MENÚS ---
if menu == "🚪 Salir":
    st.session_state['autenticado'] = False; st.rerun()

elif menu == "📊 Dashboard":
    st.title("📊 Resumen Ejecutivo de Ventas")
    
    # Tarjetas Pro
    c1, c2, c3 = st.columns(3)
    val1 = pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0]
    val2 = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0]
    val3 = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0]
    
    with c1: st.markdown(f'<div class="metric-card"><h3>📦 Cuentas</h3><h2>{val1}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card" style="border-left-color:#25D366;"><h3>✅ Vendidos</h3><h2>{val2}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card" style="border-left-color:#FBC02D;"><h3>🔓 Disponibles</h3><h2>{val3}</h2></div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("🗓️ Próximos Vencimientos (30 días)")
    df = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True, hide_index=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Alta de Nuevas Cuentas")
    plat = st.selectbox("Elegir Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    with st.form("registro"):
        c1, c2, c3 = st.columns([2,2,1])
        m, p, cost = c1.text_input("Correo"), c2.text_input("Clave"), c3.number_input("Costo S/", 0.0)
        f = st.date_input("Vencimiento Proveedor", format="DD/MM/YYYY")
        st.write("---")
        # Perfiles en 2 columnas como pediste
        per_data = []
        col_a, col_b = st.columns(2)
        for i in range(PLATAFORMAS_CONFIG[plat]):
            with col_a: n = st.text_input(f"Nombre P{i+1}", f"P{i+1}", key=f"n_{i}")
            with col_b: pi = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
            per_data.append((n, pi))
        if st.form_submit_button("✅ ACTIVAR PLATAFORMA"):
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", (plat, m, p, f.strftime("%d/%m/%Y"), cost))
                for nom, pin in per_data:
                    cur.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", (m, plat, nom, pin))
                conn.commit(); st.success("¡Cuenta subida!"); st.rerun()
            except: st.error("El correo ya existe.")

elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Administración y Entregas")
    emails = pd.read_sql_query("SELECT email FROM cuentas", conn)['email'].tolist()
    if emails:
        sel = st.selectbox("Seleccionar Cuenta:", emails)
        cta = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel}'", conn).iloc[0]
        st.info(f"🔑 **Acceso {cta['plataforma']}:** `{cta['password']}`")
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel}'", conn)
        for _, row in perfs.iterrows():
            stat = f"🔴 {row['whatsapp']}" if row['estado'] == 'VENDIDO' else "🟢 LIBRE"
            with st.expander(f"{row['nombre']} | {stat}"):
                c1, c2 = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("WhatsApp:", key=f"wa_{row['id']}")
                    pv = c2.number_input("Precio Venta S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("🛒 Confirmar Venta", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} (**{d} días restantes**)")
                    msg = f"💎 *ENTREGA {row['plataforma']}* 💎\n📧 `{sel}`\n🔑 `{cta['password']}`\n👤 {row['nombre']}\n📌 {row['pin']}\n📅 Vence: {row['fecha_vence']}"
                    # BOTÓN DE WHATSAPP REAL
                    st.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" class="btn-wa">🚀 ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
                    st.write("")
                    col_b1, col_b2 = st.columns(2)
                    if col_b1.button("🔄 Renovar (+30d)", key=f"r_{row['id']}"):
                        nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if col_b2.button("✂️ Cortar Servicio", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

elif menu == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza Inteligente")
    # Buscamos todos los vendidos para notificar
    df_not = pd.read_sql_query("SELECT * FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df_not.empty:
        df_not['DÍAS'] = df_not['fecha_vence'].apply(calcular_dias)
        vencidos = df_not[df_not['DÍAS'] <= 3].sort_values('DÍAS')
        if vencidos.empty: st.success("✅ Todo al día. Ningún perfil vence pronto.")
        for _, r in vencidos.iterrows():
            with st.container():
                c1, c2 = st.columns([3, 1])
                c1.warning(f"⚠️ **{r['plataforma']}** | {r['nombre']} vence en {r['DÍAS']} días ({r['fecha_vence']})")
                msg = f"Hola {r['nombre']}, te saludamos de Saúl Streaming 🎬. Tu perfil de {r['plataforma']} vence el {r['fecha_vence']}. ¿Deseas renovar?"
                c2.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#008CBA; color:white; padding:8px; border-radius:5px; width:100%; border:none; cursor:pointer;">🔔 AVISAR</button></a>', unsafe_allow_html=True)
                st.divider()
    else: st.info("No hay ventas registradas.")

elif menu == "💰 Finanzas Pro":
    st.title("💰 Balance de Caja (Soles S/) ")
    egresos = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    ingresos = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    c1, c2, c3 = st.columns(3)
    c1.metric("📉 Egresos (Costos)", moneda(egresos))
    c2.metric("📈 Ingresos (Ventas)", moneda(ingresos))
    c3.metric("🤑 Ganancia Real", moneda(ingresos - egresos))
    st.divider()
    # Tabla resumen
    res = []
    for p in PLATAFORMAS_CONFIG.keys():
        ep = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}'", conn)['t'][0] or 0
        ip = pd.read_sql_query(f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}'", conn)['t'][0] or 0
        res.append({"Plataforma": p, "Egresos": moneda(ep), "Ingresos": moneda(ip), "Ganancia": moneda(ip-ep)})
    st.table(pd.DataFrame(res))

elif menu == "🗑️ Eliminar Cuentas":
    st.title("🗑️ Gestión de Bajas")
    df_del = pd.read_sql_query("SELECT id, plataforma, email FROM cuentas", conn)
    for _, r in df_del.iterrows():
        c1, c2 = st.columns([4, 1])
        c1.write(f"📺 **{r['plataforma']}** | {r['email']}")
        if c2.button("🗑️ ELIMINAR", key=f"del_{r['id']}"):
            cur = conn.cursor()
            cur.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
            cur.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
            conn.commit(); st.rerun()

elif menu == "👥 Usuarios":
    st.title("👥 Control de Usuarios")
    pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
    for _, r in pends.iterrows():
        c1, c2 = st.columns([3, 1])
        c1.write(f"👤 Solicitud de: **{r['user']}**")
        if c2.button("✅ ACTIVAR", key=f"u_{r['id']}"):
            conn.cursor().execute(f"UPDATE usuarios SET rango='CLIENTE' WHERE id={r['id']}")
            conn.commit(); st.rerun()
    st.divider()
    st.write("Usuarios en el sistema:")
    st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)

elif menu == "🔑 Cambiar Clave":
    st.title("🔑 Seguridad")
    cp = st.text_input("Clave Actual", type="password")
    np = st.text_input("Nueva Clave", type="password")
    if st.button("ACTUALIZAR"):
        cur = conn.cursor()
        cur.execute("SELECT password FROM usuarios WHERE user=?", (st.session_state['usuario'],))
        if cur.fetchone()[0] == cp:
            cur.execute("UPDATE usuarios SET password=? WHERE user=?", (np, st.session_state['usuario']))
            conn.commit(); st.success("¡Clave actualizada!")
        else: st.error("Clave actual incorrecta.")

elif menu == "📅 Proveedores":
    st.title("📅 Lista de Proveedores Maestros")
    st.dataframe(pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas", conn), use_container_width=True)

elif menu == "📱 Mis Servicios":
    st.title("📱 Mi Zona de Cliente")
    u = st.session_state['usuario']
    df_m = pd.read_sql_query(f"SELECT plataforma, nombre, pin, fecha_vence FROM perfiles WHERE (whatsapp LIKE '%{u}%' OR nombre LIKE '%{u}%') AND estado='VENDIDO'", conn)
    if not df_m.empty:
        df_m['Días Restantes'] = df_m['fecha_vence'].apply(calcular_dias)
        st.table(df_m)
    else: st.info("No tienes perfiles activos vinculados.")