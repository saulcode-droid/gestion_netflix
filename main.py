import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAÚL STREAMING ELITE V9", page_icon="💎", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_final_v9.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, 
                       fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", ('admin', hash_pass('admin123'), 'ADMIN'))
    conn.commit()

init_db()

# --- ESTILOS CSS PROFESIONALES (DARK ELITE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; }
    .card-pro {
        padding: 25px; border-radius: 15px; border: 1px solid #1e2530;
        background: linear-gradient(145deg, #141a24, #0b0e14);
        box-shadow: 5px 5px 15px #05070a, -5px -5px 15px #11171e;
        margin-bottom: 20px;
    }
    .stMetric { background-color: #141a24; padding: 15px; border-radius: 12px; border: 1px solid #1e2530; }
    h1, h2, h3 { text-transform: uppercase; letter-spacing: 1px; color: #ffffff; }
    .stButton>button { border-radius: 8px; font-weight: bold; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(valor):
    return f"S/ {valor:,.2f}"

def calcular_dias(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

# --- SISTEMA DE LOGIN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.5, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.image("https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png", width=180)
        st.markdown("</div>", unsafe_allow_html=True)
        st.title("🛡️ ACCESO SISTEMA VIP")
        t_login, t_reg = st.tabs(["INGRESAR", "REGISTRARSE"])
        
        with t_login:
            u = st.text_input("USUARIO", placeholder="Ingrese su usuario")
            p = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••")
            if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
                res = cursor.fetchone()
                if res and res[2] == hash_pass(p):
                    if res[1] == 'PENDIENTE': st.warning("SU CUENTA ESTÁ EN ESPERA DE ACTIVACIÓN.")
                    else:
                        st.session_state['auth'], st.session_state['u_id'], st.session_state['u_nom'], st.session_state['u_ran'] = True, res[0], u, res[1]
                        st.rerun()
                else: st.error("DATOS INCORRECTOS")
            
            if st.button("❓ OLVIDÉ MI CONTRASEÑA", use_container_width=True):
                st.info("POR FAVOR, CONTACTE AL ADMINISTRADOR SAÚL PARA RESTABLECER SU CLAVE.")
        
        with t_reg:
            nu = st.text_input("NUEVO USUARIO")
            np = st.text_input("NUEVA CONTRASEÑA", type="password")
            if st.button("📩 SOLICITAR ACCESO", use_container_width=True):
                if nu and np:
                    try:
                        conn = get_db(); cursor = conn.cursor()
                        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, hash_pass(np)))
                        conn.commit(); st.success("SOLICITUD ENVIADA CON ÉXITO.")
                    except: st.error("EL USUARIO YA EXISTE.")
    st.stop()

# --- SIDEBAR ELITE ---
st.sidebar.title(f"👤 {st.session_state['u_nom'].upper()}")
menu = st.sidebar.radio("MENÚ PRINCIPAL:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN DE PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "📅 PROVEEDORES", "🗑️ ELIMINAR CUENTAS", "👥 USUARIOS", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])

conn = get_db()
uid = st.session_state['u_id']

if menu == "🚪 SALIR":
    st.session_state['auth'] = False; st.rerun()

elif menu == "📊 DASHBOARD":
    st.title("📊 Resumen del Negocio")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 CUENTAS MAESTRAS", pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0])
    c2.metric("✅ PERFILES VENDIDOS", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0])
    c3.metric("🔓 PERFILES LIBRES", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0])
    
    st.divider()
    st.subheader("👥 Clientes Próximos a Vencer")
    df = pd.read_sql_query(f"SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True, hide_index=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Nuevas Cuentas")
    plat = st.selectbox("PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    with st.form("f_reg", clear_on_submit=True):
        col1, col2, col3 = st.columns([2,2,1])
        m = col1.text_input("CORREO ELECTRÓNICO")
        p = col2.text_input("CONTRASEÑA MAESTRA")
        c = col3.number_input("COSTO (S/)", min_value=0.0)
        f = st.date_input("FECHA VENCIMIENTO PROVEEDOR", format="DD/MM/YYYY")
        st.write("---")
        per_data = []
        ca, cb = st.columns(2)
        for i in range(PLATAFORMAS_CONFIG[plat]):
            with ca: n = st.text_input(f"Nombre Perfil {i+1}", f"P{i+1}", key=f"n_{i}")
            with cb: pi = st.text_input(f"PIN {i+1}", "0000", key=f"p_{i}")
            per_data.append((n, pi))
        if st.form_submit_button("🚀 ACTIVAR PLATAFORMA"):
            if m and p:
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?)", (plat, m, p, f.strftime("%d/%m/%Y"), c, uid))
                    for nom, pin in per_data:
                        cur.execute("INSERT INTO perfiles (email, plataforma, nombre, pin, creador_id) VALUES (?,?,?,?,?)", (m, plat, nom, pin, uid))
                    conn.commit(); st.success("✅ ¡CUENTA SUBIDA CON ÉXITO!"); st.rerun()
                except: st.error("ERROR: EL CORREO YA EXISTE.")

elif menu == "📱 GESTIÓN DE PERFILES":
    st.title("📱 Administración y Entregas")
    p_sel = st.selectbox("FILTRAR POR PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    emails = pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)['email'].tolist()
    
    if emails:
        target = st.selectbox("SELECCIONAR CUENTA:", emails)
        cta = pd.read_sql_query(f"SELECT password FROM cuentas WHERE email='{target}'", conn).iloc[0]
        st.markdown(f"<div class='card-pro' style='border-left-color:#0080ff;'>🔑 <b>CLAVE {p_sel}:</b> {cta['password']}</div>", unsafe_allow_html=True)
        
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{target}' AND creador_id={uid}", conn)
        for _, row in perfs.iterrows():
            stat = "🟢 LIBRE" if row['estado'] == 'LIBRE' else f"🔴 VENDIDO ({row['whatsapp']})"
            with st.expander(f"{stat} - {row['nombre']}"):
                col_i, col_d = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = col_i.text_input("WhatsApp Cliente:", key=f"wa_{row['id']}")
                    pv = col_d.number_input("Precio Venta S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("🛒 CONFIRMAR VENTA", key=f"v_{row['id']}", use_container_width=True):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 **VENCE EL:** {row['fecha_vence']} (**{d} días restantes**)")
                    
                    msg = (f"*ENTREGA DE SERVICIO - {row['plataforma']}*\n\n"
                           f"• *Correo:* {target}\n"
                           f"• *Contraseña:* {cta['password']}\n"
                           f"• *Perfil:* {row['nombre']}\n"
                           f"• *PIN:* {row['pin']}\n"
                           f"• *Vencimiento:* {row['fecha_vence']}\n\n"
                           f"*¡Disfruta tu servicio!* Saúl Streaming")
                    
                    st.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; width:100%; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">🚀 ENVIAR POR WHATSAPP</button></a>', unsafe_allow_html=True)
                    
                    st.write("---")
                    c_b1, c_b2 = st.columns(2)
                    if c_b1.button("🔄 RENOVAR (+30D)", key=f"r_{row['id']}", use_container_width=True):
                        nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                        conn.commit(); st.success("¡RENOVADO!"); st.rerun()
                    if c_b2.button("✂️ CORTAR SERVICIO", key=f"c_{row['id']}", use_container_width=True):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()
    else: st.info("No hay cuentas registradas en esta plataforma.")

elif menu == "🔔 NOTIFICACIONES":
    st.title("🔔 Central de Cobranza y Soporte")
    p_noti = st.selectbox("FILTRAR POR PLATAFORMA:", ["TODAS"] + list(PLATAFORMAS_CONFIG.keys()))
    
    query = f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}"
    if p_noti != "TODAS": query += f" AND plataforma='{p_noti}'"
    
    df_n = pd.read_sql_query(query, conn)
    if not df_n.empty:
        df_n['DÍAS'] = df_n['fecha_vence'].apply(calcular_dias)
        for _, r in df_n.sort_values('DÍAS').iterrows():
            with st.container():
                st.markdown(f"<div class='card-pro' style='border-left-color:#ffd700;'>", unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns([2, 1, 1])
                col_a.write(f"👤 **{r['nombre']}** ({r['plataforma']}) - Vence en **{r['DÍAS']} días**")
                
                # Botón de Renovación
                msg_ren = f"Hola {r['nombre']}, te saludamos de Saúl Streaming. Tu perfil de {r['plataforma']} vence pronto ({r['fecha_vence']}). ¿Deseas renovar?"
                col_b.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg_ren)}" target="_blank" style="text-decoration:none;"><button style="background-color:#0080ff; color:white; border:none; padding:8px; border-radius:5px; width:100%;">🔔 RECORDAR</button></a>', unsafe_allow_html=True)
                
                # Botón de Cambio de Cuenta
                msg_cam = f"Hola {r['nombre']}, te informamos un cambio en tu cuenta de {r['plataforma']}. Por favor, contáctanos para darte tus nuevas credenciales."
                col_c.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg_cam)}" target="_blank" style="text-decoration:none;"><button style="background-color:#6c757d; color:white; border:none; padding:8px; border-radius:5px; width:100%;">🔄 CAMBIO CTA</button></a>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else: st.success("Todo al día.")

elif menu == "💰 FINANZAS PRO":
    st.title("💰 Balance Financiero Real")
    eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
    in_g = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0] or 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📉 EGRESOS (PROVEEDORES)", moneda(eg))
    col2.metric("📈 INGRESOS (VENTAS)", moneda(in_g))
    col3.metric("🤑 GANANCIA NETA", moneda(in_g - eg))
    
    st.divider()
    res = []
    for p in PLATAFORMAS_CONFIG.keys():
        e_p = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE plataforma='{p}' AND creador_id={uid}", conn).iloc[0,0] or 0
        i_p = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}' AND creador_id={uid}", conn).iloc[0,0] or 0
        res.append({"PLATAFORMA": p, "EGRESOS": moneda(e_p), "INGRESOS": moneda(i_p), "GANANCIA": moneda(i_p - e_p)})
    st.dataframe(pd.DataFrame(res), use_container_width=True, hide_index=True)

elif menu == "🗑️ ELIMINAR CUENTAS":
    st.title("🗑️ Gestión de Bajas")
    df_d = pd.read_sql_query(f"SELECT id, plataforma, email FROM cuentas WHERE creador_id={uid}", conn)
    for _, r in df_d.iterrows():
        with st.container():
            st.markdown("<div class='card-pro' style='border-left-color:#ff4b4b;'>", unsafe_allow_html=True)
            c1, c2 = st.columns([5,1])
            c1.write(f"📺 PLATAFORMA: **{r['plataforma']}** | 📧 CORREO: `{r['email']}`")
            if c2.button("🗑️", key=f"del_{r['id']}", use_container_width=True):
                cur = conn.cursor()
                cur.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
                cur.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
                conn.commit(); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

elif menu == "👥 USUARIOS":
    st.title("👥 Administración de Socios")
    if st.session_state['u_ran'] == 'ADMIN':
        pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
        for _, r in pends.iterrows():
            col1, col2 = st.columns([4,1])
            col1.write(f"👤 SOLICITUD DE: **{r['user']}**")
            if col2.button("✅ ACTIVAR", key=f"acc_{r['id']}", use_container_width=True):
                conn.cursor().execute(f"UPDATE usuarios SET rango='SOCIO' WHERE id={r['id']}")
                conn.commit(); st.rerun()
        st.divider()
        st.dataframe(pd.read_sql_query("SELECT user as USUARIO, rango as RANGO FROM usuarios", conn), use_container_width=True, hide_index=True)
    else: st.error("Acceso restringido al Administrador Global.")

elif menu == "🔑 CAMBIAR CLAVE":
    st.title("🔑 Seguridad")
    with st.form("f_pass"):
        old = st.text_input("CONTRASEÑA ACTUAL", type="password")
        new = st.text_input("NUEVA CONTRASEÑA", type="password")
        if st.form_submit_button("ACTUALIZAR"):
            cur = conn.cursor(); cur.execute("SELECT password FROM usuarios WHERE id=?", (uid,))
            if cur.fetchone()[0] == hash_pass(old):
                cur.execute("UPDATE usuarios SET password=? WHERE id=?", (hash_pass(new), uid))
                conn.commit(); st.success("¡CLAVE CAMBIADA CON ÉXITO!")
            else: st.error("La clave actual no es correcta.")

elif menu == "📅 PROVEEDORES":
    st.title("📅 Vencimientos Maestro")
    st.dataframe(pd.read_sql_query(f"SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas WHERE creador_id={uid}", conn), use_container_width=True, hide_index=True)