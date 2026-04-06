import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Saúl Streaming Pro V6.0", page_icon="🎬", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
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

def formata_moneda(valor):
    return f"S/ {valor:,.2f}"

# --- LOGIN PRO SYSTEM ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    # CSS para el Login Pro
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #1e1e1e 0%, #0d0d0d 100%);
            display: flex; align-items: center; justify-content: center;
        }
        .login-box {
            background-color: rgba(30, 30, 30, 0.9);
            padding: 3rem; border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,255,0,0.2);
            border: 1px solid #333; width: 450px; text-align: center;
        }
        .stButton>button {
            background-color: #00ff00; color: black; font-weight: bold;
            border-radius: 5px; border: none; width: 100%;
        }
        .stButton>button:hover { background-color: #00cc00; color: white; }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # Imagen Hacker (Puedes cambiar el link aquí)
        st.image("https://img.freepik.com/vector-premium/hacker-gafas-casco-auriculares_116348-75.jpg", width=150)
        
        st.title("👨‍💻 ACCESO SISTEMA SAÚL")
        t1, t2 = st.tabs(["Ingresar", "Registrarse"])
        with t1:
            u = st.text_input("Usuario", key="l_u")
            p = st.text_input("Contraseña", type="password", key="l_p")
            if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT rango FROM usuarios WHERE user=? AND password=?", (u, p))
                res = cursor.fetchone()
                if res:
                    if res[0] == 'PENDIENTE': st.warning("Tu cuenta está en espera.")
                    else:
                        st.session_state['autenticado'] = True
                        st.session_state['usuario'] = u
                        st.session_state['rango'] = res[0]
                        st.rerun()
                else: st.error("Datos incorrectos.")
        with t2:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Clave", type="password")
            if st.button("📩 SOLICITAR ACCESO"):
                try:
                    conn = get_db(); cursor = conn.cursor()
                    cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, np))
                    conn.commit(); st.success("Solicitud enviada.")
                except: st.error("El usuario ya existe.")
        st.markdown('</div>', unsafe_allow_html=True)
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
    st.session_state['autenticado'] = False; st.rerun()

elif menu == "📊 Dashboard":
    st.title("📊 Resumen General")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas Maestras", pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0])
    c2.metric("✅ Perfiles Vendidos", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0])
    c3.metric("🔓 Perfiles Libres", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0])
    
    st.subheader("👥 Clientes Próximos a Vencer")
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
        costo = c3.number_input("Costo Cuenta Completa (S/)", min_value=0.0, step=1.0)
        f_v = st.date_input("Vence Proveedor", format="DD/MM/YYYY")
        st.write("---")
        cols = st.columns(2)
        for i in range(PLATAFORMAS_CONFIG[plat]):
            with cols[0]: n = st.text_input(f"Nombre P{i+1}", f"P{i+1}", key=f"n_{i}")
            with cols[1]: p = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
        if st.form_submit_button("🚀 GUARDAR PLATAFORMA"):
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", (plat, mail, pasw, f_v.strftime("%d/%m/%Y"), costo))
                for i in range(PLATAFORMAS_CONFIG[plat]):
                    cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", (mail, plat, st.session_state[f"n_{i}"], st.session_state[f"p_{i}"]))
                conn.commit(); st.success("✅ Cuenta registrada."); st.rerun()
            except: st.error("Error: El correo ya existe.")

elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Panel de Ventas")
    emails = pd.read_sql_query("SELECT email FROM cuentas", conn)['email'].tolist()
    if emails:
        sel_m = st.selectbox("Cuenta:", emails)
        cta = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel_m}'", conn).iloc[0]
        st.info(f"🔑 Clave {cta['plataforma']}: `{cta['password']}`")
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_m}'", conn)
        for _, row in perfs.iterrows():
            stat = f"🔴 {row['whatsapp']} (S/ {row['precio_venta']:.2f})" if row['estado'] == 'VENDIDO' else "🟢 LIBRE"
            with st.expander(f"{row['nombre']} | PIN: {row['pin']} | {stat}"):
                c1, c2 = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("WhatsApp Cliente (ej: 51930...):", key=f"wa_{row['id']}")
                    pv = c2.number_input("Precio de Venta (S/):", min_value=0.0, step=1.0, value=10.0, key=f"pv_{row['id']}")
                    if st.button("🛒 Confirmar Venta", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} (**{d} días restantes**)")
                    msg = f"💎 *ENTREGA {row['plataforma']}* 💎\n📧 `{sel_m}`\n🔑 `{cta['password']}`\n👤 {row['nombre']}\n📌 {row['pin']}\n📅 Vence: {row['fecha_vence']}\n\n🎬 *¡Disfruta tu servicio con Saúl Streaming!* Prohibido cambiar datos."
                    url_entrega = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg)}"
                    
                    # BOTÓN VERDE PROFESIONAL DE WHATSAPP
                    c1.markdown(f'<a href="{url_entrega}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer; width:100%; font-weight:bold; font-size:16px;">🚀 ENVIAR POR WHATSAPP</button></a>', unsafe_allow_html=True)
                    
                    if c2.button("🔄 Renovar (+30d)", key=f"r_{row['id']}"):
                        fv = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{fv}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if c2.button("✂️ Cortar Servicio", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

elif menu == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza (Notificaciones)")
    conn = get_db()
    
    # Notificaciones arregladas para todas las plataformas
    df_n = pd.read_sql_query("SELECT * FROM perfiles WHERE estado='VENDIDO'", conn)
    
    if df_n.empty:
        st.success("🎉 No hay perfiles vendidos actualmente.")
    else:
        # Calcular días y ordenar por urgencia
        df_n['DÍAS'] = df_n['fecha_vence'].apply(calcular_dias)
        df_n = df_n.sort_values('DÍAS')
        
        # Mostrar solo los que vencen pronto (ejemplo: 3 días o menos)
        for _, r in df_n.iterrows():
            if r['DÍAS'] <= 3:
                icon = "⏰" if r['DÍAS'] <= 1 else "🗓️"
                with st.container():
                    col1, col2 = st.columns([3,1])
                    col1.warning(f"{icon} **{r['plataforma']}** | Perfil: *{r['nombre']}* | Vence en: **{max(0, r['DÍAS'])} días** ({r['fecha_vence']})")
                    
                    msg_cobro = f"👋 Hola *{r['nombre']}*, te saludamos de Saúl Streaming 🎬. Te recordamos que tu perfil de *{r['plataforma']}* vence el *{r['fecha_vence']}*. ¿Deseas renovar para no perder tu acceso?"
                    url_cobro = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg_cobro)}"
                    
                    # Botón profesional de cobro
                    col2.markdown(f'<a href="{url_cobro}" target="_blank" style="text-decoration:none;"><button style="background-color:#008CBA; color:white; padding:5px; border:none; border-radius:5px; cursor:pointer; width:100%;">🔔 RECORDAR</button></a>', unsafe_allow_html=True)
                    st.divider()

elif menu == "💰 Finanzas Pro":
    st.title("💰 Reporte Real Saúl (Soles S/) ")
    e = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    i = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    
    c1, c2, c3 = st.columns(3)
    
    # Formateo de moneda peruana S/ con 2 decimales
    c1.metric("📉 Egresos (Inversión)", formata_moneda(e))
    c2.metric("📈 Ingresos (Ventas)", formata_moneda(i))
    c3.metric("🤑 Ganancia Neta", formata_moneda(i-e))
    
    st.divider()
    st.subheader("📊 Resumen por Plataforma")
    resumen = []
    for p in PLATAFORMAS_CONFIG.keys():
        ep = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}'", conn)['t'][0] or 0
        ip = pd.read_sql_query(f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}'", conn)['t'][0] or 0
        resumen.append({
            "Plataforma": p, 
            "Egresos (S/)": f"{ep:,.2f}", 
            "Ingresos (S/)": f"{ip:,.2f}", 
            "Ganancia (S/)": f"{(ip-ep):,.2f}"
        })
    st.table(pd.DataFrame(resumen))

elif menu == "🗑️ Eliminar Cuentas":
    st.title("🗑️ Borrar Cuentas Caídas")
    df_d = pd.read_sql_query("SELECT id, plataforma, email FROM cuentas", conn)
    for _, r in df_d.iterrows():
        col1, col2 = st.columns([4,1])
        col1.write(f"📺 **{r['plataforma']}** | {r['email']}")
        if col2.button("🗑️ ELIMINAR", key=f"d_{r['id']}"):
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
            cursor.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
            conn.commit(); st.rerun()

elif menu == "👥 Usuarios":
    st.title("👥 Gestión de Usuarios")
    pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
    for _, r in pends.iterrows():
        col1, col2 = st.columns([3,1])
        col1.write(f"👤 **{r['user']}**")
        if col2.button("✅ ACTIVAR", key=f"acc_{r['id']}"):
            conn.cursor().execute(f"UPDATE usuarios SET rango='CLIENTE' WHERE id={row['id']}")
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
            conn.commit(); st.success("✅ Clave actualizada.")
        else: st.error("Clave incorrecta.")

elif menu == "📅 Proveedores":
    st.title("📅 Vencimientos Proveedor")
    st.dataframe(pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas", conn), use_container_width=True)

elif menu == "📱 Mis Servicios":
    st.title("📱 Mis Servicios Comprados")
    u = st.session_state['usuario']
    df_m = pd.read_sql_query(f"SELECT plataforma, nombre, pin, fecha_vence FROM perfiles WHERE (whatsapp LIKE '%{u}%' OR nombre LIKE '%{u}%') AND estado='VENDIDO'", conn)
    if not df_m.empty:
        df_m['Días Restantes'] = df_m['fecha_vence'].apply(calcular_dias)
        st.table(df_m)
    else: st.info("No tienes perfiles activos.")