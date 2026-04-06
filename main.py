import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

# --- CONFIG ---
st.set_page_config(page_title="PERUVIAN STREAMING PRO", page_icon="💎", layout="wide")

DB_NAME = 'db_streaming_saul_v15.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT)')
    c.execute("SELECT * FROM usuarios WHERE user='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (user,password,rango) VALUES ('admin', ?, 'ADMIN')",(hash_pass('admin123'),))
    conn.commit()

init_db()

# --- CSS PRO ---
st.markdown("""
<style>
body {background: #0f172a;}
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: white;
}

/* LOGIN CARD */
.login-box {
    background: rgba(255,255,255,0.05);
    padding: 40px;
    border-radius: 20px;
    backdrop-filter: blur(12px);
    box-shadow: 0 0 25px rgba(0,0,0,0.5);
}

/* BOTONES */
.stButton>button {
    background: linear-gradient(135deg, #00ffcc, #0066ff);
    border: none;
    border-radius: 12px;
    padding: 12px;
    font-weight: bold;
    color: white;
    transition: 0.3s;
}
.stButton>button:hover {
    transform: scale(1.05);
}

/* TARJETAS */
.card {
    background: #111827;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.1);
}
.card img {
    width: 70px;
    margin-bottom: 10px;
}
.card:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(0,255,255,0.3);
    transition: 0.3s;
}

.title {
    text-align:center;
    font-size:40px;
    font-weight:800;
    background: linear-gradient(90deg,#00ffcc,#ffffff);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}
</style>
""", unsafe_allow_html=True)

# --- SESSION ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

# =====================================
# LOGIN PRO
# =====================================
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,1.2,1])

    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<div class='title'>STREAMING PRO</div>", unsafe_allow_html=True)
        st.write("")

        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        if st.button("Ingresar"):
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id,password FROM usuarios WHERE user=?",(user,))
            res = c.fetchone()

            if res and res[1] == hash_pass(password):
                st.session_state.auth = True
                st.session_state.user_id = res[0]
                st.success("Bienvenido 🔥")
                st.rerun()
            else:
                st.error("Datos incorrectos")

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# =====================================
# DASHBOARD PRINCIPAL
# =====================================
st.markdown("<div class='title'>PANEL PRINCIPAL</div>", unsafe_allow_html=True)
st.write("")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <img src="https://cdn-icons-png.flaticon.com/512/3502/3502601.png">
        <h4>SUBIR CUENTAS</h4>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Entrar", key="subir"):
        st.session_state.menu = "SUBIR"

with col2:
    st.markdown("""
    <div class="card">
        <img src="https://cdn-icons-png.flaticon.com/512/869/869121.png">
        <h4>GESTIÓN</h4>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Entrar", key="gestion"):
        st.session_state.menu = "GESTION"

with col3:
    st.markdown("""
    <div class="card">
        <img src="https://cdn-icons-png.flaticon.com/512/3135/3135706.png">
        <h4>FINANZAS</h4>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Entrar", key="finanzas"):
        st.session_state.menu = "FINANZAS"

st.write("---")

# =====================================
# SUBMODULOS
# =====================================
menu = st.session_state.get("menu", "")

if menu == "SUBIR":
    st.subheader("Registrar Cuenta")

    with st.form("form"):
        plataforma = st.selectbox("Plataforma", ["NETFLIX","DISNEY","PRIME"])
        email = st.text_input("Correo")
        password = st.text_input("Contraseña")
        costo = st.number_input("Costo", 0.0)

        if st.form_submit_button("Guardar"):
            conn = get_db()
            conn.execute("INSERT INTO cuentas (tipo_negocio, plataforma, email, password, costo) VALUES (?,?,?,?,?)",
                         ("CUENTAS", plataforma, email, password, costo))
            conn.commit()
            st.success("Cuenta guardada")

elif menu == "GESTION":
    st.subheader("Cuentas Registradas")
    conn = get_db()
    df = pd.read_sql("SELECT * FROM cuentas", conn)
    st.dataframe(df)

elif menu == "FINANZAS":
    st.subheader("Resumen Financiero")
    conn = get_db()
    total = pd.read_sql("SELECT SUM(costo) as total FROM cuentas", conn).iloc[0,0]
    st.metric("Gasto Total", f"S/ {total or 0:.2f}")