import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming Web Pro", page_icon="🚀", layout="wide")

# Configuración Maestra de Perfiles
PLATAFORMAS_CONFIG = {
    "NETFLIX": 5,
    "MAX": 5,
    "PRIME VIDEO": 6,
    "DISNEY": 7,
    "CRUNCHYROLL": 5,
    "VIX": 5
}

# --- BASE DE DATOS ---
def get_db():
    conn = sqlite3.connect('db_saul_streaming_v4.db', check_same_thread=False)
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
st.sidebar.title("🎬 Panel Saúl V4.5")
menu = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "📅 Proveedores", "🔔 Notificaciones"])

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Resumen de Ventas")
    conn = get_db()
    
    c1, c2, c3 = st.columns(3)
    total_ctas = pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0]
    total_vendidos = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0]
    total_libres = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0]
    
    c1.metric("Cuentas Totales", total_ctas)
    c2.metric("Perfiles Vendidos", total_vendidos)
    c3.metric("Perfiles Disponibles", total_libres)

    st.subheader("👥 Clientes Activos")
    df_clientes = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    st.dataframe(df_clientes, use_container_width=True)

# --- 2. SECCIÓN PLATAFORMAS (DINÁMICO CORREGIDO) ---
elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Plataformas")
    
    # Selección de plataforma fuera del form para refresco inmediato
    plat_sel = st.selectbox("1. Selecciona la Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_perfiles = PLATAFORMAS_CONFIG[plat_sel]
    
    st.info(f"Configurando **{num_perfiles} perfiles** para **{plat_sel}**")

    with st.form("form_registro_pro"):
        col_mail, col_pass = st.columns(2)
        mail = col_mail.text_input("Correo de cuenta:")
        pasw = col_pass.text_input("Contraseña:")
        
        # Fecha en formato DD/MM/YYYY
        f_prov = st.date_input("Vencimiento con Proveedor:", format="DD/MM/YYYY")
        
        st.write("---")
        st.write("📝 **Configuración de Perfiles**")
        
        perfiles_lista = []
        # Crear filas de perfiles de 4 en 4 para que no se vea amontonado
        for i in range(num_perfiles):
            col_p_nom, col_p_pin = st.columns([3, 1])
            p_n = col_p_nom.text_input(f"Nombre Perfil {i+1}", f"P{i+1}", key=f"n_{plat_sel}_{i}")
            p_p = col_p_pin.text_input(f"PIN", "0000", key=f"p_{plat_sel}_{i}")
            perfiles_lista.append((p_n, p_p))
        
        submit = st.form_submit_button("🚀 GUARDAR Y ACTIVAR PLATAFORMA")
        
        if submit:
            if not mail or not pasw:
                st.error("❌ Por favor completa el correo y la contraseña.")
            else:
                conn = get_db()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor) VALUES (?,?,?,?)", 
                                   (plat_sel, mail, pasw, f_prov.strftime("%d/%m/%Y")))
                    for nom, pin in perfiles_lista:
                        cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", 
                                       (mail, plat_sel, nom, pin))
                    conn.commit()
                    st.success(f"✅ {plat_sel} cargada correctamente.")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error: El correo ya existe o hubo un problema: {e}")

# --- 3. GESTIÓN DE PERFILES ---
elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Panel de Ventas")
    conn = get_db()
    
    col_f1, col_f2 = st.columns(2)
    p_filtro = col_f1.selectbox("Filtrar Plataforma:", ["TODAS"] + list(PLATAFORMAS_CONFIG.keys()))
    
    query = "SELECT email FROM cuentas"
    if p_filtro != "TODAS":
        query += f" WHERE plataforma='{p_filtro}'"
    
    emails = pd.read_sql_query(query, conn)['email'].tolist()
    
    if not emails:
        st.warning("No hay cuentas registradas.")
    else:
        sel_mail = col_f2.selectbox("Selecciona la cuenta:", emails)
        cta_data = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel_mail}'", conn).iloc[0]
        st.markdown(f"### 🔑 Clave {cta_data['plataforma']}: `{cta_data['password']}`")
        
        perfiles = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_mail}'", conn)
        
        for _, row in perfiles.iterrows():
            status = "🟢 LIBRE" if row['estado'] == 'LIBRE' else f"🔴 VENDIDO a {row['whatsapp']}"
            with st.expander(f"{row['nombre']} | PIN: {row['pin']} | {status}"):
                c1, c2 = st.columns(2)
                
                if row['estado'] == 'LIBRE':
                    cliente_wa = c1.text_input("WhatsApp Cliente:", key=f"wa_{row['id']}")
                    if c1.button("🛒 Marcar Vendido", key=f"btn_v_{row['id']}"):
                        vence = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{cliente_wa}', fecha_vence='{vence}' WHERE id={row['id']}")
                        conn.commit()
                        st.rerun()
                else:
                    c1.write(f"📅 **Vence el:** {row['fecha_vence']}")
                    if c1.button("🔄 Renovar (+30 días)", key=f"ren_{row['id']}"):
                        f_actual = datetime.strptime(row['fecha_vence'], "%d/%m/%Y")
                        f_nueva = (f_actual + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{f_nueva}' WHERE id={row['id']}")
                        conn.commit()
                        st.rerun()
                    
                    if c2.button("✂️ CORTE (Liberar)", key=f"cut_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=None, fecha_vence=None WHERE id={row['id']}")
                        conn.commit()
                        st.rerun()

# --- 4. PROVEEDORES ---
elif menu == "📅 Proveedores":
    st.title("📅 Control de Proveedores")
    conn = get_db()
    df_p = pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor FROM cuentas", conn)
    st.table(df_p)

# --- 5. NOTIFICACIONES ---
elif menu == "🔔 Notificaciones":
    st.title("🔔 Recordatorios WhatsApp")
    conn = get_db()
    df_n = pd.read_sql_query("SELECT * FROM perfiles WHERE estado='VENDIDO'", conn)
    
    if df_n.empty:
        st.success("No hay perfiles vendidos actualmente.")
    else:
        for _, r in df_n.iterrows():
            fv = datetime.strptime(r['fecha_vence'], "%d/%m/%Y")
            dias = (fv - datetime.now()).days
            if dias <= 2:
                st.warning(f"⚠️ {r['plataforma']} - {r['nombre']} vence en {max(0, dias)} días.")
                msg = f"Hola {r['nombre']}, te aviso que tu perfil de {r['plataforma']} vence el {r['fecha_vence']}. ¿Deseas renovar?"
                url = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg)}"
                st.markdown(f"[📲 Enviar Recordatorio a +{r['whatsapp']}]({url})")