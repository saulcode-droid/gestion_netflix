import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming Pro V4.8", page_icon="💰", layout="wide")

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
    try: cursor.execute("ALTER TABLE cuentas ADD COLUMN costo REAL DEFAULT 0")
    except: pass
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT, costo REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT)''')
    conn.commit()

init_db()

# --- MENÚ LATERAL ---
st.sidebar.title("🎬 Saúl Streaming v4.8")
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
    df_clientes = pd.read_sql_query("SELECT plataforma, email, nombre, whatsapp, fecha_vence FROM perfiles WHERE estado='VENDIDO'", conn)
    st.dataframe(df_clientes, use_container_width=True)

# --- 2. PLATAFORMAS (CARGA EN 2 COLUMNAS) ---
elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Plataformas")
    plat_sel = st.selectbox("1. Selecciona la Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_perfiles = PLATAFORMAS_CONFIG[plat_sel]
    
    with st.form("form_registro_pro"):
        c_mail, c_pass, c_costo = st.columns([2, 2, 1])
        mail = c_mail.text_input("📧 Correo de cuenta:")
        pasw = c_pass.text_input("🔑 Contraseña:")
        costo = c_costo.number_input("💵 Costo Proveedor (S/):", min_value=0.0, step=0.5)
        f_prov = st.date_input("📅 Vencimiento con Proveedor:", format="DD/MM/YYYY")
        
        perfiles_lista = []
        st.write("---")
        st.write("📝 **Nombres y PINs de Perfiles (2 Columnas)**")
        
        # Generar perfiles en solo 2 columnas
        for i in range(num_perfiles):
            col_nom, col_pin = st.columns(2)
            with col_nom:
                p_n = st.text_input(f"Nombre Perfil {i+1}", f"P{i+1}", key=f"n_{i}")
            with col_pin:
                p_p = st.text_input(f"PIN Perfil {i+1}", "0000", key=f"p_{i}")
            perfiles_lista.append((p_n, p_p))
        
        if st.form_submit_button("🚀 GUARDAR PLATAFORMA"):
            if mail and pasw:
                conn = get_db(); cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", 
                                   (plat_sel, mail, pasw, f_prov.strftime("%d/%m/%Y"), costo))
                    for nom, pin in perfiles_lista:
                        cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", 
                                       (mail, plat_sel, nom, pin))
                    conn.commit()
                    st.success("✅ Plataforma activada correctamente."); st.balloons()
                except: st.error("❌ El correo ya existe o hubo un error.")

# --- 3. GESTIÓN DE PERFILES ---
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
            status = "🟢 LIBRE" if row['estado'] == 'LIBRE' else f"🔴 VENDIDO a {row['whatsapp']}"
            with st.expander(f"{row['nombre']} | PIN: {row['pin']} | {status}"):
                c1, c2 = st.columns(2)
                if row['estado'] == 'LIBRE':
                    wa = c1.text_input("📱 WhatsApp Cliente (ej: 51930...):", key=f"wa_{row['id']}")
                    if c1.button("🛒 Confirmar Venta", key=f"v_{row['id']}"):
                        vence = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{vence}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    c1.write(f"📅 **Vence:** {row['fecha_vence']}")
                    msg_entrega = (
                        f"💎 *ENTREGA DE CUENTA - {row['plataforma']}* 💎\n\n"
                        f"📧 *Correo:* `{sel_mail}`\n"
                        f"🔑 *Clave:* `{cta['password']}`\n"
                        f"👤 *Perfil:* {row['nombre']}\n"
                        f"📌 *PIN:* `{row['pin']}`\n"
                        f"📅 *Vence:* {row['fecha_vence']}\n\n"
                        "🚀 *¡Gracias por tu confianza Saúl Streaming!* 🎬"
                    )
                    url_entrega = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg_entrega)}"
                    c1.markdown(f'<a href="{url_entrega}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer; width:100%; font-weight:bold;">🚀 ENVIAR POR WHATSAPP</button></a>', unsafe_allow_html=True)
                    
                    if c2.button("🔄 Renovar (+30d)", key=f"ren_{row['id']}"):
                        fv = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{fv}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    if c2.button("✂️ Cortar Servicio", key=f"cut_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=None, fecha_vence=None WHERE id={row['id']}")
                        conn.commit(); st.rerun()

# --- 4. NOTIFICACIONES (FILTRADO POR PLATAFORMA) ---
elif menu == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza WhatsApp")
    conn = get_db()
    
    # Filtro dinámico por plataforma
    plat_cobro = st.selectbox("🔍 Cobrar por Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    
    df_n = pd.read_sql_query(f"SELECT * FROM perfiles WHERE estado='VENDIDO' AND plataforma='{plat_cobro}'", conn)
    
    if df_n.empty:
        st.success(f"No hay perfiles de {plat_cobro} por vencer pronto.")
    else:
        st.write(f"A continuación se muestran los clientes de **{plat_cobro}** ordenados por fecha de vencimiento:")
        for _, r in df_n.iterrows():
            fv = datetime.strptime(r['fecha_vence'], "%d/%m/%Y")
            diff = (fv - datetime.now()).days
            
            icon = "⏰" if diff <= 2 else "🗓️"
            with st.container():
                col1, col2 = st.columns([3, 1])
                col1.write(f"{icon} Perfil: *{r['nombre']}* | Vence en: **{diff} días** ({r['fecha_vence']})")
                
                msg_cobro = f"👋 Hola *{r['nombre']}*, te saluda Saúl Streaming 🎬. Te recordamos que tu perfil de *{r['plataforma']}* vence el *{r['fecha_vence']}*. ¿Deseas renovar para no perder tu acceso? ✨"
                url_cobro = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg_cobro)}"
                col2.markdown(f'<a href="{url_cobro}" target="_blank" style="text-decoration:none;"><button style="background-color:#008CBA; color:white; padding:5px; border:none; border-radius:5px; cursor:pointer; width:100%;">🔔 RECORDAR</button></a>', unsafe_allow_html=True)
                st.divider()

# --- 5. PROVEEDORES ---
elif menu == "📅 Proveedores":
    st.title("📅 Control de Inversión y Proveedores")
    conn = get_db()
    df_p = pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas", conn)
    st.dataframe(df_p, use_container_width=True)

# --- 6. FINANZAS PRO (POR PLATAFORMA + TOTALES) ---
elif menu == "💰 Finanzas Pro":
    st.title("💰 Reporte Financiero Saúl Pro")
    conn = get_db()
    
    # --- CUADRO LATERAL DE PRECIOS DE VENTA ---
    st.sidebar.markdown("### 💵 Configurar Precios de Venta")
    precios_venta = {}
    for plat in PLATAFORMAS_CONFIG.keys():
        precios_venta[plat] = st.sidebar.number_input(f"Venta promedio {plat} (S/):", value=10.0, step=0.5)
    
    # --- CÁLCULOS GENERALES ---
    costo_total_gen = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    
    # Calcular ingresos totales sumando los vendidos de cada plataforma por su precio
    ingresos_totales_gen = 0
    for plat, precio in precios_venta.items():
        vendidos_plat = pd.read_sql_query(f"SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{plat}'", conn)['t'][0]
        ingresos_totales_gen += (vendidos_plat * precio)
    
    ganancia_total_gen = ingresos_totales_gen - costo_total_gen

    # --- CUADRO DE TOTALES GENERALES ---
    st.markdown("## 📊 TOTALES GENERALES")
    tg1, tg2, tg3 = st.columns(3)
    tg1.metric("💸 Inversión Total (Proveedores)", f"S/ {costo_total_gen:.2f}")
    tg2.metric("📈 Ingresos Brutos Totales", f"S/ {ingresos_totales_gen:.2f}")
    
    # Color de la ganancia
    color_ganancia = "normal" if ganancia_total_gen >= 0 else "inverse"
    tg3.metric("🤑 Utilidad Neta Total", f"S/ {ganancia_total_gen:.2f}", delta_color=color_ganancia)
    
    st.divider()
    
    # --- DETALLE POR PLATAFORMA ---
    st.markdown("## 📊 DETALLE POR PLATAFORMA")
    
    data_finanzas = []
    for plat, precio_v in precios_venta.items():
        # Costo (Egresos) de esta plataforma
        costo_plat = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{plat}'", conn)['t'][0] or 0
        # Perfiles Vendidos
        vendidos_plat = pd.read_sql_query(f"SELECT COUNT(*) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{plat}'", conn)['t'][0]
        # Ingresos Brutos
        ingresos_plat = vendidos_plat * precio_v
        # Utilidad
        utilidad_plat = ingresos_plat - costo_plat
        
        data_finanzas.append({
            "PLATAFORMA": plat,
            "Costo (Egresos)": f"S/ {costo_plat:.2f}",
            "Vendidos": vendidos_plat,
            "Precio Venta": f"S/ {precio_v:.2f}",
            "Ingresos Brutos": f"S/ {ingresos_plat:.2f}",
            "Utilidad Neta": f"S/ {utilidad_plat:.2f}"
        })
    
    df_finanzas = pd.DataFrame(data_finanzas)
    st.dataframe(df_finanzas, use_container_width=True, hide_index=True)