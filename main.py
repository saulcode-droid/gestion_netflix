import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Multiservicios Saúl", page_icon="🚀", layout="wide")

# Diccionario de configuración de perfiles por plataforma
PLATAFORMAS = {
    "NETFLIX": 5,
    "MAX": 5,
    "PRIME VIDEO": 6,
    "DISNEY": 7,
    "CRUNCHYROLL": 5,
    "VIX": 5
}

# --- BASE DE DATOS ---
def get_db():
    conn = sqlite3.connect('gestion_web_multi.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT)''')
    conn.commit()

init_db()

# --- MENÚ LATERAL ---
st.sidebar.title("🎬 Saúl Streaming Pro")
opcion = st.sidebar.radio("Menú Principal:", 
                         ["📊 Dashboard", "➕ Subir Cuentas", "📱 Gestión de Perfiles", "📅 Proveedores", "🔔 Notificaciones"])

# --- DASHBOARD ---
if opcion == "📊 Dashboard":
    st.title("📊 Resumen General Multiplataforma")
    conn = get_db()
    
    # Filtro por plataforma para el resumen
    plat_filter = st.selectbox("Filtrar por Plataforma:", ["TODAS"] + list(PLATAFORMAS.keys()))
    
    query_ctas = "SELECT COUNT(*) as total FROM cuentas"
    query_vendidos = "SELECT COUNT(*) as total FROM perfiles WHERE estado='VENDIDO'"
    
    if plat_filter != "TODAS":
        query_ctas += f" WHERE plataforma='{plat_filter}'"
        query_vendidos += f" AND plataforma='{plat_filter}'"
    
    ctas = pd.read_sql_query(query_ctas, conn)['total'][0]
    vendidos = pd.read_sql_query(query_vendidos, conn)['total'][0]
    
    col1, col2 = st.columns(2)
    col1.metric(f"Cuentas {plat_filter}", ctas)
    col2.metric("Perfiles Vendidos", vendidos)

    st.subheader("📋 Clientes Próximos a Vencer")
    df_c = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    st.dataframe(df_c, use_container_width=True)

# --- SUBIR CUENTAS MULTIPLATAFORMA ---
elif opcion == "➕ Subir Cuentas":
    st.title("➕ Cargar Nueva Plataforma")
    
    with st.form("form_multi"):
        plat_sel = st.selectbox("Selecciona la Plataforma:", list(PLATAFORMAS.keys()))
        email = st.text_input("Correo de la cuenta:")
        password = st.text_input("Contraseña:")
        f_prov = st.date_input("Vencimiento Proveedor:")
        
        num_perfiles = PLATAFORMAS[plat_sel]
        st.info(f"Esta plataforma requiere {num_perfiles} perfiles.")
        
        perfiles_data = []
        cols = st.columns(2)
        for i in range(num_perfiles):
            with cols[i % 2]:
                p_nom = st.text_input(f"Nombre Perfil {i+1}", f"P{i+1}")
                p_pin = st.text_input(f"PIN Perfil {i+1}", "0000", key=f"pin_{i}")
                perfiles_data.append((p_nom, p_pin))
        
        if st.form_submit_button("🚀 ACTIVAR CUENTA"):
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor) VALUES (?,?,?,?)", 
                               (plat_sel, email, password, f_prov.strftime("%d/%m/%Y")))
                for nom, pin in perfiles_data:
                    cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", 
                                   (email, plat_sel, nom, pin))
                conn.commit()
                st.success(f"✅ {plat_sel} cargado con éxito.")
            except: st.error("Error: Esta cuenta ya existe.")

# --- GESTIÓN DE PERFILES (RENOVACIÓN/CORTE AUTOMÁTICO) ---
elif opcion == "📱 Gestión de Perfiles":
    st.title("📱 Administrador de Accesos")
    conn = get_db()
    
    plat_busqueda = st.selectbox("Filtrar Plataforma:", list(PLATAFORMAS.keys()))
    emails = pd.read_sql_query(f"SELECT email FROM cuentas WHERE plataforma='{plat_busqueda}'", conn)['email'].tolist()
    
    if emails:
        sel_email = st.selectbox("Seleccionar Correo:", emails)
        info_cta = pd.read_sql_query(f"SELECT password FROM cuentas WHERE email='{sel_email}'", conn).iloc[0]
        st.warning(f"🔑 **Clave actual:** `{info_cta['password']}`")
        
        perfiles = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_email}'", conn)
        
        for _, row in perfiles.iterrows():
            color = "🟢" if row['estado'] == "LIBRE" else "🔴"
            with st.expander(f"{color} {row['nombre']} | PIN: {row['pin']}"):
                if row['estado'] == 'LIBRE':
                    wa = st.text_input("WhatsApp Cliente:", key=f"wa_{row['id']}")
                    if st.button("🛒 Alquilar 30 Días", key=f"v_{row['id']}"):
                        f_v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{f_v}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    st.write(f"👤 **Cliente:** +{row['whatsapp']} | 📅 **Vence:** {row['fecha_vence']}")
                    c1, c2 = st.columns(2)
                    if c1.button("🔄 Renovación Automática (+30d)", key=f"ren_{row['id']}"):
                        nueva_f = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{nueva_f}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if c2.button("✂️ Corte Automático", key=f"cut_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=None, fecha_vence=None WHERE id={row['id']}")
                        conn.commit(); st.rerun()

# --- PROVEEDORES ---
elif opcion == "📅 Proveedores":
    st.title("📅 Control de Pagos a Proveedores")
    conn = get_db()
    df_p = pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor FROM cuentas", conn)
    st.dataframe(df_p, use_container_width=True)

# --- NOTIFICACIONES ---
elif opcion == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza WhatsApp")
    conn = get_db()
    df_v = pd.read_sql_query("SELECT * FROM perfiles WHERE estado='VENDIDO'", conn)
    
    for _, r in df_v.iterrows():
        f_v = datetime.strptime(r['fecha_vence'], "%d/%m/%Y")
        diff = (f_v - datetime.now()).days
        if diff <= 2:
            st.warning(f"⚠️ {r['plataforma']} - {r['nombre']} vence en {diff} días.")
            msg = f"Hola, recordatorio de tu perfil de {r['plataforma']}. Vence el {r['fecha_vence']}. ¿Deseas renovar?"
            url = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg)}"
            st.markdown(f"[📲 Enviar Recordatorio a +{r['whatsapp']}]({url})")