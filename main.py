import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming Pro V5.4", page_icon="🎬", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS BLINDADA v5.4 ---
# Cambiamos el nombre para asegurar que se cree la estructura correcta sin errores
DB_NAME = 'db_streaming_saul_v54.db'

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Tabla Usuarios (Login y Seguridad)
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                      (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT DEFAULT 'CLIENTE')''')
    # Tabla Cuentas Completas (Egresos)
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT, costo REAL DEFAULT 0)''')
    # Tabla Perfiles Individuales (Ingresos)
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, precio_venta REAL DEFAULT 0)''')
    
    # Crear admin maestro por defecto si no existe
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

# --- SISTEMA DE LOGIN Y SEGURIDAD ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

def login():
    st.title("🔐 Acceso Saúl Streaming Pro")
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
                    st.warning("⚠️ Tu cuenta espera activación del administrador.")
                else:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = u
                    st.session_state['rango'] = res[0]
                    st.rerun()
            else: st.error("Usuario o contraseña incorrectos.")

    with tab2:
        st.write("Crea tu cuenta de cliente.")
        new_u = st.text_input("Nuevo Usuario", key="r_user")
        new_p = st.text_input("Nueva Contraseña", type="password", key="r_pass")
        if st.button("Solicitar Acceso"):
            if new_u and new_p:
                conn = get_db(); cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", (new_u, new_p, 'PENDIENTE'))
                    conn.commit()
                    st.success("✅ Solicitud enviada correctamente.")
                except: st.error("❌ El usuario ya existe.")
            else: st.warning("Completa todos los campos.")

# --- MENÚ LATERAL Y RUTEO ---
if not st.session_state['autenticado']:
    login()
    st.stop()

st.sidebar.title(f"👤 {st.session_state['usuario']}")
st.sidebar.write(f"Rango: **{st.session_state['rango']}**")

if st.session_state['rango'] == 'ADMIN':
    menu = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "💰 Finanzas Pro", "📅 Proveedores", "🗑️ Eliminar Cuentas", "👥 Usuarios", "🔑 Cambiar Mi Clave", "🚪 Salir"])
else:
    menu = st.sidebar.radio("Ir a:", ["📱 Mis Servicios", "🔑 Cambiar Mi Clave", "🚪 Salir"])

# --- FUNCIONES DE LOS MENÚS ---

if menu == "🚪 Salir":
    st.session_state['autenticado'] = False
    st.rerun()

elif menu == "🔑 Cambiar Mi Clave":
    st.title("🔑 Cambiar Mi Contraseña de Acceso")
    u = st.session_state['usuario']
    old_p = st.text_input("Contraseña Actual", type="password")
    new_p = st.text_input("Nueva Contraseña", type="password")
    new_p_c = st.text_input("Confirmar Nueva Contraseña", type="password")
    
    if st.button("Actualizar Contraseña"):
        if new_p != new_p_c:
            st.error("❌ Las nuevas contraseñas no coinciden.")
        else:
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT password FROM usuarios WHERE user=?", (u,))
            current_p_db = cursor.fetchone()[0]
            
            if old_p == current_p_db:
                cursor.execute("UPDATE usuarios SET password=? WHERE user=?", (new_p, u))
                conn.commit()
                st.success("✅ Contraseña actualizada correctamente.")
            else:
                st.error("❌ La contraseña actual es incorrecta.")

elif menu == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    conn = get_db()
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas", pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0])
    c2.metric("✅ Vendidos", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0])
    c3.metric("🔓 Libres", pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0])
    
    st.divider()
    st.subheader("👥 Clientes y Días Restantes")
    df = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Cuentas Completas")
    plat_sel = st.selectbox("Selecciona la Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_per = PLATAFORMAS_CONFIG[plat_sel]
    
    with st.form("reg_form"):
        c1, c2, c3 = st.columns([2,2,1])
        mail = c1.text_input("📧 Correo")
        pasw = c2.text_input("🔑 Clave")
        costo = c3.number_input("💵 Costo (S/)", min_value=0.0, step=1.0)
        f_p = st.date_input("📅 Vence Proveedor", format="DD/MM/YYYY")
        
        per_list = []
        st.write("---")
        st.write("📝 **Nombres y PINs de Perfiles**")
        cols = st.columns(2)
        for i in range(num_per):
            with cols[0]: n = st.text_input(f"Nombre P{i+1}", f"P{i+1}", key=f"n_{i}")
            with cols[1]: p = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
            per_list.append((n, p))
            
        if st.form_submit_button("🚀 GUARDAR PLATAFORMA"):
            if mail and pasw:
                conn = get_db(); cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", (plat_sel, mail, pasw, f_p.strftime("%d/%m/%Y"), costo))
                    for nom, pin in per_list:
                        cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", (mail, plat_sel, nom, pin))
                    conn.commit(); st.success("✅ Cuenta Creada"); st.rerun()
                except: st.error("❌ Error: El correo ya existe.")

elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Panel de Ventas y Entregas")
    conn = get_db()
    
    # Asegurar que haya cuentas para filtrar
    p_filter = st.selectbox("🔍 Filtrar Plataforma:", ["TODAS"] + list(PLATAFORMAS_CONFIG.keys()))
    q_mail = "SELECT email FROM cuentas"
    if p_filter != "TODAS": q_mail += f" WHERE plataforma='{p_filter}'"
    emails = pd.read_sql_query(q_mail, conn)['email'].tolist()
    
    if not emails:
        st.warning("📂 No hay cuentas registradas en esta categoría.")
    else:
        sel_m = st.selectbox("📩 Selecciona la cuenta:", emails)
        # Traer datos de la cuenta completa
        cta_data = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel_m}'", conn).iloc[0]
        st.markdown(f"### 🔑 Clave {cta_data['plataforma']}: `{cta_data['password']}`")
        
        # Traer perfiles individuales
        perfiles = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_m}'", conn)
        
        for _, row in perfiles.iterrows():
            stat = f"🔴 {row['whatsapp']} (S/ {row['precio_venta']})" if row['estado'] == 'VENDIDO' else "🟢 LIBRE"
            with st.expander(f"{row['nombre']} | PIN: {row['pin']} | {stat}"):
                c1, c2 = st.columns(2)
                
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("📱 WhatsApp Cliente:", key=f"wa_{row['id']}")
                    pv = c2.number_input("💵 Precio Venta (S/):", min_value=0.0, value=10.0, step=1.0, key=f"pv_{row['id']}")
                    if st.button("🛒 Confirmar Venta", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} (**{d} días restantes**)")
                    # FORMATO ELEGANTE DE ENTREGA CON EMOJIS
                    msg = (
                        f"💎 *ENTREGA DE CUENTA - {cta['plataforma']}* 💎\n\n"
                        f"📧 *Correo:* `{sel_m}`\n🔑 *Clave:* `{cta_data['password']}`\n"
                        f"👤 *Perfil:* {row['nombre']}\n📌 *PIN:* `{row['pin']}`\n"
                        f"📅 *Vence:* {row['fecha_vence']}\n\n"
                        "🎬 *¡Disfruta tu servicio con Saúl Streaming!* 🚀"
                    )
                    url_e = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg)}"
                    c1.markdown(f'<a href="{url_e}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer; width:100%; font-weight:bold;">🚀 ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)
                    
                    if c2.button("✂️ Cortar Servicio", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

elif menu == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza WhatsApp")
    conn = get_db()
    df_n = pd.read_sql_query("SELECT * FROM perfiles WHERE estado='VENDIDO'", conn)
    
    if df_n.empty:
        st.success("🎉 No hay cobros pendientes.")
    else:
        for _, r in df_n.iterrows():
            d = calcular_dias(r['fecha_vence'])
            if d <= 3:
                icon = "⏰" if d <= 1 else "🗓️"
                with st.container():
                    col1, col2 = st.columns([3,1])
                    col1.warning(f"{icon} {r['nombre']} ({r['plataforma']}) vence en **{max(0, d)} días** ({r['fecha_vence']})")
                    msg = f"👋 Hola {r['nombre']}, te saludamos de Saúl Streaming 🎬. Te recordamos que tu perfil de {r['plataforma']} vence el {r['fecha_vence']}. ¿Renovamos?"
                    url_c = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg)}"
                    col2.markdown(f'<a href="{url_c}" target="_blank" style="text-decoration:none;"><button style="background-color:#008CBA; color:white; padding:5px; border:none; border-radius:5px; cursor:pointer; width:100%;">🔔 AVISAR</button></a>', unsafe_allow_html=True)
                    st.divider()

elif menu == "💰 Finanzas Pro":
    st.title("💰 Balance Financiero Real Saúl")
    conn = get_db()
    # Egresos: Suma del costo de las CUENTAS COMPLETAS
    e = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    # Ingresos: Suma del precio de venta de los PERFILES VENDIDOS
    i = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📉 Egresos (Inversión)", f"S/ {e:.2f}")
    c2.metric("📈 Ingresos (Ventas Realizadas)", f"S/ {i:.2f}")
    c3.metric("🤑 Ganancia Neta Real", f"S/ {i-e:.2f}")
    
    st.divider()
    st.subheader("📊 Desglose por Plataforma")
    data_fin = []
    for p in PLATAFORMAS_CONFIG.keys():
        e_p = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}'", conn)['t'][0] or 0
        i_p = pd.read_sql_query(f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}'", conn)['t'][0] or 0
        data_fin.append({"PLATAFORMA": p, "Egresos": f"S/ {e_p:.2f}", "Ingresos": f"S/ {i_p:.2f}", "Ganancia": f"S/ {i_p - e_p:.2f}"})
    st.table(pd.DataFrame(data_fin))

elif menu == "🗑️ Eliminar Cuentas":
    st.title("🗑️ Borrar Cuentas y Perfiles")
    st.warning("⚠️ Cuidado: Al eliminar una cuenta se borrarán todos sus perfiles asociados permanentemente.")
    conn = get_db()
    df_d = pd.read_sql_query("SELECT id, plataforma, email FROM cuentas", conn)
    
    for _, r in df_d.iterrows():
        c1, c2 = st.columns([4,1])
        c1.write(f"📺 **{r['plataforma']}** | 📧 {r['email']}")
        if c2.button("🗑️ ELIMINAR", key=f"d_{r['id']}"):
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
            cursor.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
            conn.commit(); st.rerun()
            
elif menu == "👥 Usuarios":
    st.title("👥 Gestión de Solicitudes y Usuarios")
    conn = get_db(); cursor = conn.cursor()
    # Solicitudes
    st.subheader("⏳ Solicitudes Pendientes")
    pend = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
    if not pend.empty:
        for _, r in pend.iterrows():
            c1, c2 = st.columns([3,1])
            c1.write(f"👤 **{r['user']}**")
            if c2.button("✅ ACTIVAR CLIENTE", key=f"a_{r['id']}"):
                cursor.execute(f"UPDATE usuarios SET rango='CLIENTE' WHERE id={r['id']}")
                conn.commit(); st.rerun()
    else: st.info("No hay solicitudes pendientes.")
    st.divider()
    # Lista de todos los usuarios
    st.subheader("👥 Lista General de Usuarios")
    st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)

elif menu == "📅 Proveedores":
    st.title("📅 Vencimientos de Cuentas Maestras")
    conn = get_db()
    df_prov = pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas", conn)
    st.dataframe(df_prov, use_container_width=True)

elif menu == "📱 Mis Servicios":
    st.title("📱 Mis Servicios Comprados")
    conn = get_db()
    u = st.session_state['usuario']
    # Buscamos servicios donde el nombre de usuario coincida con el WhatsApp del cliente
    df_m = pd.read_sql_query(f"SELECT plataforma, nombre, pin, fecha_vence FROM perfiles WHERE whatsapp LIKE '%{u}%' AND estado='VENDIDO'", conn)
    if not df_m.empty:
        df_m['Días Restantes'] = df_m['fecha_vence'].apply(calcular_dias)
        st.table(df_m)
    else: st.info("📂 No tienes servicios activos vinculados a este usuario.")