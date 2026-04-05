import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Streaming Saúl", page_icon="🎬", layout="wide")

# --- CONEXIÓN BASE DE DATOS ---
def get_db():
    conn = sqlite3.connect('gestion_web_netflix.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Actualizamos tabla para incluir contraseña si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT)''')
    conn.commit()

init_db()

# --- INTERFAZ LATERAL ---
st.sidebar.title("🚀 Panel de Control")
opcion = st.sidebar.radio("Selecciona una opción:", 
                         ["📊 Dashboard", "➕ Subir Cuentas", "📱 Gestionar Perfiles", "📅 Proveedores", "🔔 Notificaciones"])

# --- DASHBOARD ---
if opcion == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    conn = get_db()
    total_ctas = pd.read_sql_query("SELECT COUNT(*) as total FROM cuentas", conn)['total'][0]
    total_vendidos = pd.read_sql_query("SELECT COUNT(*) as total FROM perfiles WHERE estado='VENDIDO'", conn)['total'][0]
    total_libres = pd.read_sql_query("SELECT COUNT(*) as total FROM perfiles WHERE estado='LIBRE'", conn)['total'][0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Cuentas Totales", total_ctas)
    col2.metric("Perfiles Vendidos", total_vendidos)
    col3.metric("Perfiles Libres", total_libres)

    st.subheader("👥 Clientes Activos")
    df_clientes = pd.read_sql_query("SELECT email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    st.dataframe(df_clientes, use_container_width=True)

# --- SUBIR CUENTAS ---
elif opcion == "➕ Subir Cuentas":
    st.title("➕ Registrar Nueva Cuenta")
    with st.form("form_subida"):
        email = st.text_input("Correo electrónico:")
        password = st.text_input("Contraseña:")
        f_prov = st.date_input("Vencimiento con Proveedor:")
        p1 = st.text_input("Perfil 1", "P1:0000")
        p2 = st.text_input("Perfil 2", "P2:0000")
        p3 = st.text_input("Perfil 3", "P3:0000")
        p4 = st.text_input("Perfil 4", "P4:0000")
        p5 = st.text_input("Perfil 5", "P5:0000")
        if st.form_submit_button("Guardar Cuenta"):
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO cuentas (email, password, fecha_proveedor) VALUES (?,?,?)", 
                               (email, password, f_prov.strftime("%d/%m/%Y")))
                for p in [p1, p2, p3, p4, p5]:
                    nom, pin = p.split(':')
                    cursor.execute("INSERT INTO perfiles (email, nombre, pin) VALUES (?,?,?)", (email, nom.strip(), pin.strip()))
                conn.commit()
                st.success(f"✅ Cuenta {email} cargada.")
            except: st.error("Error al subir.")

# --- GESTIONAR PERFILES ---
elif opcion == "📱 Gestionar Perfiles":
    st.title("📱 Administración")
    conn = get_db()
    emails = pd.read_sql_query("SELECT email FROM cuentas", conn)['email'].tolist()
    if emails:
        sel_email = st.selectbox("Seleccionar cuenta:", emails)
        perfiles = pd.read_sql_query(f"SELECT id, nombre, pin, estado, whatsapp, fecha_vence FROM perfiles WHERE email='{sel_email}'", conn)
        for i, row in perfiles.iterrows():
            with st.expander(f"👤 {row['nombre']} - {row['estado']}"):
                if row['estado'] == 'LIBRE':
                    wa = st.text_input("WhatsApp Cliente:", key=f"wa_{row['id']}")
                    if st.button("🔴 Vender", key=f"v_{row['id']}"):
                        fv = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{fv}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    st.write(f"📱 WhatsApp: {row['whatsapp']} | 📅 Vence: {row['fecha_vence']}")
                    if st.button("✂️ Liberar Perfil", key=f"lib_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=None, fecha_vence=None WHERE id={row['id']}")
                        conn.commit(); st.rerun()

# --- PROVEEDORES (AHORA CON CONTRASEÑA) ---
elif opcion == "📅 Proveedores":
    st.title("📅 Cuentas y Contraseñas")
    conn = get_db()
    df_prov = pd.read_sql_query("SELECT email, password, fecha_proveedor FROM cuentas", conn)
    st.dataframe(df_prov, use_container_width=True)

# --- CENTRAL DE NOTIFICACIONES ---
elif opcion == "🔔 Notificaciones":
    st.title("🔔 Recordatorios de Pago")
    conn = get_db()
    df_vence = pd.read_sql_query("SELECT email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    
    if not df_vence.empty:
        hoy = datetime.now()
        for idx, r in df_vence.iterrows():
            f_vence = datetime.strptime(r['fecha_vence'], "%d/%m/%Y")
            dias_restantes = (f_vence - hoy).days
            
            if dias_restantes <= 2: # Avisar si faltan 2 días o menos
                col1, col2 = st.columns([3, 1])
                col1.warning(f"⚠️ {r['nombre']} (+{r['whatsapp']}) vence en {max(0, dias_restantes)} días.")
                
                # Mensaje personalizado
                msg = f"Hola {r['nombre']}, te saludamos de Saúl Streaming 🎬. Te recordamos que tu perfil vence el {r['fecha_vence']}. ¡Renueva ahora para no perder tu acceso!"
                url = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg)}"
                col2.markdown(f"[📲 Enviar WhatsApp]({url})")
    else:
        st.success("No hay clientes por vencer pronto.")