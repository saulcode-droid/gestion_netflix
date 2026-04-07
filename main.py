import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="STREAMING VIP MANAGER", page_icon="▶", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_v14.db'

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def hash_pass(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, user TEXT UNIQUE, password TEXT, rango TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas 
                      (id INTEGER PRIMARY KEY, tipo_negocio TEXT, plataforma TEXT, email TEXT UNIQUE, 
                       password TEXT, fecha_proveedor TEXT, costo REAL DEFAULT 0, creador_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS perfiles 
                      (id INTEGER PRIMARY KEY, email TEXT, plataforma TEXT, nombre TEXT, pin TEXT, 
                       estado TEXT DEFAULT 'LIBRE', whatsapp TEXT, fecha_vence TEXT, 
                       precio_venta REAL DEFAULT 0, creador_id INTEGER, fecha_venta TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN_GLOBAL')", (hash_pass('admin123'),))
    conn.commit()

init_db()

# --- ESTILOS CSS PREMIUM ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap');

* { font-family: 'Outfit', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

/* ─── FONDO GENERAL ─── */
.stApp {
    background: #070B14;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.15) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(16,185,129,0.08) 0%, transparent 50%);
    color: #E2E8F0;
}

/* ─── SIDEBAR ─── */
section[data-testid="stSidebar"] {
    background: #0D1117 !important;
    border-right: 1px solid #1E2A3B;
}
section[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section[data-testid="stSidebar"] .stRadio label {
    padding: 10px 14px;
    border-radius: 8px;
    transition: background 0.2s;
    display: block;
}
section[data-testid="stSidebar"] .stRadio label:hover { background: #1E2A3B; }

/* ─── TÍTULOS ─── */
.title-main {
    font-size: 2.4rem;
    font-weight: 900;
    background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
    margin-bottom: 0.2rem;
}
.subtitle {
    color: #64748B;
    font-size: 0.9rem;
    font-weight: 400;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* ─── TARJETAS MÉTRICAS ─── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0F1923 0%, #131E2E 100%);
    border: 1px solid #1E2A3B;
    border-radius: 16px;
    padding: 24px 20px !important;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
}
div[data-testid="stMetric"]:hover { border-color: #6366F1; }
div[data-testid="stMetric"]::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366F1, #10B981);
}
div[data-testid="stMetric"] label { color: #64748B !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 0.1em; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #F8FAFC !important; font-size: 2.2rem !important; font-weight: 700 !important; }

/* ─── BOTONES GLOBALES ─── */
.stButton > button {
    background: linear-gradient(135deg, #1E2A3B 0%, #0F1923 100%) !important;
    color: #E2E8F0 !important;
    border: 1px solid #2D3F56 !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.04em !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    border-color: #6366F1 !important;
    color: #FFFFFF !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.35) !important;
}
.stButton > button:active { transform: translateY(0px) !important; }

/* ─── BOTONES PLATAFORMA ─── */
.btn-netflix .stButton > button { border-color: #E50914 !important; color: #E50914 !important; }
.btn-netflix .stButton > button:hover { background: linear-gradient(135deg, #E50914, #B20000) !important; color: white !important; border-color: #E50914 !important; box-shadow: 0 6px 20px rgba(229,9,20,0.4) !important; }

.btn-max .stButton > button { border-color: #7B2CBF !important; color: #7B2CBF !important; }
.btn-max .stButton > button:hover { background: linear-gradient(135deg, #7B2CBF, #5A189A) !important; color: white !important; box-shadow: 0 6px 20px rgba(123,44,191,0.4) !important; }

.btn-prime .stButton > button { border-color: #00A8E1 !important; color: #00A8E1 !important; }
.btn-prime .stButton > button:hover { background: linear-gradient(135deg, #00A8E1, #0077B6) !important; color: white !important; box-shadow: 0 6px 20px rgba(0,168,225,0.4) !important; }

.btn-disney .stButton > button { border-color: #006E99 !important; color: #006E99 !important; }
.btn-disney .stButton > button:hover { background: linear-gradient(135deg, #006E99, #00405A) !important; color: white !important; box-shadow: 0 6px 20px rgba(0,110,153,0.4) !important; }

.btn-vix .stButton > button { border-color: #FF5A00 !important; color: #FF5A00 !important; }
.btn-vix .stButton > button:hover { background: linear-gradient(135deg, #FF5A00, #CC4800) !important; color: white !important; box-shadow: 0 6px 20px rgba(255,90,0,0.4) !important; }

.btn-crunchy .stButton > button { border-color: #F47521 !important; color: #F47521 !important; }
.btn-crunchy .stButton > button:hover { background: linear-gradient(135deg, #F47521, #C45C10) !important; color: white !important; box-shadow: 0 6px 20px rgba(244,117,33,0.4) !important; }

/* ─── BOTONES ACCIÓN ─── */
.btn-sell .stButton > button { background: linear-gradient(135deg, #10B981, #059669) !important; border-color: #10B981 !important; color: white !important; }
.btn-sell .stButton > button:hover { box-shadow: 0 6px 20px rgba(16,185,129,0.45) !important; transform: translateY(-2px) !important; }

.btn-renew .stButton > button { background: linear-gradient(135deg, #6366F1, #4F46E5) !important; border-color: #6366F1 !important; color: white !important; }
.btn-renew .stButton > button:hover { box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important; transform: translateY(-2px) !important; }

.btn-cut .stButton > button { background: linear-gradient(135deg, #EF4444, #DC2626) !important; border-color: #EF4444 !important; color: white !important; }
.btn-cut .stButton > button:hover { box-shadow: 0 6px 20px rgba(239,68,68,0.45) !important; transform: translateY(-2px) !important; }

/* ─── INPUTS ─── */
.stTextInput input, .stNumberInput input {
    background: #0D1117 !important;
    border: 1px solid #1E2A3B !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
    font-family: 'Outfit', sans-serif !important;
    padding: 10px 14px !important;
    transition: border-color 0.2s !important;
}
.stTextInput input:focus, .stNumberInput input:focus { border-color: #6366F1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important; }
.stSelectbox div[data-baseweb="select"] > div {
    background: #0D1117 !important;
    border: 1px solid #1E2A3B !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
}

/* ─── FORMULARIO ─── */
.stForm {
    background: linear-gradient(135deg, #0F1923, #0D1117) !important;
    border: 1px solid #1E2A3B !important;
    border-radius: 16px !important;
    padding: 24px !important;
}

/* ─── EXPANDER ─── */
.streamlit-expanderHeader {
    background: #0F1923 !important;
    border: 1px solid #1E2A3B !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: #080E18 !important;
    border: 1px solid #1E2A3B !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* ─── TARJETA PERFIL ─── */
.perfil-card {
    background: linear-gradient(135deg, #0F1923, #131E2E);
    border: 1px solid #1E2A3B;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 10px 0;
    display: flex;
    align-items: center;
    gap: 16px;
}
.badge-libre { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid #10B981; border-radius: 6px; padding: 3px 12px; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; }
.badge-vendido { background: rgba(239,68,68,0.15); color: #EF4444; border: 1px solid #EF4444; border-radius: 6px; padding: 3px 12px; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; }

/* ─── SEPARADOR ─── */
hr { border: none; border-top: 1px solid #1E2A3B; margin: 1.5rem 0; }

/* ─── CÓDIGO ─── */
.stCode { background: #0D1117 !important; border: 1px solid #1E2A3B; border-radius: 8px; font-family: 'JetBrains Mono', monospace; }

/* ─── LOGIN ─── */
.login-box {
    background: linear-gradient(145deg, #0D1117, #0F1923);
    border: 1px solid #1E2A3B;
    border-radius: 24px;
    padding: 48px 40px;
    box-shadow: 0 40px 80px rgba(0,0,0,0.6);
    position: relative;
    overflow: hidden;
}
.login-box::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6366F1, #10B981, #6366F1);
}
.login-logo {
    width: 72px; height: 72px;
    background: linear-gradient(135deg, #6366F1, #10B981);
    border-radius: 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem; margin: 0 auto 24px; text-align: center;
}
.login-title {
    font-size: 1.8rem; font-weight: 900;
    background: linear-gradient(135deg, #FFFFFF, #94A3B8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    text-align: center; margin-bottom: 4px;
}
.login-sub { color: #475569; font-size: 0.85rem; text-align: center; margin-bottom: 32px; letter-spacing: 0.08em; text-transform: uppercase; }

/* ─── SELECTOR DE MODO ─── */
.modo-card {
    background: linear-gradient(145deg, #0F1923, #131E2E);
    border: 2px solid #1E2A3B;
    border-radius: 20px;
    padding: 40px 30px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.modo-card:hover { border-color: #6366F1; box-shadow: 0 0 40px rgba(99,102,241,0.2); transform: translateY(-4px); }
.modo-card .icon { font-size: 3.5rem; margin-bottom: 16px; }
.modo-card h3 { color: #F8FAFC; font-weight: 800; font-size: 1.2rem; margin-bottom: 8px; }
.modo-card p { color: #64748B; font-size: 0.88rem; }

/* ─── PLATAFORMA HEADER ─── */
.plat-header {
    display: flex; align-items: center; gap: 16px;
    background: linear-gradient(135deg, #0F1923, #131E2E);
    border: 1px solid #1E2A3B; border-radius: 14px;
    padding: 18px 24px; margin-bottom: 20px;
}
.plat-dot { width: 14px; height: 14px; border-radius: 50%; }

/* ─── USUARIO BADGE SIDEBAR ─── */
.user-badge {
    background: linear-gradient(135deg, #1E2A3B, #0F1923);
    border: 1px solid #2D3F56; border-radius: 12px;
    padding: 16px; margin-bottom: 20px; text-align: center;
}
.user-avatar {
    width: 48px; height: 48px; border-radius: 12px;
    background: linear-gradient(135deg, #6366F1, #10B981);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; margin: 0 auto 10px;
}
.user-name { color: #F8FAFC; font-weight: 700; font-size: 1rem; }
.user-role { color: #64748B; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; }

/* ─── SEPARADOR DE SECCIÓN ─── */
.section-divider {
    border: none; height: 1px;
    background: linear-gradient(90deg, transparent, #1E2A3B, transparent);
    margin: 28px 0;
}

/* ─── DÍAS ALERTA ─── */
.dias-ok { color: #10B981; font-weight: 700; }
.dias-warn { color: #F59E0B; font-weight: 700; }
.dias-danger { color: #EF4444; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(valor): return f"S/ {valor:,.2f}"
def calcular_dias(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

PLATAFORMAS = {
    "NETFLIX":  {"color": "#E50914", "emoji": "🔴", "icon": "https://cdn.worldvectorlogo.com/logos/netflix-3.svg"},
    "MAX":      {"color": "#7B2CBF", "emoji": "🟣", "icon": "https://cdn-icons-png.flaticon.com/512/5602/5602732.png"},
    "PRIME":    {"color": "#00A8E1", "emoji": "🔵", "icon": "https://cdn-icons-png.flaticon.com/512/888/888845.png"},
    "DISNEY":   {"color": "#006E99", "emoji": "🏰", "icon": "https://cdn-icons-png.flaticon.com/512/732/732228.png"},
    "VIX":      {"color": "#FF5A00", "emoji": "🟠", "icon": "https://cdn-icons-png.flaticon.com/512/5602/5602732.png"},
    "CRUNCHY":  {"color": "#F47521", "emoji": "🍊", "icon": "https://cdn-icons-png.flaticon.com/512/5602/5602732.png"},
}
BTN_CLASS = {"NETFLIX":"btn-netflix","MAX":"btn-max","PRIME":"btn-prime","DISNEY":"btn-disney","VIX":"btn-vix","CRUNCHY":"btn-crunchy"}

# --- NAVEGACIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'modo' not in st.session_state: st.session_state['modo'] = None
if 'herramienta' not in st.session_state: st.session_state['herramienta'] = 'MENU'
if 'p_sel' not in st.session_state: st.session_state['p_sel'] = 'NETFLIX'

# ==========================================
# LOGIN
# ==========================================
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.1, 1])
    with col_log:
        st.markdown("""
        <div class='login-box'>
            <div class='login-logo'>▶</div>
            <div class='login-title'>STREAMING VIP</div>
            <div class='login-sub'>Sistema de Gestión Profesional</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        u = st.text_input("👤  USUARIO", placeholder="Tu usuario...", key="user_in")
        p = st.text_input("🔒  CONTRASEÑA", type="password", placeholder="••••••••", key="pass_in")
        st.write("")
        if st.button("🚀  INGRESAR AL SISTEMA", use_container_width=True):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p):
                st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'modo': None, 'herramienta': 'MENU'})
                st.rerun()
            else:
                st.error("❌  Credenciales incorrectas. Intenta de nuevo.")
        st.markdown("<div style='text-align:center; margin-top:16px; color:#475569; font-size:0.8rem;'>¿Olvidaste tu clave? Contacta a <b style='color:#6366F1'>Saúl</b></div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    rango_label = "ADMINISTRADOR" if st.session_state['u_ran'] == 'ADMIN_GLOBAL' else "OPERADOR"
    st.markdown(f"""
    <div class='user-badge'>
        <div class='user-avatar'>👤</div>
        <div class='user-name'>{st.session_state['u_nom'].upper()}</div>
        <div class='user-role'>{rango_label}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state['u_ran'] == 'ADMIN_GLOBAL':
        menu = st.radio("Navegar:", ["📊  Dashboard", "🌐  Plataformas", "📱  Gestión Perfiles", "🔔  Notificaciones", "💰  Finanzas", "🗑️  Eliminar", "👥  Usuarios", "🚪  Salir"], label_visibility="collapsed")
    else:
        menu = st.radio("Navegar:", ["📊  Dashboard", "🌐  Plataformas", "📱  Gestión Perfiles", "🔔  Notificaciones", "💰  Finanzas", "🔑  Cambiar Clave", "🚪  Salir"], label_visibility="collapsed")

    st.markdown("<hr style='border-top:1px solid #1E2A3B; margin:16px 0;'>", unsafe_allow_html=True)
    if st.session_state.get('modo'):
        modo_txt = "📱 Perfiles" if st.session_state['modo'] == 'PERFILES' else "📧 Cuentas"
        st.markdown(f"<div style='color:#64748B; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em;'>Modo activo</div><div style='color:#6366F1; font-weight:700; margin-bottom:12px;'>{modo_txt}</div>", unsafe_allow_html=True)
        if st.button("⇄  Cambiar modo", use_container_width=True):
            st.session_state['modo'] = None; st.rerun()

conn = get_db(); uid = st.session_state['u_id']

# ==========================================
# SELECTOR DE MODO
# ==========================================
if st.session_state['modo'] is None and "📱  Gestión Perfiles" not in menu:
    st.markdown("<div class='title-main'>SELECCIONA EL MODO</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>¿Cómo quieres trabajar hoy?</div>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        <div class='modo-card'>
            <div class='icon'>👤</div>
            <h3>VENTA POR PERFILES</h3>
            <p>Gestiona y vende perfiles individuales de cuentas compartidas.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("ENTRAR — PERFILES", use_container_width=True, key="m_per"):
            st.session_state['modo'] = "PERFILES"; st.rerun()
    with col2:
        st.markdown("""
        <div class='modo-card'>
            <div class='icon'>📧</div>
            <h3>CUENTAS COMPLETAS</h3>
            <p>Administra y entrega accesos completos de cuentas premium.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("ENTRAR — CUENTAS", use_container_width=True, key="m_cta"):
            st.session_state['modo'] = "CUENTAS"; st.rerun()
    st.stop()

elif st.session_state['modo'] is None:
    st.session_state['modo'] = "PERFILES"

# ==========================================
# DASHBOARD
# ==========================================
if "📊" in menu:
    st.markdown("<div class='title-main'>DASHBOARD</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Resumen general de tu negocio</div>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    total_cuentas = pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0]
    vendidos = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0]
    libres = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0]
    total_perfiles = vendidos + libres

    c1.metric("📦 Cuentas Maestras", total_cuentas)
    c2.metric("✅ Perfiles Vendidos", vendidos)
    c3.metric("🔓 Perfiles Libres", libres)
    c4.metric("📊 Total Perfiles", total_perfiles)

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("### Actividad reciente por plataforma")
    for plat, info in PLATAFORMAS.items():
        cnt = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE plataforma='{plat}' AND estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0]
        if cnt > 0:
            pct = int((cnt / vendidos * 100) if vendidos > 0 else 0)
            st.markdown(f"""
            <div style='display:flex; align-items:center; gap:16px; margin:10px 0;'>
                <span style='color:{info["color"]}; font-weight:800; width:90px;'>{info["emoji"]} {plat}</span>
                <div style='flex:1; background:#0D1117; border-radius:6px; height:8px; overflow:hidden;'>
                    <div style='width:{pct}%; height:8px; background:{info["color"]}; border-radius:6px;'></div>
                </div>
                <span style='color:#64748B; font-size:0.85rem; width:60px;'>{cnt} vendidos</span>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# GESTIÓN PERFILES
# ==========================================
elif "📱" in menu:
    st.markdown("<div class='title-main'>GESTIÓN DE PERFILES</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Selecciona una plataforma para administrar</div>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # Botones plataforma con colores
    cols = st.columns(6)
    plat_list = list(PLATAFORMAS.keys())
    for i, name in enumerate(plat_list):
        info = PLATAFORMAS[name]
        with cols[i]:
            st.markdown(f"<div class='{BTN_CLASS[name]}'>", unsafe_allow_html=True)
            if st.button(f"{info['emoji']} {name}", key=f"btn_{name}", use_container_width=True):
                st.session_state['p_sel'] = name
            st.markdown("</div>", unsafe_allow_html=True)

    p_sel = st.session_state.get('p_sel', 'NETFLIX')
    info_plat = PLATAFORMAS[p_sel]

    st.markdown(f"""
    <div class='plat-header'>
        <div class='plat-dot' style='background:{info_plat["color"]};'></div>
        <div>
            <span style='color:#F8FAFC; font-weight:800; font-size:1.1rem;'>{p_sel}</span>
            <span style='color:#64748B; font-size:0.85rem; margin-left:12px;'>Panel de administración</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    ctas = pd.read_sql_query(f"SELECT email, password FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)
    if ctas.empty:
        st.markdown("""
        <div style='text-align:center; padding:60px 20px; color:#475569;'>
            <div style='font-size:3rem; margin-bottom:16px;'>📭</div>
            <div style='font-weight:600; font-size:1.1rem;'>Sin cuentas registradas</div>
            <div style='font-size:0.9rem; margin-top:8px;'>Ve a Plataformas para agregar una cuenta maestra.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for _, c in ctas.iterrows():
            with st.expander(f"📧  {c['email']}"):
                st.markdown(f"<div style='font-family:JetBrains Mono,monospace; background:#0D1117; border:1px solid #1E2A3B; border-radius:8px; padding:12px 16px; color:#10B981; margin-bottom:16px;'>🔑 {c['password']}</div>", unsafe_allow_html=True)

                perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c['email']}' AND creador_id={uid}", conn)
                for _, row in perfs.iterrows():
                    estado_badge = f"<span class='badge-libre'>LIBRE</span>" if row['estado'] == 'LIBRE' else f"<span class='badge-vendido'>VENDIDO</span>"
                    st.markdown(f"""
                    <div class='perfil-card'>
                        {estado_badge}
                        <span style='color:#E2E8F0; font-weight:600;'>👤 {row['nombre']}</span>
                        <span style='color:#64748B; font-size:0.85rem;'>PIN: <span style='font-family:JetBrains Mono,monospace; color:#F59E0B;'>{row['pin']}</span></span>
                    </div>
                    """, unsafe_allow_html=True)

                    if row['estado'] == 'LIBRE':
                        c1_in, c2_in = st.columns([3, 1])
                        wa = c1_in.text_input("📱 WhatsApp del cliente", placeholder="Ej: 51987654321", key=f"wa_{row['id']}")
                        precio = c1_in.number_input("💵 Precio de venta S/", min_value=0.0, key=f"pv_{row['id']}")
                        with c2_in:
                            st.write("")
                            st.markdown("<div class='btn-sell'>", unsafe_allow_html=True)
                            if st.button("🛒 VENDER", key=f"v_{row['id']}", use_container_width=True):
                                if wa:
                                    v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                    cur = conn.cursor()
                                    cur.execute("UPDATE perfiles SET estado='VENDIDO', whatsapp=?, fecha_vence=?, precio_venta=?, fecha_venta=? WHERE id=?",
                                                (wa, v, precio, datetime.now().strftime("%d/%m/%Y"), row['id']))
                                    conn.commit(); st.rerun()
                                else:
                                    st.warning("Ingresa el WhatsApp del cliente")
                            st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        d = calcular_dias(row['fecha_vence'])
                        dias_class = "dias-ok" if d > 7 else ("dias-warn" if d > 3 else "dias-danger")
                        st.markdown(f"<div style='margin:8px 0;'>📅 Vence: <b>{row['fecha_vence']}</b> — <span class='{dias_class}'>{d} días restantes</span></div>", unsafe_allow_html=True)

                        cb1, cb2, cb3 = st.columns(3)
                        with cb1:
                            st.markdown("<div class='btn-renew'>", unsafe_allow_html=True)
                            if st.button("🔄  RENOVAR", key=f"r_{row['id']}", use_container_width=True):
                                try:
                                    nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                                except:
                                    nueva = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                conn.cursor().execute("UPDATE perfiles SET fecha_vence=? WHERE id=?", (nueva, row['id']))
                                conn.commit(); st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        with cb2:
                            st.markdown("<div class='btn-cut'>", unsafe_allow_html=True)
                            if st.button("✂️  CORTAR", key=f"c_{row['id']}", use_container_width=True):
                                conn.cursor().execute("UPDATE perfiles SET estado='LIBRE', whatsapp=NULL, precio_venta=0 WHERE id=?", (row['id'],))
                                conn.commit(); st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        with cb3:
                            wa_num = row['whatsapp'] if row['whatsapp'] else ''
                            msg = f"*🎬 ENTREGA {p_sel}*\n\n📧 Correo: {c['email']}\n🔑 Clave: {c['password']}\n👤 Perfil: {row['nombre']}\n🔢 PIN: {row['pin']}\n📅 Vence: {row['fecha_vence']}\n\n✅ ¡Gracias por tu compra!"
                            wa_link = f"https://wa.me/{wa_num}?text={urllib.parse.quote(msg)}"
                            st.markdown(f"""
                            <a href="{wa_link}" target="_blank" style="text-decoration:none;">
                                <div style="background:linear-gradient(135deg,#25D366,#128C7E); color:white; border-radius:10px;
                                    padding:10px; text-align:center; font-weight:700; font-size:0.88rem; letter-spacing:0.04em;
                                    cursor:pointer; transition:all 0.2s; box-shadow:0 4px 12px rgba(37,211,102,0.3);">
                                    💬  ENVIAR WA
                                </div>
                            </a>
                            """, unsafe_allow_html=True)

# ==========================================
# PLATAFORMAS — REGISTRO DE CUENTAS
# ==========================================
elif "🌐" in menu:
    st.markdown("<div class='title-main'>REGISTRO DE CUENTAS</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Agrega una cuenta maestra nueva</div>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    with st.form("reg_cuenta"):
        c1, c2 = st.columns(2)
        plat = c1.selectbox("🎬 Plataforma", list(PLATAFORMAS.keys()))
        mail = c2.text_input("📧 Correo electrónico")
        clv  = c1.text_input("🔑 Contraseña maestra")
        cst  = c2.number_input("💵 Costo S/", min_value=0.0, step=0.5)
        vnc  = c1.date_input("📅 Vencimiento proveedor")
        num_perfiles = c2.number_input("👤 Número de perfiles", min_value=1, max_value=10, value=5)

        st.markdown("<hr style='border-top:1px solid #1E2A3B; margin:12px 0;'>", unsafe_allow_html=True)
        st.markdown("**Configura los perfiles:**")
        perfiles_data = []
        pcols = st.columns(4)
        for i in range(int(num_perfiles)):
            pnombre = pcols[i % 4].text_input(f"Perfil {i+1}", placeholder=f"Nombre{i+1}", key=f"pn_{i}")
            ppin    = pcols[i % 4].text_input(f"PIN {i+1}", placeholder="0000", key=f"pp_{i}")
            perfiles_data.append((pnombre, ppin))

        if st.form_submit_button("🚀  ACTIVAR CUENTA MAESTRA", use_container_width=True):
            if mail and clv:
                try:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO cuentas (tipo_negocio, plataforma, email, password, fecha_proveedor, costo, creador_id) VALUES ('SOCIO VIP',?,?,?,?,?,?)",
                                (plat, mail, clv, vnc.strftime("%d/%m/%Y"), cst, uid))
                    for pnombre, ppin in perfiles_data:
                        if pnombre:
                            cur.execute("INSERT INTO perfiles (email, plataforma, nombre, pin, estado, creador_id) VALUES (?,?,?,?,'LIBRE',?)",
                                        (mail, plat, pnombre, ppin, uid))
                    conn.commit()
                    st.success(f"✅ Cuenta {mail} activada con {sum(1 for p,_ in perfiles_data if p)} perfiles.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("Completa correo y contraseña.")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("### Cuentas registradas")
    ctas_df = pd.read_sql_query(f"SELECT * FROM cuentas WHERE creador_id={uid} ORDER BY plataforma", conn)
    if not ctas_df.empty:
        for _, row in ctas_df.iterrows():
            info = PLATAFORMAS.get(row['plataforma'], {"color":"#6366F1","emoji":"▶"})
            st.markdown(f"""
            <div class='perfil-card' style='border-left:3px solid {info["color"]};'>
                <span style='font-size:1.5rem;'>{info["emoji"]}</span>
                <div style='flex:1;'>
                    <div style='color:#F8FAFC; font-weight:700;'>{row['email']}</div>
                    <div style='color:#64748B; font-size:0.82rem; margin-top:4px;'>
                        {row['plataforma']} · Vence: {row['fecha_proveedor']} · Costo: S/ {row['costo']:.2f}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No tienes cuentas registradas aún.")

# ==========================================
# FINANZAS
# ==========================================
elif "💰" in menu:
    st.markdown("<div class='title-main'>FINANZAS</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Análisis económico de tu operación</div>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    ingresos = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0] or 0
    costos   = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
    ganancia = ingresos - costos

    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Ingresos Totales", moneda(ingresos))
    c2.metric("📤 Costos Totales",   moneda(costos))
    c3.metric("💰 Ganancia Neta",    moneda(ganancia), delta=f"{((ganancia/costos*100) if costos > 0 else 0):.1f}%")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("### Detalle por plataforma")
    for plat, info in PLATAFORMAS.items():
        ing_plat = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE plataforma='{plat}' AND estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0] or 0
        cst_plat = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE plataforma='{plat}' AND creador_id={uid}", conn).iloc[0,0] or 0
        if ing_plat > 0 or cst_plat > 0:
            st.markdown(f"""
            <div class='perfil-card' style='border-left:3px solid {info["color"]};'>
                <span style='font-size:1.4rem;'>{info["emoji"]}</span>
                <div style='flex:1;'>
                    <span style='color:#F8FAFC; font-weight:700;'>{plat}</span>
                </div>
                <div style='text-align:right;'>
                    <div style='color:#10B981; font-weight:700;'>+{moneda(ing_plat)}</div>
                    <div style='color:#EF4444; font-size:0.82rem;'>-{moneda(cst_plat)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# NOTIFICACIONES
# ==========================================
elif "🔔" in menu:
    st.markdown("<div class='title-main'>NOTIFICACIONES</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Perfiles próximos a vencer</div>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    perfs = pd.read_sql_query(f"SELECT p.*, c.password as clave_maestra FROM perfiles p JOIN cuentas c ON p.email=c.email WHERE p.estado='VENDIDO' AND p.creador_id={uid}", conn)
    if perfs.empty:
        st.info("No hay perfiles vendidos activos.")
    else:
        urgentes = []
        for _, row in perfs.iterrows():
            d = calcular_dias(row['fecha_vence'])
            if d <= 7: urgentes.append((d, row))

        urgentes.sort(key=lambda x: x[0])

        if not urgentes:
            st.success("✅ Todos los perfiles están al día (más de 7 días)")
        else:
            for d, row in urgentes:
                info_p = PLATAFORMAS.get(row['plataforma'], {"color":"#6366F1","emoji":"▶"})
                alerta = "🔴" if d <= 2 else ("🟡" if d <= 5 else "🟢")
                st.markdown(f"""
                <div class='perfil-card' style='border-left:3px solid {"#EF4444" if d<=2 else ("#F59E0B" if d<=5 else "#10B981")};'>
                    <span style='font-size:1.4rem;'>{alerta}</span>
                    <div style='flex:1;'>
                        <div style='color:#F8FAFC; font-weight:700;'>{row["nombre"]} — {row["plataforma"]}</div>
                        <div style='color:#64748B; font-size:0.82rem;'>📧 {row["email"]} · 📱 {row["whatsapp"]}</div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='color:{"#EF4444" if d<=2 else ("#F59E0B" if d<=5 else "#10B981")}; font-weight:800; font-size:1.1rem;'>{d}d</div>
                        <div style='color:#64748B; font-size:0.78rem;'>{row["fecha_vence"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if row['whatsapp']:
                    msg = f"⚠️ *RENOVACIÓN {row['plataforma']}*\n\nHola! Tu perfil *{row['nombre']}* vence el {row['fecha_vence']}.\n¿Deseas renovar? 🎬"
                    wa_link = f"https://wa.me/{row['whatsapp']}?text={urllib.parse.quote(msg)}"
                    st.markdown(f"""
                    <a href="{wa_link}" target="_blank" style="text-decoration:none;">
                        <div style="background:linear-gradient(135deg,#25D366,#128C7E); color:white; border-radius:8px;
                            padding:8px 16px; text-align:center; font-weight:700; font-size:0.82rem; margin:0 0 12px; display:inline-block;">
                            💬 Avisar por WhatsApp
                        </div>
                    </a>
                    """, unsafe_allow_html=True)

# ==========================================
# USUARIOS GLOBALES (solo ADMIN)
# ==========================================
elif "👥" in menu and st.session_state['u_ran'] == 'ADMIN_GLOBAL':
    st.markdown("<div class='title-main'>USUARIOS DEL SISTEMA</div>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    with st.form("nuevo_user"):
        c1, c2, c3 = st.columns(3)
        nu = c1.text_input("Usuario")
        np = c2.text_input("Contraseña", type="password")
        nr = c3.selectbox("Rol", ["OPERADOR", "ADMIN_GLOBAL"])
        if st.form_submit_button("➕ CREAR USUARIO", use_container_width=True):
            if nu and np:
                try:
                    conn.cursor().execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", (nu, hash_pass(np), nr))
                    conn.commit(); st.success(f"Usuario {nu} creado.")
                except: st.error("Usuario ya existe.")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    users = pd.read_sql_query("SELECT id, user, rango FROM usuarios", conn)
    for _, row in users.iterrows():
        icono = "👑" if row['rango'] == 'ADMIN_GLOBAL' else "👤"
        st.markdown(f"""
        <div class='perfil-card'>
            <span style='font-size:1.4rem;'>{icono}</span>
            <div style='flex:1;'>
                <div style='color:#F8FAFC; font-weight:700;'>{row["user"]}</div>
                <div style='color:#64748B; font-size:0.82rem;'>{row["rango"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# ELIMINAR (solo ADMIN)
# ==========================================
elif "🗑️" in menu and st.session_state['u_ran'] == 'ADMIN_GLOBAL':
    st.markdown("<div class='title-main'>ELIMINAR DATOS</div>", unsafe_allow_html=True)
    st.markdown("<div style='background:rgba(239,68,68,0.1); border:1px solid #EF4444; border-radius:12px; padding:16px; margin-bottom:24px; color:#FCA5A5;'>⚠️ Zona peligrosa — esta acción no se puede deshacer.</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Eliminar cuenta maestra**")
        ctas_e = pd.read_sql_query(f"SELECT email FROM cuentas WHERE creador_id={uid}", conn)
        if not ctas_e.empty:
            mail_del = st.selectbox("Selecciona cuenta", ctas_e['email'].tolist(), key="del_mail")
            st.markdown("<div class='btn-cut'>", unsafe_allow_html=True)
            if st.button("🗑️ ELIMINAR CUENTA Y SUS PERFILES", use_container_width=True):
                conn.cursor().execute("DELETE FROM perfiles WHERE email=?", (mail_del,))
                conn.cursor().execute("DELETE FROM cuentas WHERE email=?", (mail_del,))
                conn.commit(); st.success("Cuenta eliminada."); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No hay cuentas para eliminar.")

# ==========================================
# CAMBIAR CLAVE
# ==========================================
elif "🔑" in menu:
    st.markdown("<div class='title-main'>CAMBIAR CONTRASEÑA</div>", unsafe_allow_html=True)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    with st.form("cambio_clave"):
        p_actual = st.text_input("Contraseña actual", type="password")
        p_nueva  = st.text_input("Nueva contraseña", type="password")
        p_conf   = st.text_input("Confirmar nueva contraseña", type="password")
        if st.form_submit_button("🔒 ACTUALIZAR CONTRASEÑA", use_container_width=True):
            cur = conn.cursor()
            cur.execute("SELECT password FROM usuarios WHERE id=?", (uid,))
            res = cur.fetchone()
            if res and res[0] == hash_pass(p_actual):
                if p_nueva == p_conf and len(p_nueva) >= 6:
                    cur.execute("UPDATE usuarios SET password=? WHERE id=?", (hash_pass(p_nueva), uid))
                    conn.commit(); st.success("✅ Contraseña actualizada correctamente.")
                else:
                    st.error("Las contraseñas no coinciden o son muy cortas (mín. 6 caracteres).")
            else:
                st.error("Contraseña actual incorrecta.")

# ==========================================
# SALIR
# ==========================================
elif "🚪" in menu:
    st.markdown("<div style='text-align:center; padding:80px 20px;'>", unsafe_allow_html=True)
    st.markdown("<div class='title-main' style='text-align:center;'>¿CERRAR SESIÓN?</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B; text-align:center; margin-bottom:32px;'>Tu sesión será terminada de forma segura.</p>", unsafe_allow_html=True)
    _, cc, _ = st.columns([2,1,2])
    with cc:
        if st.button("🚪  SÍ, SALIR", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)