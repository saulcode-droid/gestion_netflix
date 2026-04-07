import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# ---------------- CONFIG ----------------
st.set_page_config(page_title="STREAMING PRO", layout="wide")

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
estado TEXT DEFAULT 'LIBRE',
fecha_vence TEXT,
cliente TEXT
)''')

conn.commit()

# ADMIN DEFAULT
c.execute("SELECT * FROM usuarios WHERE user='admin'")
if not c.fetchone():
    c.execute("INSERT INTO usuarios (user,password) VALUES (?,?)",
              ("admin", hash_pass("admin123")))
    conn.commit()

# ---------------- CSS ----------------
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#020617,#0f172a);}

.title {
text-align:center;
font-size:42px;
font-weight:900;
background: linear-gradient(90deg,#00f5ff,#00ff85);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
}

.btn button {
height:120px;
width:100%;
border-radius:15px;
font-size:18px;
font-weight:bold;
background:#111827;
color:white;
border:1px solid rgba(255,255,255,0.1);
}
.btn button:hover {
transform:scale(1.05);
box-shadow:0 0 20px cyan;
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
    st.markdown("<div class='title'>LOGIN</div>", unsafe_allow_html=True)

    col1,col2,col3 = st.columns([1,1,1])

    with col2:
        tab1, tab2 = st.tabs(["LOGIN","REGISTRO"])

        with tab1:
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")

            if st.button("Ingresar"):
                c.execute("SELECT * FROM usuarios WHERE user=?", (u,))
                r = c.fetchone()
                if r and r[2] == hash_pass(p):
                    st.session_state.auth = True
                    st.session_state.step = "panel"
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

    st.stop()

# ---------------- PANEL ----------------
st.markdown("<div class='title'>PANEL PRO</div>", unsafe_allow_html=True)

menu = [
    "➕ SUBIR",
    "💸 VENDER",
    "📦 CUENTAS",
    "🔔 NOTIFICAR",
    "💰 FINANZAS"
]

cols = st.columns(5)

for i,m in enumerate(menu):
    with cols[i]:
        st.markdown("<div class='btn'>", unsafe_allow_html=True)
        if st.button(m):
            st.session_state.modulo = m
        st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

mod = st.session_state.modulo

# ---------------- SUBIR ----------------
if mod == "➕ SUBIR":
    st.subheader("Subir cuenta")

    with st.form("subir"):
        plat = st.selectbox("Plataforma", ["NETFLIX","DISNEY","PRIME"])
        email = st.text_input("Correo")
        password = st.text_input("Clave")
        precio = st.number_input("Precio")

        if st.form_submit_button("Guardar"):
            vence = datetime.now() + timedelta(days=30)

            c.execute("INSERT INTO cuentas VALUES (NULL,?,?,?,?,?,?,?)",
                      (plat,email,password,precio,"LIBRE",
                       vence.strftime("%Y-%m-%d"),""))
            conn.commit()
            st.success("Cuenta guardada")

# ---------------- VENDER ----------------
elif mod == "💸 VENDER":
    df = pd.read_sql("SELECT * FROM cuentas WHERE estado='LIBRE'", conn)

    if df.empty:
        st.warning("No hay cuentas disponibles")
    else:
        cuenta = st.selectbox("Cuenta", df["email"])
        cliente = st.text_input("WhatsApp cliente")

        if st.button("VENDER AHORA"):
            fecha = datetime.now() + timedelta(days=30)

            c.execute("UPDATE cuentas SET estado='OCUPADO', cliente=?, fecha_vence=? WHERE email=?",
                      (cliente, fecha.strftime("%Y-%m-%d"), cuenta))
            conn.commit()

            msg = f"Cuenta: {cuenta} - 30 días"
            url = f"https://wa.me/{cliente}?text={urllib.parse.quote(msg)}"

            st.success("Venta realizada")
            st.markdown(f"[Enviar WhatsApp]({url})")

# ---------------- CUENTAS ----------------
elif mod == "📦 CUENTAS":
    df = pd.read_sql("SELECT * FROM cuentas", conn)

    for _,r in df.iterrows():
        st.write(r["email"], r["estado"], r["fecha_vence"])

        c1,c2 = st.columns(2)

        with c1:
            if st.button(f"Renovar {r['id']}"):
                nueva = datetime.now() + timedelta(days=30)
                c.execute("UPDATE cuentas SET fecha_vence=? WHERE id=?",
                          (nueva.strftime("%Y-%m-%d"), r["id"]))
                conn.commit()
                st.rerun()

        with c2:
            if st.button(f"Cortar {r['id']}"):
                c.execute("UPDATE cuentas SET estado='LIBRE', cliente='' WHERE id=?",(r["id"],))
                conn.commit()
                st.rerun()

# ---------------- NOTIFICAR ----------------
elif mod == "🔔 NOTIFICAR":
    df = pd.read_sql("SELECT * FROM cuentas WHERE estado='OCUPADO'", conn)

    hoy = datetime.now()

    for _,r in df.iterrows():
        vence = datetime.strptime(r["fecha_vence"], "%Y-%m-%d")
        dias = (vence - hoy).days

        if dias <= 3:
            msg = f"Tu cuenta vence en {dias} días"
            url = f"https://wa.me/{r['cliente']}?text={urllib.parse.quote(msg)}"

            st.warning(f"{r['email']} vence en {dias} días")
            st.markdown(f"[Notificar]({url})")

# ---------------- FINANZAS ----------------
elif mod == "💰 FINANZAS":
    df = pd.read_sql("SELECT * FROM cuentas", conn)
    ingresos = df[df["estado"]=="OCUPADO"]["precio"].sum()
    st.metric("Ingresos", ingresos or 0)