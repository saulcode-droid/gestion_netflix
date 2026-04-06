import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------
# CONFIG
# ---------------------------------
st.set_page_config(page_title="STREAMING PRO MAX", layout="wide")

DB = "streaming.db"

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------------------------
# DB INIT
# ---------------------------------
conn = db()
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
id INTEGER PRIMARY KEY,
user TEXT UNIQUE,
password TEXT,
rango TEXT DEFAULT 'USER'
)''')

c.execute('''CREATE TABLE IF NOT EXISTS clientes (
id INTEGER PRIMARY KEY,
nombre TEXT,
whatsapp TEXT
)''')

conn.commit()

# ADMIN DEFAULT
c.execute("SELECT * FROM usuarios WHERE user='admin'")
if not c.fetchone():
    c.execute("INSERT INTO usuarios (user,password,rango) VALUES (?,?,?)",
              ("admin", hash_pass("admin123"), "ADMIN"))
    conn.commit()

# ---------------------------------
# CSS PRO
# ---------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#020617,#0f172a);
    color: white;
}

/* TITULO */
.title {
    text-align:center;
    font-size:40px;
    font-weight:900;
    background: linear-gradient(90deg,#00f5ff,#00ff85);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

/* BOTONES GRANDES */
.big-btn button {
    height:120px;
    width:100%;
    border-radius:18px;
    font-size:18px;
    font-weight:bold;
    background: linear-gradient(135deg,#111827,#1f2937);
    border:1px solid rgba(255,255,255,0.1);
    transition:0.3s;
}
.big-btn button:hover {
    transform:scale(1.05);
    box-shadow:0 0 20px #00ffff;
}

/* LOGIN BOX */
.login {
    background: rgba(255,255,255,0.05);
    padding:40px;
    border-radius:20px;
    backdrop-filter: blur(10px);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------
# SESSION
# ---------------------------------
if "auth" not in st.session_state:
    st.session_state.auth = False
if "step" not in st.session_state:
    st.session_state.step = "login"

# ---------------------------------
# LOGIN + REGISTER
# ---------------------------------
if not st.session_state.auth:

    col1, col2, col3 = st.columns([1,1.2,1])

    with col2:
        st.markdown("<div class='login'>", unsafe_allow_html=True)
        st.markdown("<div class='title'>STREAMING PRO</div>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 LOGIN", "📝 REGISTRO"])

        # LOGIN
        with tab1:
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")

            if st.button("Ingresar"):
                c.execute("SELECT id,password,rango FROM usuarios WHERE user=?", (u,))
                res = c.fetchone()

                if res and res[1] == hash_pass(p):
                    st.session_state.auth = True
                    st.session_state.uid = res[0]
                    st.session_state.rango = res[2]
                    st.session_state.step = "modo"
                    st.rerun()
                else:
                    st.error("Datos incorrectos")

        # REGISTRO
        with tab2:
            new_u = st.text_input("Nuevo usuario")
            new_p = st.text_input("Nueva contraseña", type="password")

            if st.button("Registrarme"):
                try:
                    c.execute("INSERT INTO usuarios (user,password) VALUES (?,?)",
                              (new_u, hash_pass(new_p)))
                    conn.commit()
                    st.success("Registrado, espera aprobación ADMIN")
                except:
                    st.error("Usuario ya existe")

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ---------------------------------
# PASO 1: MODO
# ---------------------------------
if st.session_state.step == "modo":
    st.markdown("<div class='title'>SELECCIONA MODO</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        if st.button("📱 ADMINISTRAR POR PERFILES"):
            st.session_state.tipo = "PERFILES"
            st.session_state.step = "rol"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        if st.button("📧 CUENTAS COMPLETAS"):
            st.session_state.tipo = "CUENTAS"
            st.session_state.step = "rol"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------
# PASO 2: ROL
# ---------------------------------
elif st.session_state.step == "rol":
    st.markdown("<div class='title'>TIPO DE USUARIO</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        if st.button("👤 CLIENTE FINAL"):
            st.session_state.rol = "CLIENTE"
            st.session_state.step = "panel"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        if st.button("💼 COMISIONISTA"):
            st.session_state.rol = "COMISIONISTA"
            st.session_state.step = "panel"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------
# PANEL PRINCIPAL
# ---------------------------------
elif st.session_state.step == "panel":

    st.markdown(f"<div class='title'>PANEL {st.session_state.tipo}</div>", unsafe_allow_html=True)

    opciones = [
        "➕ SUBIR CUENTAS",
        "⚙️ ADMINISTRAR",
        "👥 CLIENTES",
        "💸 VENDER",
        "📦 CUENTAS",
        "🔔 NOTIFICACIONES",
        "💰 FINANZAS",
        "👨‍💻 USUARIOS",
        "👤 MI CUENTA"
    ]

    cols = st.columns(3)

    for i, op in enumerate(opciones):
        with cols[i % 3]:
            st.markdown('<div class="big-btn">', unsafe_allow_html=True)
            if st.button(op, key=op):
                st.session_state.modulo = op
            st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")

    # ----------------------------
    # SUBMODULOS (BASE)
    # ----------------------------
    mod = st.session_state.get("modulo", "")

    if mod == "➕ SUBIR CUENTAS":
        st.header("Subir cuentas")
        st.info("Aquí irá lógica: perfiles, precios, vencimientos 30 días")

    elif mod == "⚙️ ADMINISTRAR":
        st.header("Administrar cuentas/perfiles")

    elif mod == "👥 CLIENTES":
        st.header("Clientes")
        bus = st.text_input("Buscar por WhatsApp")
        df = pd.read_sql("SELECT * FROM clientes", conn)
        st.dataframe(df)

    elif mod == "💸 VENDER":
        st.header("Ventas")
        st.info("Aquí podrás vender, renovar, cortar, enviar WhatsApp")

    elif mod == "📦 CUENTAS":
        st.header("Disponibilidad de cuentas")

    elif mod == "🔔 NOTIFICACIONES":
        st.header("Notificaciones masivas")

    elif mod == "💰 FINANZAS":
        st.header("Finanzas")
        st.metric("Ingresos", "S/ 0")
        st.metric("Egresos", "S/ 0")
        st.metric("Ganancia", "S/ 0")

    elif mod == "👨‍💻 USUARIOS":
        st.header("Usuarios")
        df = pd.read_sql("SELECT user,rango FROM usuarios", conn)
        st.dataframe(df)

    elif mod == "👤 MI CUENTA":
        st.header("Mi cuenta")
        new_pass = st.text_input("Nueva contraseña", type="password")
        if st.button("Actualizar"):
            c.execute("UPDATE usuarios SET password=? WHERE id=?",
                      (hash_pass(new_pass), st.session_state.uid))
            conn.commit()
            st.success("Contraseña actualizada")