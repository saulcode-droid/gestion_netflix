import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Netflix Saúl", page_icon="🎬", layout="wide")

# --- CONEXIÓN BASE DE DATOS ---
def get_db():
    conn = sqlite3.connect('gestion_web_netflix.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT)''')
    conn.commit()

init_db()

# --- INTERFAZ LATERAL (MENÚ) ---
st.sidebar.title("🚀 Panel de Control")
opcion = st.sidebar.radio("Selecciona una opción:", 
                         ["📊 Dashboard", "➕ Subir Cuentas", "📱 Gestionar Perfiles", "📅 Vencimientos Proveedor"])

# --- LÓGICA DE DASHBOARD ---
if opcion == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    conn = get_db()
    
    # Métricas rápidas
    total_ctas = pd.read_sql_query("SELECT COUNT(*) as total FROM cuentas", conn)['total'][0]
    total_vendidos = pd.read_sql_query("SELECT COUNT(*) as total FROM perfiles WHERE estado='VENDIDO'", conn)['total'][0]
    total_libres = pd.read_sql_query("SELECT COUNT(*) as total FROM perfiles WHERE estado='LIBRE'", conn)['total'][0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Cuentas Totales", total_ctas)
    col2.metric("Perfiles Vendidos", total_vendidos, delta_color="inverse")
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
        st.write("Configura los 5 Perfiles (Nombre:PIN)")
        p1 = st.text_input("Perfil 1", "P1:0000")
        p2 = st.text_input("Perfil 2", "P2:0000")
        p3 = st.text_input("Perfil 3", "P3:0000")
        p4 = st.text_input("Perfil 4", "P4:0000")
        p5 = st.text_input("Perfil 5", "P5:0000")
        
        btn_subir = st.form_submit_button("Guardar Cuenta")
        
        if btn_subir:
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO cuentas (email, password, fecha_proveedor) VALUES (?,?,?)", 
                               (email, password, f_prov.strftime("%d/%m/%Y")))
                
                perfiles_lista = [p1, p2, p3, p4, p5]
                for p in perfiles_lista:
                    nom, pin = p.split(':')
                    cursor.execute("INSERT INTO perfiles (email, nombre, pin) VALUES (?,?,?)", (email, nom, pin))
                
                conn.commit()
                st.success(f"✅ Cuenta {email} cargada correctamente.")
            except Exception as e:
                st.error(f"❌ Error: El correo ya existe o el formato es incorrecto.")

# --- GESTIONAR PERFILES (Vender / Notificar / Cortar) ---
elif opcion == "📱 Gestionar Perfiles":
    st.title("📱 Administración de Perfiles")
    conn = get_db()
    
    emails = pd.read_sql_query("SELECT email FROM cuentas", conn)['email'].tolist()
    if not emails:
        st.warning("No hay cuentas registradas.")
    else:
        sel_email = st.selectbox("Selecciona una cuenta para gestionar:", emails)
        
        # Traer clave de la cuenta
        clave = pd.read_sql_query(f"SELECT password FROM cuentas WHERE email='{sel_email}'", conn)['password'][0]
        st.info(f"🗝 **Contraseña de la cuenta:** `{clave}`")
        
        perfiles = pd.read_sql_query(f"SELECT id, nombre, pin, estado, whatsapp, fecha_vence FROM perfiles WHERE email='{sel_email}'", conn)
        
        for index, row in perfiles.iterrows():
            with st.expander(f"👤 {row['nombre']} | PIN: {row['pin']} | {row['estado']}"):
                col_a, col_b = st.columns(2)
                
                if row['estado'] == 'LIBRE':
                    wa = col_a.text_input(f"WhatsApp del Cliente (+)", key=f"wa_{row['id']}")
                    if col_a.button(f"🔴 Marcar como Vendido", key=f"btn_v_{row['id']}"):
                        f_v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{f_v}' WHERE id={row['id']}")
                        conn.commit()
                        st.rerun()
                else:
                    col_a.write(f"📱 **Cliente:** {row['whatsapp']}")
                    col_a.write(f"📅 **Vence:** {row['fecha_vence']}")
                    
                    if col_a.button("✂️ Cortar Servicio (Liberar)", key=f"cut_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=None, fecha_vence=None WHERE id={row['id']}")
                        conn.commit()
                        st.rerun()
                    
                    # Botones de Notificación
                    st.write("---")
                    st.write("🔔 **Enviar Notificación por WhatsApp:**")
                    msg1 = "Hola, tu perfil vence mañana. ¿Deseas renovar?"
                    msg2 = "Hola, tu perfil vence hoy. Evita el corte."
                    
                    url1 = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg1)}"
                    url2 = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg2)}"
                    
                    st.markdown(f"[📩 Avisar Vence Mañana]({url1})", unsafe_allow_html=True)
                    st.markdown(f"[📩 Avisar Vence Hoy]({url2})", unsafe_allow_html=True)

# --- VENCIMIENTOS PROVEEDOR ---
elif opcion == "📅 Vencimientos Proveedor":
    st.title("📅 Renovación con Proveedores")
    conn = get_db()
    df_prov = pd.read_sql_query("SELECT email, fecha_proveedor FROM cuentas ORDER BY id DESC", conn)
    st.table(df_prov)