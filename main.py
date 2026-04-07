import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# ---------------- CONFIG ----------------
st.set_page_config(page_title="STREAMING PRO MAX", layout="wide")

DB = "streaming.db"

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

conn = db()
c = conn.cursor()

# ---------------- DB ----------------
c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
id INTEGER PRIMARY KEY,
user TEXT UNIQUE,
password TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS cuentas (
id INTEGER PRIMARY KEY,
plataforma TEXT,
email TEXT,
password TEXT,
precio REAL,
estado TEXT DEFAULT 'LIBRE'
)''')

c.execute('''CREATE TABLE IF NOT EXISTS clientes (
id INTEGER PRIMARY KEY,
nombre TEXT,
whatsapp TEXT
)''')

conn.commit()

# ---------------- CSS PRO MAX ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#020617,#020617,#0f172a);
}

/* TITULO */
.title {
    text-align:center;
    font-size:42px;
    font-weight:900;
    background: linear-gradient(90deg,#00f5ff,#00ff85);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

/* GRID CARDS */
.card {
    background: #111827;
    border-radius: 18px;
    padding: 30px;
    text-align: center;
    height: 180px;
    border: 1px solid rgba(255,255,255,0.08);
    transition: 0.3s;
}
.card:hover {
    transform: scale(1.07);
    box-shadow: 0 0 25px #00ffff;
}

/* ICON */
.icon {
    font-size:40px;
    margin-bottom:10px;
}

/* BUTTON FULL */
div.stButton > button {
    width:100%;
    height:180px;
    opacity:0;
    position:absolute;
}

/* CONTAINER RELATIVE */
.btn-wrap {
    position:relative;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "auth" not in st.session_state:
    st.session_state.auth = False
if "step" not in st.session_state:
    st.session_state.step = "login"
if "modulo" not in st.session_state:
    st.session_state.modulo = None

# ---------------- LOGIN ----------------
if not st.session_state.auth:

    col1, col2, col3 = st.columns([1,1.2,1])

    with col2:
        st.markdown("<div class='title'>STREAMING PRO</div>", unsafe_allow_html=True)

        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        if st.button("INGRESAR"):
            c.execute("SELECT * FROM usuarios WHERE user=?", (u,))
            r = c.fetchone()
            if r and r[2] == hash_pass(p):
                st.session_state.auth = True
                st.session_state.step = "panel"
                st.rerun()
            else:
                st.error("Error login")

    st.stop()

# ---------------- PANEL ----------------
st.markdown("<div class='title'>PANEL PREMIUM</div>", unsafe_allow_html=True)

menu = [
    ("➕","SUBIR"),
    ("⚙️","ADMIN"),
    ("👥","CLIENTES"),
    ("💸","VENDER"),
    ("📦","CUENTAS"),
    ("🔔","NOTIF"),
    ("💰","FINANZAS"),
    ("👤","USUARIOS"),
    ("👑","MI CUENTA")
]

cols = st.columns(3)

for i,(icon,name) in enumerate(menu):
    with cols[i%3]:
        st.markdown("<div class='btn-wrap'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card'>
            <div class='icon'>{icon}</div>
            <h3>{name}</h3>
        </div>
        """, unsafe_allow_html=True)

        if st.button(name, key=name):
            st.session_state.modulo = name

        st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ---------------- FUNCIONES ----------------

# SUBIR
if st.session_state.modulo == "SUBIR":
    st.subheader("Subir cuentas")

    with st.form("subir"):
        plat = st.selectbox("Plataforma", ["NETFLIX","DISNEY","PRIME"])
        email = st.text_input("Correo")
        password = st.text_input("Contraseña")
        precio = st.number_input("Precio")

        if st.form_submit_button("Guardar"):
            c.execute("INSERT INTO cuentas (plataforma,email,password,precio) VALUES (?,?,?,?)",
                      (plat,email,password,precio))
            conn.commit()
            st.success("Guardado")

# CLIENTES
elif st.session_state.modulo == "CLIENTES":
    st.subheader("Clientes")

    nombre = st.text_input("Nombre")
    numero = st.text_input("WhatsApp")

    if st.button("Guardar cliente"):
        c.execute("INSERT INTO clientes (nombre,whatsapp) VALUES (?,?)",(nombre,numero))
        conn.commit()

    df = pd.read_sql("SELECT * FROM clientes", conn)
    st.dataframe(df)

# VENDER (YA FUNCIONA 🔥)
elif st.session_state.modulo == "VENDER":
    st.subheader("Vender cuenta")

    cuentas = pd.read_sql("SELECT * FROM cuentas WHERE estado='LIBRE'", conn)

    if cuentas.empty:
        st.warning("No hay cuentas disponibles")
    else:
        cuenta = st.selectbox("Seleccionar cuenta", cuentas["email"])

        cliente = st.text_input("WhatsApp cliente")
        precio = st.number_input("Precio venta")

        if st.button("VENDER AHORA"):
            c.execute("UPDATE cuentas SET estado='OCUPADO' WHERE email=?", (cuenta,))
            conn.commit()

            mensaje = f"Cuenta: {cuenta}"
            url = f"https://wa.me/{cliente}?text={urllib.parse.quote(mensaje)}"

            st.success("Venta realizada")
            st.markdown(f"[Enviar WhatsApp]({url})")

# CUENTAS
elif st.session_state.modulo == "CUENTAS":
    df = pd.read_sql("SELECT plataforma,estado,COUNT(*) as total FROM cuentas GROUP BY plataforma,estado", conn)
    st.dataframe(df)

# FINANZAS
elif st.session_state.modulo == "FINANZAS":
    total = pd.read_sql("SELECT SUM(precio) FROM cuentas", conn).iloc[0,0]
    st.metric("Ingresos", total or 0)