import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SISTEMA SAÚL STREAMING PRO", page_icon="🎬", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_saul_final_v85.db'

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

# --- ESTILOS CSS PROFESIONALES ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .card-pro {
        padding: 20px; border-radius: 15px; border-left: 8px solid #00ff00;
        background-color: #161b22; box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .metric-egresos { border-left-color: #ff4b4b !important; }
    .metric-ingresos { border-left-color: #0080ff !important; }
    .metric-ganancia { border-left-color: #ffd700 !important; }
    h1, h2, h3 { color: #ffffff; text-transform: uppercase; }
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

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False

if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.image("https://cdn-icons-png.flaticon.com/512/924/924915.png", width=100)
        st.title("🔐 ACCESO VIP")
        u = st.text_input("USUARIO")
        p = st.text_input("CONTRASEÑA", type="password")
        if st.button("🚀 ENTRAR AL SISTEMA", use_container_width=True):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p):
                st.session_state['auth'], st.session_state['u_id'], st.session_state['u_nom'], st.session_state['u_ran'] = True, res[0], u, res[1]
                st.rerun()
            else: st.error("DATOS INCORRECTOS")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(f"👤 {st.session_state['u_nom'].upper()}")
menu = st.sidebar.radio("MENÚ:", ["📊 DASHBOARD", "🌐 PLATAFORMAS", "📱 GESTIÓN DE PERFILES", "🔔 NOTIFICACIONES", "💰 FINANZAS PRO", "🗑️ ELIMINAR CUENTAS", "👥 USUARIOS", "🔑 CAMBIAR CLAVE", "🚪 SALIR"])

conn = get_db()
uid = st.session_state['u_id']

# --- LÓGICA DE MENÚS ---
if menu == "🚪 SALIR":
    st.session_state['auth'] = False; st.rerun()

elif menu == "📊 DASHBOARD":
    st.title("📊 RESUMEN GENERAL")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 CUENTAS", pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0])
    c2.metric("✅ VENDIDOS", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0])
    c3.metric("🔓 LIBRES", pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0])
    
    st.divider()
    df = pd.read_sql_query(f"SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
    if not df.empty:
        df['DÍAS'] = df['fecha_vence'].apply(calcular_dias)
        st.subheader("👥 PRÓXIMOS VENCIMIENTOS")
        st.dataframe(df.sort_values('DÍAS'), use_container_width=True, hide_index=True)

elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 REGISTRO DE CUENTAS")
    plat = st.selectbox("PLATAFORMA:", list(PLATAFORMAS_CONFIG.keys()))
    with st.form("f_reg", clear_on_submit=True):
        col1, col2, col3 = st.columns([2,2,1])
        m = col1.text_input("📧 CORREO")
        p = col2.text_input("🔑 CONTRASEÑA")
        c = col3.number_input("💵 COSTO CUENTA (S/)", min_value=0.0, step=0.1)
        f = st.date_input("📅 VENCIMIENTO PROVEEDOR", format="DD/MM/YYYY")
        st.write("---")
        per_data = []
        ca, cb = st.columns(2)
        for i in range(PLATAFORMAS_CONFIG[plat]):
            with ca: n = st.text_input(f"NOMBRE P{i+1}", f"P{i+1}", key=f"n_{i}")
            with cb: pi = st.text_input(f"PIN P{i+1}", "0000", key=f"p_{i}")
            per_data.append((n, pi))
        
        if st.form_submit_button("🚀 ACTIVAR CUENTA"):
            if m and p:
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?)", (plat, m, p, f.strftime("%d/%m/%Y"), c, uid))
                    for nom, pin in per_data:
                        cur.execute("INSERT INTO perfiles (email, plataforma, nombre, pin, creador_id) VALUES (?,?,?,?,?)", (m, plat, nom, pin, uid))
                    conn.commit()
                    st.success("✅ ¡CUENTA REGISTRADA CON ÉXITO!")
                    st.balloons()
                except: st.error("❌ EL CORREO YA EXISTE EN EL SISTEMA")

elif menu == "📱 GESTIÓN DE PERFILES":
    st.title("📱 GESTIÓN POR PLATAFORMA")
    p_sel = st.selectbox("SELECCIONA PLATAFORMA A GESTIONAR:", list(PLATAFORMAS_CONFIG.keys()))
    emails = pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)['email'].tolist()
    
    if emails:
        target = st.selectbox("SELECCIONAR CORREO:", emails)
        cta = pd.read_sql_query(f"SELECT password FROM cuentas WHERE email='{target}'", conn).iloc[0]
        st.markdown(f"<div class='card-pro'><h3>🔑 CLAVE {p_sel}: {cta['password']}</h3></div>", unsafe_allow_html=True)
        
        perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{target}' AND creador_id={uid}", conn)
        for _, row in perfs.iterrows():
            stat_color = "🟢" if row['estado'] == 'LIBRE' else "🔴"
            with st.expander(f"{stat_color} {row['nombre']} | PIN: {row['pin']} | {row['estado']}"):
                col_a, col_b = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = col_a.text_input("WhatsApp Cliente:", key=f"wa_{row['id']}")
                    pv = col_b.number_input("Precio Venta S/", value=10.0, key=f"pv_{row['id']}")
                    if st.button("🛒 CONFIRMAR VENTA", key=f"v_{row['id']}"):
                        v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{v}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    d = calcular_dias(row['fecha_vence'])
                    st.write(f"📅 Vence: {row['fecha_vence']} ({d} días)")
                    
                    msg = (f"💎 *ENTREGA DE SERVICIO - {row['plataforma']}* 💎\n\n"
                           f"📧 *Correo:* `{target}`\n"
                           f"🔑 *Contraseña:* `{cta['password']}`\n"
                           f"👤 *Perfil:* {row['nombre']}\n"
                           f"📌 *PIN:* `{row['pin']}`\n"
                           f"📅 *Vencimiento:* {row['fecha_vence']}\n\n"
                           f"🎬 *¡Disfruta tu servicio!* Saúl Streaming 🚀")
                    
                    st.markdown(f'<a href="https://wa.me/{row["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; width:100%; border:none; padding:12px; border-radius:10px; cursor:pointer; font-weight:bold;">🚀 ENVIAR POR WHATSAPP</button></a>', unsafe_allow_html=True)
                    st.write("")
                    c_b1, c_b2 = st.columns(2)
                    if c_b1.button("🔄 RENOVAR (+30D)", key=f"r_{row['id']}"):
                        nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if c_b2.button("✂️ CORTAR SERVICIO", key=f"c_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()
    else: st.info(f"Aún no tienes cuentas de {p_sel} registradas.")

elif menu == "💰 FINANZAS PRO":
    st.title("💰 BALANCE DE CAJA REAL")
    eg = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
    in_g = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0] or 0
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1: st.markdown(f'<div class="card-pro metric-egresos"><h3>📉 EGRESOS</h3><h2>{moneda(eg)}</h2></div>', unsafe_allow_html=True)
    with col_t2: st.markdown(f'<div class="card-pro metric-ingresos"><h3>📈 INGRESOS</h3><h2>{moneda(in_g)}</h2></div>', unsafe_allow_html=True)
    with col_t3: st.markdown(f'<div class="card-pro metric-ganancia"><h3>🤑 GANANCIA</h3><h2>{moneda(in_g - eg)}</h2></div>', unsafe_allow_html=True)
    
    st.divider()
    res = []
    for p in PLATAFORMAS_CONFIG.keys():
        e_p = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE plataforma='{p}' AND creador_id={uid}", conn).iloc[0,0] or 0
        i_p = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}' AND creador_id={uid}", conn).iloc[0,0] or 0
        res.append({"PLATAFORMA": p, "EGRESOS": moneda(e_p), "INGRESOS": moneda(i_p), "GANANCIA": moneda(i_p - e_p)})
    st.table(pd.DataFrame(res))

elif menu == "🗑️ ELIMINAR CUENTAS":
    st.title("🗑️ GESTIÓN DE BAJAS")
    df_d = pd.read_sql_query(f"SELECT id, plataforma, email FROM cuentas WHERE creador_id={uid}", conn)
    for _, r in df_d.iterrows():
        with st.container():
            c1, c2 = st.columns([5,1])
            c1.markdown(f"<div class='card-pro' style='border-left-color:red;'><h4>📺 {r['plataforma']} | {r['email']}</h4></div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"del_{r['id']}"):
                cur = conn.cursor()
                cur.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
                cur.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
                conn.commit(); st.rerun()

elif menu == "🔔 NOTIFICACIONES":
    st.title("🔔 COBRANZA PENDIENTE")
    df_n = pd.read_sql_query(f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
    if not df_n.empty:
        df_n['DÍAS'] = df_n['fecha_vence'].apply(calcular_dias)
        v_list = df_n[df_n['DÍAS'] <= 3]
        if v_list.empty: st.success("✅ TODO AL DÍA")
        for _, r in v_list.iterrows():
            st.warning(f"⚠️ {r['nombre']} ({r['plataforma']}) vence en {r['DÍAS']} días")
            msg = f"Hola {r['nombre']}, recordatorio de Saúl Streaming. Tu perfil vence el {r['fecha_vence']}. ¿Renovamos?"
            st.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank"><button style="background-color:#008CBA; color:white; padding:8px; border-radius:5px; border:none; cursor:pointer;">🔔 AVISAR</button></a>', unsafe_allow_html=True)
            st.divider()

elif menu == "👥 USUARIOS":
    st.title("👥 ADMINISTRACIÓN DE SOCIOS")
    if st.session_state['u_ran'] == 'ADMIN':
        pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
        for _, r in pends.iterrows():
            col1, col2 = st.columns([4,1])
            col1.write(f"👤 USUARIO: {r['user']}")
            if col2.button("✅ ACTIVAR", key=f"acc_{r['id']}"):
                conn.cursor().execute(f"UPDATE usuarios SET rango='SOCIO' WHERE id={r['id']}")
                conn.commit(); st.rerun()
        st.divider()
        st.write("TODOS LOS USUARIOS:")
        st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)
    else: st.error("ACCESO SOLO PARA ADMINISTRADOR GLOBAL.")