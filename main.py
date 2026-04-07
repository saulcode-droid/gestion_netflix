import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
st.set_page_config(page_title="STREAMING PRO MAX", layout="wide")
DB = "streaming.db"

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- DB ----------------
conn = db()
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
id INTEGER PRIMARY KEY,
user TEXT UNIQUE,
password TEXT,
rango TEXT DEFAULT 'USER'
)''')

c.execute('''CREATE TABLE IF NOT EXISTS cuentas (
id INTEGER PRIMARY KEY,
plataforma TEXT,
email TEXT,
password TEXT,
vencimiento TEXT,
precio REAL
)''')

c.execute('''CREATE TABLE IF NOT EXISTS clientes (
id INTEGER PRIMARY KEY,
nombre TEXT,
whatsapp TEXT
)''')

conn.commit()

# ADMIN
c.execute("SELECT * FROM usuarios WHERE user='admin'")
if not c.fetchone():
    c.execute("INSERT INTO usuarios (user,password,rango) VALUES (?,?,?)",
              ("admin", hash_pass("admin123"), "ADMIN"))
    conn.commit()

# ---------------- CSS PRO ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#020617,#0f172a);
    color: white;
}

/* TITULO */
.title {
    text-align:center;
    font-size:38px;
    font-weight:900;
    background: linear-gradient(90deg,#00f5ff,#00ff85);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

/* BOTONES GRANDES */
.btn-grid button {
    height:120px;
    width:100%;
    border-radius:16px;
    font-size:16px;
    font-weight:600;
    background: #111827;
    border:1px solid rgba(255,255,255,0.1);
    transition:0.3s;
}
.btn-grid button:hover {
    transform:scale(1.05);
    box-shadow:0 0 20px #00ffff;
}

/* LOGIN */
.login {
    background: rgba(255,255,255,0.05);
    padding:35px;
    border-radius:20px;
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
        st.markdown("<div class='login'>", unsafe_allow_html=True)
        st.markdown("<div class='title'>STREAMING PRO</div>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["LOGIN", "REGISTRO"])

        with tab1:
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")

            if st.button("Ingresar"):
                c.execute("SELECT id,password FROM usuarios WHERE user=?", (u,))
                res = c.fetchone()
                if res and res[1] == hash_pass(p):
                    st.session_state.auth = True
                    st.session_state.uid = res[0]
                    st.session_state.step = "modo"
                    st.rerun()
                else:
                    st.error("Datos incorrectos")

        with tab2:
            nu = st.text_input("Nuevo usuario")
            np = st.text_input("Nueva contraseña", type="password")
            if st.button("Registrar"):
                try:
                    c.execute("INSERT INTO usuarios (user,password) VALUES (?,?)",
                              (nu, hash_pass(np)))
                    conn.commit()
                    st.success("Registrado")
                except:
                    st.error("Usuario existe")

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ---------------- PASO 1 ----------------
if st.session_state.step == "modo":
    st.markdown("<div class='title'>SELECCIONA MODO</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="btn-grid">', unsafe_allow_html=True)
        if st.button("📱 ADMINISTRAR POR PERFILES"):
            st.session_state.tipo = "PERFILES"
            st.session_state.step = "rol"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="btn-grid">', unsafe_allow_html=True)
        if st.button("📧 CUENTAS COMPLETAS"):
            st.session_state.tipo = "CUENTAS"
            st.session_state.step = "rol"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- PASO 2 ----------------
elif st.session_state.step == "rol":
    st.markdown("<div class='title'>TIPO DE USUARIO</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="btn-grid">', unsafe_allow_html=True)
        if st.button("👤 CLIENTE FINAL"):
            st.session_state.step = "panel"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="btn-grid">', unsafe_allow_html=True)
        if st.button("💼 COMISIONISTA"):
            st.session_state.step = "panel"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- PANEL ----------------
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
            st.markdown('<div class="btn-grid">', unsafe_allow_html=True)
            if st.button(op):
                st.session_state.modulo = op
            st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")

    # ---------------- FUNCIONALIDAD ----------------

    if st.session_state.modulo == "➕ SUBIR CUENTAS":
        st.subheader("Subir cuentas")

        with st.form("subir"):
            plat = st.selectbox("Plataforma", ["NETFLIX","DISNEY","PRIME"])
            email = st.text_input("Correo")
            password = st.text_input("Contraseña")
            precio = st.number_input("Precio")
            fecha = st.date_input("Vencimiento")

            if st.form_submit_button("Guardar"):
                c.execute("INSERT INTO cuentas (plataforma,email,password,vencimiento,precio) VALUES (?,?,?,?,?)",
                          (plat,email,password,str(fecha),precio))
                conn.commit()
                st.success("Cuenta guardada")

    elif st.session_state.modulo == "⚙️ ADMINISTRAR":
        st.subheader("Administrar")
        df = pd.read_sql("SELECT * FROM cuentas", conn)
        st.dataframe(df)

    elif st.session_state.modulo == "👥 CLIENTES":
        st.subheader("Clientes")
        bus = st.text_input("Buscar WhatsApp")
        df = pd.read_sql("SELECT * FROM clientes", conn)
        st.dataframe(df)

    elif st.session_state.modulo == "💸 VENDER":
        st.subheader("Ventas (próximo nivel)")

    elif st.session_state.modulo == "📦 CUENTAS":
        st.subheader("Cuentas disponibles")
        df = pd.read_sql("SELECT plataforma, COUNT(*) as total FROM cuentas GROUP BY plataforma", conn)
        st.dataframe(df)

    elif st.session_state.modulo == "🔔 NOTIFICACIONES":
        st.subheader("Notificaciones")

    elif st.session_state.modulo == "💰 FINANZAS":
        st.subheader("Finanzas")
        total = pd.read_sql("SELECT SUM(precio) FROM cuentas", conn).iloc[0,0]
        st.metric("Ingresos", f"S/ {total or 0}")

    elif st.session_state.modulo == "👨‍💻 USUARIOS":
        st.subheader("Usuarios")
        df = pd.read_sql("SELECT user,rango FROM usuarios", conn)
        st.dataframe(df)

    elif st.session_state.modulo == "👤 MI CUENTA":
        st.subheader("Mi cuenta")
        newp = st.text_input("Nueva contraseña", type="password")
        if st.button("Actualizar"):
            c.execute("UPDATE usuarios SET password=? WHERE id=?",
                      (hash_pass(newp), st.session_state.uid))
            conn.commit()
            st.success("Actualizado")