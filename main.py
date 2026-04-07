import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="STREAMING PRO", layout="wide")

# =========================
# DB
# =========================
conn = sqlite3.connect("streaming_pro.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS usuarios(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user TEXT UNIQUE,
password TEXT,
rango TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS cuentas(
id INTEGER PRIMARY KEY AUTOINCREMENT,
plataforma TEXT,
email TEXT,
password TEXT,
precio REAL,
estado TEXT,
fecha_vence TEXT,
cliente TEXT,
whatsapp TEXT
)
""")

conn.commit()

# =========================
# FUNCIONES
# =========================
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# =========================
# ADMIN FIJO
# =========================
admin = c.execute("SELECT * FROM usuarios WHERE user='admin'").fetchone()

if not admin:
    c.execute(
        "INSERT INTO usuarios(user,password,rango) VALUES (?,?,?)",
        ("admin", hash_pass("admin123"), "ADMIN")
    )
    conn.commit()

# =========================
# CSS PRO
# =========================
st.markdown("""
<style>

.stApp {
background: linear-gradient(135deg,#020617,#020617,#020617);
color:white;
}

.big-btn button {
height:140px;
width:100%;
border-radius:20px;
font-size:20px;
font-weight:bold;
background: linear-gradient(135deg,#00ffc3,#0066ff);
color:white;
border:none;
transition:0.3s;
}

.big-btn button:hover {
transform:scale(1.05);
box-shadow:0 0 25px #00ffc3;
}

</style>
""", unsafe_allow_html=True)

# =========================
# SESSION
# =========================
if "login" not in st.session_state:
    st.session_state.login = False

if "menu" not in st.session_state:
    st.session_state.menu = "home"

# =========================
# LOGIN / REGISTER
# =========================
if not st.session_state.login:

    col1,col2 = st.columns(2)

    with col1:
        st.subheader("🔐 Login")
        u = st.text_input("Usuario")
        p = st.text_input("Password", type="password")

        if st.button("Entrar"):

            # ADMIN DIRECTO
            if u == "admin" and p == "admin123":
                st.session_state.login = True
                st.session_state.user = "admin"
                st.rerun()

            else:
                res = c.execute("SELECT * FROM usuarios WHERE user=?",(u,)).fetchone()

                if res and res[2] == hash_pass(p):
                    st.session_state.login = True
                    st.session_state.user = u
                    st.rerun()
                else:
                    st.error("Datos incorrectos")

    with col2:
        st.subheader("📝 Registro")
        u2 = st.text_input("Nuevo usuario")
        p2 = st.text_input("Nueva contraseña", type="password")

        if st.button("Registrar"):
            try:
                c.execute("INSERT INTO usuarios(user,password,rango) VALUES (?,?,?)",
                          (u2, hash_pass(p2), "USER"))
                conn.commit()
                st.success("Registrado correctamente")
            except:
                st.error("Usuario ya existe")

    st.stop()

# =========================
# PANEL PRINCIPAL
# =========================
st.title("🔥 PANEL PRO")

col1,col2,col3,col4 = st.columns(4)

with col1:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    if st.button("➕ SUBIR"):
        st.session_state.menu="subir"
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    if st.button("💰 VENDER"):
        st.session_state.menu="vender"
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    if st.button("📦 CUENTAS"):
        st.session_state.menu="cuentas"
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    if st.button("📊 FINANZAS"):
        st.session_state.menu="finanzas"
    st.markdown('</div>', unsafe_allow_html=True)

st.write("---")

# =========================
# SUBIR
# =========================
if st.session_state.menu=="subir":

    st.header("➕ Subir Cuenta")

    plataforma = st.selectbox("Plataforma",["Netflix","Disney","Prime","HBO"])
    email = st.text_input("Email")
    password = st.text_input("Password")
    precio = st.number_input("Precio",0.0)
    dias = st.number_input("Duración (días)",30)

    if st.button("Guardar"):

        fecha = datetime.now() + timedelta(days=int(dias))

        c.execute("""
        INSERT INTO cuentas(plataforma,email,password,precio,estado,fecha_vence,cliente,whatsapp)
        VALUES (?,?,?,?,?,?,?,?)
        """,(plataforma,email,password,precio,"LIBRE",fecha.strftime("%Y-%m-%d"),"", ""))

        conn.commit()
        st.success("Cuenta guardada")

# =========================
# VENDER
# =========================
if st.session_state.menu=="vender":

    st.header("💰 Vender Cuenta")

    df = pd.read_sql("SELECT * FROM cuentas WHERE estado='LIBRE'", conn)

    if df.empty:
        st.warning("No hay cuentas disponibles")
    else:
        cuenta = st.selectbox("Cuenta disponible", df["email"])

        cliente = st.text_input("Cliente")
        whatsapp = st.text_input("WhatsApp")

        if st.button("Confirmar venta"):

            c.execute("""
            UPDATE cuentas 
            SET estado='OCUPADO', cliente=?, whatsapp=? 
            WHERE email=?
            """,(cliente,whatsapp,cuenta))

            conn.commit()
            st.success("Venta realizada")

# =========================
# CUENTAS
# =========================
if st.session_state.menu=="cuentas":

    st.header("📦 Todas las cuentas")
    df = pd.read_sql("SELECT * FROM cuentas", conn)
    st.dataframe(df, use_container_width=True)

# =========================
# FINANZAS
# =========================
if st.session_state.menu=="finanzas":

    st.header("📊 Finanzas")

    df = pd.read_sql("SELECT * FROM cuentas WHERE estado='OCUPADO'", conn)

    total = df["precio"].sum() if not df.empty else 0

    st.metric("Ingresos Totales", f"S/ {total:.2f}")