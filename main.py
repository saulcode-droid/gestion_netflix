import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SAÚL STREAMING ULTRA PRO", page_icon="💎", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_ultra_v11.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, tipo_negocio TEXT, sub_tipo TEXT, plataforma TEXT, email TEXT UNIQUE, 
                       password TEXT, fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER, fecha_venta TEXT)''')
    cursor.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", ('admin', hash_pass('admin123'), 'ADMIN'))
    conn.commit()

init_db()

# --- ESTILOS CSS PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #0b0e14; color: white; }
    
    /* Estilo para las tarjetas de mosaico */
    .card-menu {
        background: #1c1f26;
        border: 1px solid #313640;
        border-radius: 20px;
        padding: 40px 20px;
        text-align: center;
        transition: 0.4s;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .card-menu:hover { border-color: #00ff00; transform: scale(1.05); box-shadow: 0 0 20px rgba(0,255,0,0.2); }
    
    .stButton>button { border-radius: 12px; height: 3em; font-weight: bold; }
    .css-1r6slb0 { border-radius: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(v): return f"S/ {v:,.2f}"
def calcular_dias(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

# --- NAVEGACIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'step' not in st.session_state: st.session_state['step'] = 'LOGIN'
if 'negocio' not in st.session_state: st.session_state['negocio'] = None
if 'publico' not in st.session_state: st.session_state['publico'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'

# ==========================================
# 1. LOGIN
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.3, 1])
    with col_log:
        st.markdown("<div style='text-align:center;'><img src='https://cdn.pixabay.com/photo/2024/02/09/11/48/hacker-8562942_1280.png' width='130'></div>", unsafe_allow_html=True)
        st.title("🔐 ACCESO VIP")
        t1, t2 = st.tabs(["INGRESAR", "REGISTRO"])
        with t1:
            u = st.text_input("USUARIO")
            p = st.text_input("CLAVE", type="password")
            if st.button("🚀 ENTRAR", use_container_width=True):
                conn = get_db(); cursor = conn.cursor()
                cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
                res = cursor.fetchone()
                if res and res[2] == hash_pass(p):
                    st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'step': 'MODO_NEGOCIO'})
                    st.rerun()
                else: st.error("DATOS INCORRECTOS")
            if st.button("❓ OLVIDÉ MI CLAVE", use_container_width=True):
                st.info("CONTACTA A SAÚL POR WHATSAPP PARA RESTABLECER TU CUENTA.")
        with t2:
            nu = st.text_input("NUEVO SOCIO")
            np = st.text_input("CLAVE NUEVA", type="password")
            if st.button("SOLICITAR ACCESO"):
                try:
                    conn = get_db(); cursor = conn.cursor()
                    cursor.execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,'PENDIENTE')", (nu, hash_pass(np)))
                    conn.commit(); st.success("SOLICITUD ENVIADA.")
                except: st.error("EL USUARIO YA EXISTE.")
    st.stop()

# ==========================================
# 2. SELECTOR DE MODO (Mosaico Grande)
# ==========================================
if st.session_state['step'] == 'MODO_NEGOCIO':
    st.title(f"BIENVENIDO, {st.session_state['u_nom'].upper()}")
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📱\n\nADMINISTRAR POR PERFILES", use_container_width=True):
            st.session_state.update({'negocio': 'PERFILES', 'step': 'MODO_PUBLICO'}); st.rerun()
    with col2:
        if st.button("📧\n\nADMINISTRAR CUENTAS COMPLETAS", use_container_width=True):
            st.session_state.update({'negocio': 'CUENTAS', 'step': 'MODO_PUBLICO'}); st.rerun()
    if st.button("🚪 CERRAR SESIÓN"): st.session_state.clear(); st.rerun()
    st.stop()

# ==========================================
# 3. SELECTOR PÚBLICO (Mosaico Grande)
# ==========================================
if st.session_state['step'] == 'MODO_PUBLICO':
    st.title(f"MODO: {st.session_state['negocio']}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥\n\nCLIENTES FINALES", use_container_width=True):
            st.session_state.update({'publico': 'FINALES', 'step': 'PANEL_CONTROL'}); st.rerun()
    with col2:
        if st.button("💼\n\nCOMISIONISTAS", use_container_width=True):
            st.session_state.update({'publico': 'COMISIONISTAS', 'step': 'PANEL_CONTROL'}); st.rerun()
    if st.button("⬅️ VOLVER"): st.session_state['step'] = 'MODO_NEGOCIO'; st.rerun()
    st.stop()

# ==========================================
# 4. PANEL DE CONTROL CENTRALIZADO
# ==========================================
conn = get_db(); uid = st.session_state['u_id']
neg, pub = st.session_state['negocio'], st.session_state['publico']

if st.session_state['step'] == 'PANEL_CONTROL':
    if st.session_state['herramienta'] == 'MENU':
        st.title(f"💎 {neg} | {pub}")
        st.write("---")
        # Mosaico 3x2
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ SUBIR PLATAFORMA", use_container_width=True): st.session_state['herramienta'] = 'SUBIR'; st.rerun()
        if c2.button("📱 GESTIÓN Y VENTAS", use_container_width=True): st.session_state['herramienta'] = 'GESTION'; st.rerun()
        if c3.button("🔔 COBRANZAS", use_container_width=True): st.session_state['herramienta'] = 'NOTIFICAR'; st.rerun()
        
        c4, c5, c6 = st.columns(3)
        if c4.button("💰 FINANZAS PRO", use_container_width=True): st.session_state['herramienta'] = 'FINANZAS'; st.rerun()
        if c5.button("🗑️ BAJAS / ELIMINAR", use_container_width=True): st.session_state['herramienta'] = 'ELIMINAR'; st.rerun()
        if c6.button("👤 USUARIOS", use_container_width=True): st.session_state['herramienta'] = 'USUARIOS'; st.rerun()
        
        st.write("---")
        if st.button("⬅️ VOLVER AL MODO DE MERCADO"): st.session_state['step'] = 'MODO_PUBLICO'; st.rerun()

    # --- SUBIR PLATAFORMA (CORREGIDO) ---
    elif st.session_state['herramienta'] == 'SUBIR':
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("🛒 Registro de Cuentas")
        
        opcion = st.radio("Acción:", ["Nueva Cuenta", "Agregar Perfiles a Existente"])
        
        if opcion == "Nueva Cuenta":
            with st.form("new_cta"):
                col1, col2 = st.columns(2)
                plat = col1.selectbox("Plataforma", ["NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"])
                mail = col2.text_input("Correo")
                clv = col1.text_input("Clave")
                cst = col2.number_input("Costo S/", 0.0)
                venc = st.date_input("Vence con Proveedor")
                if st.form_submit_button("🚀 CREAR CUENTA"):
                    cur = conn.cursor()
                    try:
                        cur.execute("INSERT INTO cuentas (tipo_negocio, sub_tipo, plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES (?,?,?,?,?,?,?,?)",
                                    (neg, pub, plat, mail, clv, venc.strftime("%d/%m/%Y"), cst, uid))
                        conn.commit(); st.success("✅ Cuenta Creada"); st.rerun()
                    except: st.error("❌ Correo ya existe")
        else:
            ctas_exist = pd.read_sql_query(f"SELECT email, plataforma FROM cuentas WHERE creador_id={uid}", conn)
            if not ctas_exist.empty:
                mail_sel = st.selectbox("Seleccione Cuenta:", ctas_exist['email'].tolist())
                with st.form("add_per"):
                    n_p = st.text_input("Nombre del Perfil")
                    p_p = st.text_input("PIN")
                    if st.form_submit_button("➕ AGREGAR PERFIL"):
                        conn.cursor().execute("INSERT INTO perfiles (email, nombre, pin, creador_id) VALUES (?,?,?,?)", (mail_sel, n_p, p_p, uid))
                        conn.commit(); st.success("✅ Perfil agregado")
            else: st.warning("No hay cuentas creadas.")

    # --- GESTIÓN Y VENTAS (CORREGIDO CON FILTRO) ---
    elif st.session_state['herramienta'] == 'GESTION':
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("📱 Administración")
        plat_f = st.selectbox("Filtrar Plataforma:", ["NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"])
        ctas = pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{plat_f}' AND sub_tipo='{pub}' AND creador_id={uid}", conn)
        
        if not ctas.empty:
            sel_mail = st.selectbox("Seleccionar Correo:", ctas['email'].tolist())
            if neg == 'PERFILES':
                perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_mail}'", conn)
                for _, row in perfs.iterrows():
                    with st.expander(f"{row['estado']} - {row['nombre']}"):
                        if row['estado'] == 'LIBRE':
                            wa = st.text_input("WhatsApp", key=f"wa_{row['id']}")
                            pv = st.number_input("Precio", 10.0, key=f"pv_{row['id']}")
                            if st.button("Vender", key=f"v_{row['id']}"):
                                fv = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                f_hoy = datetime.now().strftime("%d/%m/%Y")
                                conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', precio_venta={pv}, fecha_vence='{fv}', fecha_venta='{f_hoy}' WHERE id={row['id']}")
                                conn.commit(); st.rerun()
                        else:
                            st.write(f"Vence: {row['fecha_vence']}")
                            n_nom = st.text_input("Editar Nombre", row['nombre'], key=f"en_{row['id']}")
                            n_pin = st.text_input("Editar PIN", row['pin'], key=f"ep_{row['id']}")
                            if st.button("Actualizar", key=f"u_{row['id']}"):
                                conn.cursor().execute(f"UPDATE perfiles SET nombre='{n_nom}', pin='{n_pin}' WHERE id={row['id']}")
                                conn.commit(); st.rerun()
                            if st.button("✂️ Cortar", key=f"c_{row['id']}"):
                                conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, precio_venta=0 WHERE id={row['id']}")
                                conn.commit(); st.rerun()
            else:
                cta_dat = pd.read_sql_query(f"SELECT * FROM cuentas WHERE email='{sel_mail}'", conn).iloc[0]
                st.success(f"🔑 CLAVE: {cta_dat['password']}")

    # --- FINANZAS PRO (CON RANGO DE FECHAS) ---
    elif st.session_state['herramienta'] == 'FINANZAS':
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("💰 Balance de Ganancias")
        col_f1, col_f2 = st.columns(2)
        f_inicio = col_f1.date_input("Desde:", datetime.now() - timedelta(days=7))
        f_fin = col_f2.date_input("Hasta:", datetime.now())
        
        eg = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE creador_id={uid}", conn)['t'][0] or 0
        df_ventas = pd.read_sql_query(f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn)
        
        # Filtro de fecha manual sobre el dataframe
        df_ventas['fecha_venta'] = pd.to_datetime(df_ventas['fecha_venta'], format="%d/%m/%Y", errors='coerce')
        mask = (df_ventas['fecha_venta'] >= pd.Timestamp(f_inicio)) & (df_ventas['fecha_venta'] <= pd.Timestamp(f_fin))
        ventas_filtradas = df_ventas.loc[mask]
        
        ing = ventas_filtradas['precio_venta'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📉 EGRESOS TOTALES", moneda(eg))
        c2.metric("📈 INGRESOS PERIODO", moneda(ing))
        c3.metric("🤑 GANANCIA PERIODO", moneda(ing))
        
        st.divider()
        st.subheader("📊 Detalle por Plataforma")
        res = []
        for p in ["NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"]:
            ip = ventas_filtradas[ventas_filtradas['email'].isin(pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{p}'", conn)['email'])]['precio_venta'].sum()
            res.append({"Plataforma": p, "Ventas Periodo": moneda(ip)})
        st.table(pd.DataFrame(res))

    # --- NOTIFICACIONES / COBRANZAS ---
    elif st.session_state['herramienta'] == 'NOTIFICAR':
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("🔔 Central de Cobranzas")
        plat_n = st.selectbox("Plataforma:", ["TODAS","NETFLIX","DISNEY","MAX","PRIME","VIX","CRUNCHY"])
        
        q = f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}"
        df_n = pd.read_sql_query(q, conn)
        if not df_n.empty:
            df_n['dias'] = df_n['fecha_vence'].apply(calcular_dias)
            for _, r in df_n.sort_values('dias').iterrows():
                with st.container():
                    col_a, col_b = st.columns([3,1])
                    col_a.warning(f"👤 {r['nombre']} - Vence en {r['dias']} días ({r['fecha_vence']})")
                    msg = f"Hola {r['nombre']}, te recordamos renovar tu cuenta que vence el {r['fecha_vence']}."
                    col_b.markdown(f'<a href="https://wa.me/{r["whatsapp"]}?text={urllib.parse.quote(msg)}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; border-radius:5px; width:100%;">🔔 AVISAR</button></a>', unsafe_allow_html=True)

    # --- USUARIOS (SOLO ADMIN) ---
    elif st.session_state['herramienta'] == 'USUARIOS':
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("👥 Gestión de Socios")
        if st.session_state['u_ran'] == 'ADMIN':
            pends = pd.read_sql_query("SELECT id, user FROM usuarios WHERE rango='PENDIENTE'", conn)
            for _, r in pends.iterrows():
                c1, c2 = st.columns([4,1])
                c1.write(f"Socio: {r['user']}")
                if c2.button("✅ ACTIVAR", key=f"ac_{r['id']}"):
                    conn.cursor().execute(f"UPDATE usuarios SET rango='SOCIO' WHERE id={r['id']}")
                    conn.commit(); st.rerun()
            st.dataframe(pd.read_sql_query("SELECT user, rango FROM usuarios", conn), use_container_width=True)
        else: st.error("Acceso restringido")

    # --- BAJAS / ELIMINAR ---
    elif st.session_state['herramienta'] == 'ELIMINAR':
        if st.button("⬅️ VOLVER"): st.session_state['herramienta'] = 'MENU'; st.rerun()
        st.header("🗑️ Eliminar Cuentas")
        df_del = pd.read_sql_query(f"SELECT id, plataforma, email FROM cuentas WHERE creador_id={uid}", conn)
        for _, r in df_del.iterrows():
            c1, c2 = st.columns([5,1])
            c1.info(f"📺 {r['plataforma']} | {r['email']}")
            if c2.button("🗑️", key=f"del_{r['id']}"):
                cur = conn.cursor()
                cur.execute(f"DELETE FROM cuentas WHERE id={r['id']}"); cur.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
                conn.commit(); st.rerun()