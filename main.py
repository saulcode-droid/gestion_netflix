import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Saúl Streaming VIP V5.0", page_icon="🎬", layout="wide")

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
    # Asegurar estructura de tablas
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT UNIQUE, password TEXT, fecha_proveedor TEXT, costo REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, precio_venta REAL DEFAULT 0)''')
    conn.commit()

init_db()

# --- MENÚ LATERAL ---
st.sidebar.title("🎬 Saúl Streaming v5.0")
menu = st.sidebar.radio("Ir a:", ["📊 Dashboard", "🌐 PLATAFORMAS", "📱 Gestión de Perfiles", "🔔 Notificaciones", "📅 Proveedores", "💰 Finanzas Pro", "🗑️ Eliminar Cuentas"])

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

# --- 2. REGISTRO DE PLATAFORMAS ---
elif menu == "🌐 PLATAFORMAS":
    st.title("🌐 Registro de Plataformas")
    plat_sel = st.selectbox("Selecciona la Plataforma:", list(PLATAFORMAS_CONFIG.keys()))
    num_perfiles = PLATAFORMAS_CONFIG[plat_sel]
    
    with st.form("form_registro"):
        c_mail, c_pass, c_costo = st.columns([2, 2, 1])
        mail = c_mail.text_input("📧 Correo de cuenta:")
        pasw = c_pass.text_input("🔑 Contraseña:")
        costo_cta = c_costo.number_input("💵 Costo (S/):", min_value=0.0, step=1.0)
        f_prov = st.date_input("📅 Vence Proveedor:", format="DD/MM/YYYY")
        
        perfiles_lista = []
        st.write("---")
        cols = st.columns(2)
        for i in range(num_perfiles):
            with cols[0]: p_n = st.text_input(f"Nombre Perfil {i+1}", f"P{i+1}", key=f"n_{i}")
            with cols[1]: p_p = st.text_input(f"PIN {i+1}", "0000", key=f"p_{i}")
            perfiles_lista.append((p_n, p_p))
        
        if st.form_submit_button("🚀 GUARDAR CUENTA"):
            if mail and pasw:
                conn = get_db(); cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO cuentas (plataforma, email, password, fecha_proveedor, costo) VALUES (?,?,?,?,?)", 
                                   (plat_sel, mail, pasw, f_prov.strftime("%d/%m/%Y"), costo_cta))
                    for nom, pin in perfiles_lista:
                        cursor.execute("INSERT INTO perfiles (email, plataforma, nombre, pin) VALUES (?,?,?,?)", 
                                       (mail, plat_sel, nom, pin))
                    conn.commit(); st.success("✅ Guardado."); st.balloons()
                except: st.error("❌ El correo ya existe.")

# --- 3. GESTIÓN DE PERFILES (CORRECCIÓN DE ERROR SQL) ---
elif menu == "📱 Gestión de Perfiles":
    st.title("📱 Panel de Ventas y Entregas")
    conn = get_db()
    p_filtro = st.selectbox("🔍 Filtrar Plataforma:", ["TODAS"] + list(PLATAFORMAS_CONFIG.keys()))
    
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
                    pv = c2.number_input("💵 Precio Venta (S/):", min_value=0.0, value=5.0, key=f"pv_{row['id']}")
                    if st.button("🛒 Confirmar Venta", key=f"btn_v_{row['id']}"):
                        vence = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET estado='VENDIDO', whatsapp='{wa}', fecha_vence='{vence}', precio_venta={pv} WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                else:
                    c1.write(f"📅 **Vence:** {row['fecha_vence']}")
                    # FORMATO ELEGANTE ENTREGA
                    msg_entrega = (
                        f"💎 *ENTREGA DE CUENTA - {row['plataforma']}* 💎\n\n"
                        f"📧 *Correo:* `{sel_mail}`\n🔑 *Clave:* `{cta['password']}`\n👤 *Perfil:* {row['nombre']}\n📌 *PIN:* `{row['pin']}`\n📅 *Vence:* {row['fecha_vence']}\n\n"
                        "🚀 *¡Disfruta tu servicio con Saúl Streaming!* 🎬"
                    )
                    url_entrega = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg_entrega)}"
                    c1.markdown(f'<a href="{url_entrega}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer; width:100%; font-weight:bold;">🚀 ENVIAR POR WHATSAPP</button></a>', unsafe_allow_html=True)
                    
                    if c2.button("🔄 Renovar (+30d)", key=f"ren_{row['id']}"):
                        fv = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                        conn.cursor().execute(f"UPDATE perfiles SET fecha_vence='{fv}' WHERE id={row['id']}")
                        conn.commit(); st.rerun()
                    
                    # --- CORRECCIÓN DE ERROR AQUÍ (NULL en lugar de None) ---
                    if c2.button("✂️ Cortar Servicio", key=f"cut_{row['id']}"):
                        conn.cursor().execute(f"UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, fecha_vence=NULL, precio_venta=0 WHERE id={row['id']}")
                        conn.commit(); st.rerun()

# --- 4. NOTIFICACIONES ---
elif menu == "🔔 Notificaciones":
    st.title("🔔 Central de Cobranza")
    conn = get_db()
    plat_cobro = st.selectbox("🔍 Cobrar por Plataforma:", ["TODAS"] + list(PLATAFORMAS_CONFIG.keys()))
    q_noti = "SELECT * FROM perfiles WHERE estado='VENDIDO'"
    if plat_cobro != "TODAS": q_noti += f" AND plataforma='{plat_cobro}'"
    df_n = pd.read_sql_query(q_noti, conn)
    
    if df_n.empty: st.success("Sin pendientes.")
    else:
        for _, r in df_n.iterrows():
            fv = datetime.strptime(r['fecha_vence'], "%d/%m/%Y")
            diff = (fv - datetime.now()).days
            col1, col2 = st.columns([3, 1])
            col1.write(f"⏰ Perfil: **{r['nombre']}** ({r['plataforma']}) | Vence en: **{diff} días**")
            msg_cobro = f"👋 Hola *{r['nombre']}*, te saluda Saúl Streaming 🎬. Te recordamos que tu perfil de *{r['plataforma']}* vence el *{r['fecha_vence']}*. ¿Deseas renovar? ✨"
            url_cobro = f"https://wa.me/{r['whatsapp']}?text={urllib.parse.quote(msg_cobro)}"
            col2.markdown(f'<a href="{url_cobro}" target="_blank" style="text-decoration:none;"><button style="background-color:#008CBA; color:white; padding:5px; border:none; border-radius:5px; cursor:pointer; width:100%;">🔔 RECORDAR</button></a>', unsafe_allow_html=True)

# --- 5. FINANZAS ---
elif menu == "💰 Finanzas Pro":
    st.title("💰 Reporte Financiero Saúl")
    conn = get_db()
    egresos = pd.read_sql_query("SELECT SUM(costo) as t FROM cuentas", conn)['t'][0] or 0
    ingresos = pd.read_sql_query("SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO'", conn)['t'][0] or 0
    
    tg1, tg2, tg3 = st.columns(3)
    tg1.metric("📉 Egresos Proveedores", f"S/ {egresos:.2f}")
    tg2.metric("📈 Ingresos", f"S/ {ingresos:.2f}")
    tg3.metric("🤑 Ganancias", f"S/ {ingresos - egresos:.2f}")
    
    st.divider()
    st.subheader("📊 Detalle por Plataforma")
    data_list = []
    for p in PLATAFORMAS_CONFIG.keys():
        e_p = pd.read_sql_query(f"SELECT SUM(costo) as t FROM cuentas WHERE plataforma='{p}'", conn)['t'][0] or 0
        i_p = pd.read_sql_query(f"SELECT SUM(precio_venta) as t FROM perfiles WHERE estado='VENDIDO' AND plataforma='{p}'", conn)['t'][0] or 0
        data_list.append({"PLATAFORMA": p, "Egresos": f"S/ {e_p:.2f}", "Ingresos": f"S/ {i_p:.2f}", "Ganancia": f"S/ {i_p - e_p:.2f}"})
    st.table(pd.DataFrame(data_list))

# --- 6. NUEVO: ELIMINAR CUENTAS ---
elif menu == "🗑️ Eliminar Cuentas":
    st.title("🗑️ Eliminar Cuentas Caídas")
    st.warning("⚠️ Cuidado: Al eliminar una cuenta se borrarán todos sus perfiles asociados.")
    conn = get_db()
    df_del = pd.read_sql_query("SELECT id, plataforma, email FROM cuentas", conn)
    
    for _, r in df_del.iterrows():
        with st.container():
            c1, c2 = st.columns([4, 1])
            c1.write(f"📺 **{r['plataforma']}** | 📧 {r['email']}")
            if c2.button("🗑️ ELIMINAR", key=f"del_{r['id']}"):
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM cuentas WHERE id={r['id']}")
                cursor.execute(f"DELETE FROM perfiles WHERE email='{r['email']}'")
                conn.commit()
                st.rerun()
            st.divider()

elif menu == "📅 Proveedores":
    st.title("📅 Cuentas Activas")
    conn = get_db()
    df_p = pd.read_sql_query("SELECT plataforma, email, password, fecha_proveedor, costo FROM cuentas", conn)
    st.dataframe(df_p, use_container_width=True)