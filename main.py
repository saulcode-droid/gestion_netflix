import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib

# ---------------- CONFIG ----------------
st.set_page_config(page_title="STREAMING PRO", layout="wide")

DB = "streaming_pro.db"

def conectar():
    return sqlite3.connect(DB, check_same_thread=False)

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- DB ----------------
def crear_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY,
        user TEXT UNIQUE,
        pass TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS cuentas(
        id INTEGER PRIMARY KEY,
        plataforma TEXT,
        email TEXT,
        password TEXT,
        estado TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS perfiles(
        id INTEGER PRIMARY KEY,
        email TEXT,
        nombre TEXT,
        pin TEXT,
        estado TEXT,
        vence TEXT
    )""")

    # ADMIN FIJO
    c.execute("INSERT OR IGNORE INTO usuarios(user, pass) VALUES(?,?)",
              ("admin", hash_pass("admin123")))

    conn.commit()

crear_db()

# ---------------- ESTILOS ----------------
st.markdown("""
<style>
body {background:#0b0f1a;}
.big-btn button {
    height:120px;
    width:100%;
    font-size:20px;
    border-radius:20px;
    background: linear-gradient(145deg,#111,#1c2333);
    color:white;
    border:1px solid #2a2a2a;
}
.big-btn button:hover {
    transform:scale(1.03);
    border:1px solid #00ffd5;
}
.card {
    background:#111827;
    padding:25px;
    border-radius:15px;
    text-align:center;
    color:white;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔐 Login")
        user = st.text_input("Usuario")
        pw = st.text_input("Password", type="password")

        if st.button("Entrar"):
            conn = conectar()
            c = conn.cursor()
            c.execute("SELECT * FROM usuarios WHERE user=?", (user,))
            res = c.fetchone()

            if res and res[2] == hash_pass(pw):
                st.session_state.login = True
                st.rerun()
            else:
                st.error("Datos incorrectos")

    with col2:
        st.subheader("📝 Registro")
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Nueva clave", type="password")

        if st.button("Registrar"):
            try:
                conn = conectar()
                conn.execute("INSERT INTO usuarios(user,pass) VALUES(?,?)",
                             (new_user, hash_pass(new_pass)))
                conn.commit()
                st.success("Registrado (requiere aprobación manual)")
            except:
                st.error("Usuario ya existe")

    st.stop()

# ---------------- MENU PRINCIPAL ----------------
st.title("🚀 PANEL PRO")

menu = st.radio("", ["🏠 Panel", "📦 Subir", "💰 Vender", "📊 Cuentas", "💵 Finanzas"], horizontal=True)

conn = conectar()

# ---------------- PANEL ----------------
if menu == "🏠 Panel":

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="card">📦 CUENTAS<br><h2>{}</h2></div>'.format(
            pd.read_sql("SELECT COUNT(*) FROM cuentas", conn).iloc[0,0]
        ), unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">🟢 DISPONIBLES<br><h2>{}</h2></div>'.format(
            pd.read_sql("SELECT COUNT(*) FROM cuentas WHERE estado='LIBRE'", conn).iloc[0,0]
        ), unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="card">🔴 VENDIDOS<br><h2>{}</h2></div>'.format(
            pd.read_sql("SELECT COUNT(*) FROM cuentas WHERE estado='VENDIDO'", conn).iloc[0,0]
        ), unsafe_allow_html=True)

# ---------------- SUBIR ----------------
elif menu == "📦 Subir":

    st.subheader("➕ Subir cuenta")

    with st.form("subir"):
        plataforma = st.selectbox("Plataforma", ["NETFLIX","DISNEY","HBO"])
        email = st.text_input("Email")
        password = st.text_input("Password")

        if st.form_submit_button("Guardar"):
            conn.execute(
                "INSERT INTO cuentas(plataforma,email,password,estado) VALUES(?,?,?,?)",
                (plataforma, email, password, "LIBRE")
            )
            conn.commit()
            st.success("Cuenta guardada")

# ---------------- VENDER ----------------
elif menu == "💰 Vender":

    st.subheader("🛒 Vender cuenta")

    df = pd.read_sql("SELECT * FROM cuentas WHERE estado='LIBRE'", conn)

    if df.empty:
        st.warning("No hay cuentas disponibles")
    else:
        sel = st.selectbox("Seleccionar cuenta", df["email"])

        cliente = st.text_input("Cliente")

        if st.button("Vender ahora"):
            conn.execute("UPDATE cuentas SET estado='VENDIDO' WHERE email=?", (sel,))
            conn.commit()
            st.success(f"Cuenta vendida a {cliente}")

# ---------------- CUENTAS ----------------
elif menu == "📊 Cuentas":

    st.subheader("📋 Lista de cuentas")
    df = pd.read_sql("SELECT * FROM cuentas", conn)
    st.dataframe(df, use_container_width=True)

# ---------------- FINANZAS ----------------
elif menu == "💵 Finanzas":

    st.subheader("💰 Finanzas")

    total = pd.read_sql("SELECT COUNT(*) FROM cuentas WHERE estado='VENDIDO'", conn).iloc[0,0]

    st.metric("Ventas realizadas", total)