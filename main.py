import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(layout="wide", page_title="STREAMING GOD")

DB = "streaming.db"

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

conn = db()
c = conn.cursor()

# ---------------- DB ----------------
c.execute('''CREATE TABLE IF NOT EXISTS cuentas (
id INTEGER PRIMARY KEY,
plataforma TEXT,
email TEXT,
password TEXT,
precio REAL,
estado TEXT,
fecha_vence TEXT,
cliente TEXT
)''')

conn.commit()

# ---------------- CSS ----------------
st.markdown("""
<style>
.card {
    background:#111827;
    padding:30px;
    border-radius:20px;
    text-align:center;
    height:170px;
    transition:0.3s;
}
.card:hover {transform:scale(1.08); box-shadow:0 0 25px cyan;}
.icon {font-size:40px;}
.title {text-align:center; font-size:40px; font-weight:900;
background:linear-gradient(90deg,cyan,lime);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;}
div.stButton>button {
    height:170px; width:100%; opacity:0; position:absolute;
}
</style>
""", unsafe_allow_html=True)

# ---------------- PANEL ----------------
st.markdown("<div class='title'>PANEL DIOS</div>", unsafe_allow_html=True)

menu = ["SUBIR","VENDER","CUENTAS","FINANZAS","NOTIFICAR"]

cols = st.columns(5)

for i,m in enumerate(menu):
    with cols[i]:
        st.markdown("<div style='position:relative'>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'><div class='icon'>🔥</div><h3>{m}</h3></div>", unsafe_allow_html=True)
        if st.button(m):
            st.session_state.mod = m
        st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

mod = st.session_state.get("mod","")

# ---------------- SUBIR ----------------
if mod == "SUBIR":
    st.subheader("Subir cuenta")

    with st.form("subir"):
        plat = st.selectbox("Plataforma", ["NETFLIX","DISNEY"])
        email = st.text_input("Correo")
        password = st.text_input("Clave")
        precio = st.number_input("Precio")

        if st.form_submit_button("Guardar"):
            vence = datetime.now() + timedelta(days=30)

            c.execute("INSERT INTO cuentas VALUES (NULL,?,?,?,?,?,?,?)",
                      (plat,email,password,precio,"LIBRE",vence.strftime("%Y-%m-%d"),""))
            conn.commit()
            st.success("Cuenta lista")

# ---------------- VENDER ----------------
elif mod == "VENDER":
    df = pd.read_sql("SELECT * FROM cuentas WHERE estado='LIBRE'", conn)

    if df.empty:
        st.warning("Sin cuentas")
    else:
        cuenta = st.selectbox("Cuenta", df["email"])
        cliente = st.text_input("WhatsApp cliente")

        if st.button("VENDER"):
            fecha = datetime.now() + timedelta(days=30)

            c.execute("UPDATE cuentas SET estado='OCUPADO', cliente=?, fecha_vence=? WHERE email=?",
                      (cliente, fecha.strftime("%Y-%m-%d"), cuenta))
            conn.commit()

            msg = f"Cuenta: {cuenta}\nDuración: 30 días"
            url = f"https://wa.me/{cliente}?text={urllib.parse.quote(msg)}"

            st.success("Vendido")
            st.markdown(f"[Enviar WhatsApp]({url})")

# ---------------- CUENTAS ----------------
elif mod == "CUENTAS":
    df = pd.read_sql("SELECT * FROM cuentas", conn)

    hoy = datetime.now()

    for _,r in df.iterrows():
        vence = datetime.strptime(r["fecha_vence"], "%Y-%m-%d")
        dias = (vence - hoy).days

        st.write(f"{r['email']} - {r['estado']} - Vence en {dias} días")

        col1,col2 = st.columns(2)

        # RENOVAR
        with col1:
            if st.button(f"Renovar {r['id']}"):
                nueva = vence + timedelta(days=30)
                c.execute("UPDATE cuentas SET fecha_vence=? WHERE id=?",
                          (nueva.strftime("%Y-%m-%d"), r["id"]))
                conn.commit()
                st.rerun()

        # CORTAR
        with col2:
            if st.button(f"Cortar {r['id']}"):
                c.execute("UPDATE cuentas SET estado='LIBRE', cliente='' WHERE id=?", (r["id"],))
                conn.commit()
                st.rerun()

# ---------------- NOTIFICACIONES ----------------
elif mod == "NOTIFICAR":
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
elif mod == "FINANZAS":
    df = pd.read_sql("SELECT * FROM cuentas", conn)

    ingresos = df[df["estado"]=="OCUPADO"]["precio"].sum()

    st.metric("Ingresos", ingresos)