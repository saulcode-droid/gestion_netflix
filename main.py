import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --------------------------------
# CONFIG
# --------------------------------
st.set_page_config(page_title="STREAMING VIP", layout="wide")

DB_NAME = 'db_streaming_v14.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        user TEXT UNIQUE,
        password TEXT,
        rango TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY,
        plataforma TEXT,
        email TEXT,
        password TEXT,
        costo REAL,
        creador_id INTEGER)""")

    c.execute("""CREATE TABLE IF NOT EXISTS perfiles (
        id INTEGER PRIMARY KEY,
        email TEXT,
        plataforma TEXT,
        nombre TEXT,
        pin TEXT,
        estado TEXT,
        whatsapp TEXT,
        fecha_vence TEXT,
        precio_venta REAL,
        creador_id INTEGER)""")

    c.execute("INSERT OR IGNORE INTO usuarios (user,password,rango) VALUES ('admin',?, 'ADMIN_GLOBAL')",
              (hash_pass("admin123"),))

    conn.commit()

init_db()

# --------------------------------
# ESTILO GLOBAL CLEAN
# --------------------------------
st.markdown("""
<style>
.stApp {
    background: #020617;
    color: #E5E7EB;
}

.stButton > button {
    background: #111827 !important;
    border: 1px solid #1F2937 !important;
    border-radius: 10px !important;
    color: #E5E7EB !important;
}

.stButton > button:hover {
    background: #6366F1 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------
# COMPONENTES UI
# --------------------------------
def header(title, subtitle=""):
    st.markdown(f"""
    <div style="background:#020617;border:1px solid #1E293B;
    border-radius:16px;padding:20px;margin-bottom:20px;">
        <div style="font-size:1.6rem;font-weight:800;">{title}</div>
        <div style="color:#64748B;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def metric_card(title, value):
    st.markdown(f"""
    <div style="background:#020617;border:1px solid #1E293B;
    border-radius:12px;padding:18px;">
        <div style="color:#64748B;font-size:0.8rem;">{title}</div>
        <div style="font-size:1.8rem;font-weight:800;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def perfil_card(nombre, pin, estado):
    color = "#10B981" if estado == "LIBRE" else "#EF4444"

    st.markdown(f"""
    <div style="background:#020617;border:1px solid #1E293B;
    border-radius:12px;padding:12px;margin:8px 0;
    display:flex;justify-content:space-between;">
        <div>
            <b>{nombre}</b><br>
            <span style="color:#64748B;">PIN: {pin}</span>
        </div>
        <div style="color:{color};font-weight:700;">
            {estado}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------
# LOGIN
# --------------------------------
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align:center;'>STREAMING VIP</h2>", unsafe_allow_html=True)

    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id,password FROM usuarios WHERE user=?", (u,))
        res = c.fetchone()

        if res and res[1] == hash_pass(p):
            st.session_state.auth = True
            st.session_state.uid = res[0]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.stop()

conn = get_db()
uid = st.session_state.uid

# --------------------------------
# MENU
# --------------------------------
menu = st.sidebar.radio("Menu", ["Dashboard", "Perfiles", "Cuentas", "Finanzas", "Salir"])

# --------------------------------
# DASHBOARD
# --------------------------------
if menu == "Dashboard":
    header("Dashboard", "Resumen general")

    total = pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0]
    vendidos = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0]
    libres = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0]

    c1,c2,c3 = st.columns(3)

    with c1:
        metric_card("Cuentas", total)
    with c2:
        metric_card("Vendidos", vendidos)
    with c3:
        metric_card("Libres", libres)

# --------------------------------
# PERFILES
# --------------------------------
elif menu == "Perfiles":
    header("Perfiles", "Gestión")

    df = pd.read_sql_query(f"SELECT * FROM perfiles WHERE creador_id={uid}", conn)

    for _, row in df.iterrows():
        perfil_card(row["nombre"], row["pin"], row["estado"])

        if row["estado"] == "LIBRE":
            wa = st.text_input(f"WhatsApp {row['id']}")
            precio = st.number_input(f"Precio {row['id']}", min_value=0.0)

            if st.button(f"Vender {row['id']}"):
                if wa:
                    fecha = (datetime.now()+timedelta(days=30)).strftime("%d/%m/%Y")
                    conn.cursor().execute(
                        "UPDATE perfiles SET estado='VENDIDO',whatsapp=?,fecha_vence=?,precio_venta=? WHERE id=?",
                        (wa,fecha,precio,row["id"])
                    )
                    conn.commit()
                    st.rerun()

# --------------------------------
# CUENTAS
# --------------------------------
elif menu == "Cuentas":
    header("Cuentas", "Registrar")

    with st.form("add"):
        plat = st.text_input("Plataforma")
        mail = st.text_input("Correo")
        clv = st.text_input("Clave")
        costo = st.number_input("Costo")

        if st.form_submit_button("Guardar"):
            conn.cursor().execute(
                "INSERT INTO cuentas (plataforma,email,password,costo,creador_id) VALUES (?,?,?,?,?)",
                (plat,mail,clv,costo,uid)
            )
            conn.commit()
            st.success("Guardado")

# --------------------------------
# FINANZAS
# --------------------------------
elif menu == "Finanzas":
    header("Finanzas", "Resumen")

    ingresos = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0] or 0
    costos = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0

    st.write("Ingresos:", ingresos)
    st.write("Costos:", costos)
    st.write("Ganancia:", ingresos - costos)

# --------------------------------
# SALIR
# --------------------------------
elif menu == "Salir":
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()