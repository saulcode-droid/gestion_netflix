import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming Finanzas V4.9", page_icon="💰", layout="wide")

PLATAFORMAS_CONFIG = {
    "NETFLIX": 5, "MAX": 5, "PRIME VIDEO": 6, "DISNEY": 7, "CRUNCHYROLL": 5, "VIX": 5
}

# --- BASE DE DATOS ---
def get_db():
    conn = sqlite3.connect('db_saul_streaming_v4.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Asegurar columnas necesarias
    try: cursor.execute("ALTER TABLE perfiles ADD COLUMN precio_venta REAL DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE cuentas ADD COLUMN costo REAL DEFAULT 0")
    except: pass
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT, costo REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, precio_venta REAL)''')
    conn.commit()

init_db()

# --- MENÚ LATERAL ---
st.sidebar.title("🎬 Saúl Streaming v4.9")
menu = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "📅 Proveedores", "💰 Finanzas Pro"])

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Resumen de Inventario")
    conn = get_db()
    total_ctas = pd.read_sql_query("SELECT COUNT(*) as t FROM cuentas", conn)['t'][0]
    total_vendidos = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0]
    total_libres = pd.read_sql_query("SELECT COUNT(*) as t FROM perfiles WHERE estado='LIBRE'", conn)['t'][0]

    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Cuentas en Stock", total_ctas)
    c2.metric("✅ Perfiles Vendidos", total_vendidos)
    c3.metric("🔓 Perfiles Libres", total_libres)

    st.divider()
    st.subheader("👥 Clientes Activos")
    df_clientes = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, precio_venta, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    st.dataframe(df_clientes, use_container_width=True)

# --- 2. PLATAFORMAS (Subida de Cuenta Completa) ---
elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Plataformas")
    plat_sel = st.selectbox("Selecciona la Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_perfiles = PLATAFORMAS_CONFIG[plat_sel]
    
    with st.form("form_registro_pro"):
        c_mail, c_pass, c_costo = st.columns([2, 2, 1])
        mail = c_mail.text_input("📧 Correo de cuenta:")
        pasw = c_pass.text_input("🔑 Contraseña:")
        costo_total_cta = c_costo.number_input("💵 Costo Cuenta Completa (S/):", min_value=0.0, step=1.0)
        f_prov = st.date_input("📅 Vencimiento con Proveedor:", format="DD/MM/YYYY")
        
        perfiles_lista = []
        st.write("---")
        for i in range(num_perfiles):
            col_nom, col_pin = st.columns(2)
            p_n = col_nom.text_input(f"Nombre Perfil {i+1}", f"P{i+1}", key=f"n_{i}")
            p_p = col_pin.text_input(f"PIN Perfil {i+1}", "0000", key=f"p_{i}")
            perfiles_lista.append((p_n, p_p))
        
        if st.form_submit_button("🚀 GUARDAR CUENTA COMPLETA"):
            if mail and pasw:
                conn = get_db(); cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", 
                                   (plat_sel, mail, pasw, f_prov.strftime("%d/%m/%Y"), costo_total_cta))
                    for nom, pin in perfiles_lista:
                        cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", 
                                       (mail, plat_sel, nom, pin))
                    conn.commit()
                    st.success("✅ Cuenta y perfiles guardados."); st.balloons()
                except: st.error("❌ El correo ya existe.")

# --- 3. GESTIÓN DE PERFILES (VENTA CON PRECIO) ---
elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Panel de Ventas y Entregas")
    conn = get_db()
    p_filtro = st.selectbox("🔍 Filtrar por Plataforma:", ["TODAS"] + list(PLATAFORMAS_CONFIG.keys()))
    
    query = "SELECT email FROM cuentas"
    if p_filtro != "TODAS": query += f" WHERE plataforma='{p_filtro}'"
    emails = pd.read_sql_query(query, conn)['email'].tolist()
    
    if emails:
        sel_mail = st.selectbox("📩 Selecciona la cuenta:", emails)
        cta = pd.read_sql_query(f"SELECT plataforma, password FROM cuentas WHERE email='{sel_mail}'", conn).iloc[0]
        perfiles = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{sel_mail}'", conn)
        st.info(f"🔑 **Clave {cta['plataforma']}:** `{cta['password']}`")
        
        for _, row in perfiles.iterrows():
            status = "🟢 LIBRE" if row['estado'] == 'LIBRE' else f"🔴 VENDIDO a {row['whatsapp']} (S/ {row['precio_venta']})"
            with st.expander(f"{row['nombre']} | {status}"):
                c1, c2 = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("📱 WhatsApp Cliente:", key=f"wa_{row['id']}")
                    pv = c2.number_input("💵 Precio de Venta (S/):", min_value=0.0, step=1.0, value=5.0, key=f"pv_{row['id']}")
                    if st.button("🛒 Confirmar Venta", key=f"btn_v_{row['id']}"):
                        vence = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{vence}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    c1.write(f"📅 **Vence:** {row['fecha_vence']}")
                    msg_entrega = (
                        f"💎 *ENTREGA DE CUENTA - {row['plataforma']}* 💎\n\n"
                        f"📧 *Correo:* `{sel_mail}`\n🔑 *Clave:* `{cta['password']}`\n👤 *Perfil:* {row['nombre']}\n📌 *PIN:* `{row['pin']}`\n📅 *Vence:* {row['fecha_vence']}\n\n"
                        "🚀 *¡Gracias por tu confianza Saúl Streaming!* 🎬"
                    )
                    url_entrega = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg_entrega)}"
                    c1.markdown(f'<a href="{url_entrega}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer; width:100%; font-weight:bold;">🚀 ENVIAR POR WHATSAPP</button></a>', unsafe_allow_html=True)
                    if c2.button("✂️ Cortar Servicio", key=f"cut_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=None, fecha_vence=None, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

# --- 4. NOTIFICACIONES ---
elif menu == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza WhatsApp")
    conn = get_db()
    plat_cobro = st.selectbox("🔍 Cobrar por Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    df_n = pd.read_sql_query(f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND plataforma='{plat_cobro}'", conn)
    if df_n.empty: st.success(f"No hay ventas en {plat_cobro}.")
    else:
        for _, r in df_n.iterrows():
            fv = datetime.strptime(r['fecha_vence'], "%d/%m/%Y")
            diff = (fv - datetime.now()).days
            col1, col2 = st.columns([3, 1])
            col1.write(f"⏰ Perfil: **{r['nombre']}** | Vence en: **{diff} días**")
            msg_cobro = f"👋 Hola *{r['nombre']}*, te saluda Saúl Streaming 🎬. Te recordamos que tu perfil de *{r['plataforma']}* vence el *{r['fecha_vence']}*. ¿Deseas renovar? ✨"
            url_cobro = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg_cobro)}"
            col2.markdown(f'<a href="{url_cobro}" target="_blank" style="text-decoration:none;"><button style="background-color:#008CBA; color:white; padding:5px; border:none; border-radius:5px; cursor:pointer; width:100%;">🔔 RECORDAR</button></a>', unsafe_allow_html=True)

# --- 5. FINANZAS PRO (LÓGICA REAL SOLICITADA) ---
elif menu == "💰 Finanzas Pro":
    st.title("💰 Reporte Financiero Saúl")
    conn = get_db()
    
    # Cálculos Totales
    egresos_totales = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    ingresos_totales = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    ganancia_total = ingresos_totales - egresos_totales

    st.markdown("### 📊 TOTALES GENERALES")
    tg1, tg2, tg3 = st.columns(3)
    tg1.metric("📉 Egresos Proveedores", f"S/ {egresos_totales:.2f}")
    tg2.metric("📈 Ingresos", f"S/ {ingresos_totales:.2f}")
    tg3.metric("🤑 Ganancias", f"S/ {ganancia_total:.2f}", delta_color="normal")
    
    st.divider()
    st.markdown("### 📊 DETALLE POR PLATAFORMA")
    plat_fin = st.selectbox("Selecciona Plataforma para ver detalle:", ["TODAS"] + list(PLATAFORMAS_CONFIG.keys()))
    
    data_list = []
    lista_recorrido = list(PLATAFORMAS_CONFIG.keys()) if plat_fin == "TODAS" else [plat_fin]
    
    for p in lista_recorrido:
        e_p = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}'", conn)['t'][0] or 0
        i_p = pd.read_sql_query(f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}'", conn)['t'][0] or 0
        g_p = i_p - e_p
        data_list.append({"PLATAFORMA": p, "Egresos (Cuentas)": f"S/ {e_p:.2f}", "Ingresos (Perfiles)": f"S/ {i_p:.2f}", "Ganancias": f"S/ {g_p:.2f}"})
    
    st.table(pd.DataFrame(data_list))

# --- 6. PROVEEDORES ---
elif menu == "📅 Proveedores":
    st.title("📅 Cuentas Activas")
    conn = get_db()
    df_p = pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas", conn)
    st.dataframe(df_p, use_container_width=True)