import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="STREAMING VIP", page_icon="▶", layout="wide")

# --- BASE DE DATOS ---
DB_NAME = 'db_streaming_v15.db'

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
    cursor.execute('''CREATE TABLE IF NOT EXISTS cuentas_completas
                      (id INTEGER PRIMARY KEY, plataforma TEXT, email TEXT, password TEXT,
                       whatsapp TEXT, fecha_vence TEXT, precio_venta REAL DEFAULT 0,
                       costo REAL DEFAULT 0, estado TEXT DEFAULT 'DISPONIBLE',
                       creador_id INTEGER, fecha_venta TEXT, fecha_proveedor TEXT)''')
    cursor.execute("INSERT OR IGNORE INTO usuarios (user, password, rango) VALUES ('admin', ?, 'ADMIN_GLOBAL')", (hash_pass('admin123'),))
    conn.commit()

init_db()

# --- ESTILOS CSS PREMIUM ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

* { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

/* ── FONDO ── */
.stApp {
    background: #060810;
    background-image:
        radial-gradient(ellipse 120% 60% at 10% 0%, rgba(88,28,255,0.12) 0%, transparent 55%),
        radial-gradient(ellipse 80% 50% at 90% 100%, rgba(0,224,168,0.07) 0%, transparent 50%),
        url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.015'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    color: #E2E8F0;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #09090F !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] * { color: #94A3B8 !important; }
section[data-testid="stSidebar"] .stRadio > div { gap: 4px; }
section[data-testid="stSidebar"] .stRadio label {
    padding: 11px 16px !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
    display: block !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.01em !important;
    border: 1px solid transparent !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(99,102,241,0.1) !important;
    border-color: rgba(99,102,241,0.2) !important;
    color: #C4B5FD !important;
}

/* ── TIPOGRAFIA ── */
.title-main {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FFFFFF 20%, #7C3AED 80%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.subtitle {
    color: #475569;
    font-size: 0.82rem;
    font-weight: 400;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 4px;
    margin-bottom: 1.8rem;
}

/* ── METRICAS ── */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #0D0F1A 0%, #111320 100%) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 18px !important;
    padding: 22px 20px !important;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease !important;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(99,102,241,0.3) !important;
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(99,102,241,0.12) !important;
}
div[data-testid="stMetric"]::after {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #7C3AED, #06B6D4, #10B981);
    opacity: 0.6;
}
div[data-testid="stMetric"] label { 
    color: #475569 !important; font-size: 0.75rem !important; 
    text-transform: uppercase; letter-spacing: 0.12em; font-weight: 500 !important; 
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] { 
    color: #F1F5F9 !important; font-size: 2rem !important; 
    font-weight: 700 !important; font-family: 'Syne', sans-serif !important; 
}

/* ── BOTONES BASE ── */
.stButton > button {
    background: linear-gradient(145deg, #13172A 0%, #0D1020 100%) !important;
    color: #CBD5E1 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05) !important;
}
.stButton > button:hover {
    background: linear-gradient(145deg, #1E1B4B 0%, #312E81 100%) !important;
    border-color: rgba(99,102,241,0.4) !important;
    color: #E0E7FF !important;
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.25), inset 0 1px 0 rgba(255,255,255,0.1) !important;
}
.stButton > button:active { transform: translateY(0) scale(0.99) !important; }

/* ── BOTONES PLATAFORMA ── */
.plat-btn-NETFLIX .stButton > button { color: #FF6B7A !important; border-color: rgba(229,9,20,0.25) !important; }
.plat-btn-NETFLIX .stButton > button:hover { background: linear-gradient(145deg, #4A0909, #7B0D0D) !important; color: #FCA5A5 !important; border-color: #E50914 !important; box-shadow: 0 8px 24px rgba(229,9,20,0.3) !important; }
.plat-btn-MAX .stButton > button { color: #C084FC !important; border-color: rgba(123,44,191,0.25) !important; }
.plat-btn-MAX .stButton > button:hover { background: linear-gradient(145deg, #2E1065, #4C1D95) !important; color: #E9D5FF !important; border-color: #7B2CBF !important; box-shadow: 0 8px 24px rgba(123,44,191,0.3) !important; }
.plat-btn-PRIME .stButton > button { color: #67E8F9 !important; border-color: rgba(0,168,225,0.25) !important; }
.plat-btn-PRIME .stButton > button:hover { background: linear-gradient(145deg, #0C2436, #0E3D5C) !important; color: #A5F3FC !important; border-color: #00A8E1 !important; box-shadow: 0 8px 24px rgba(0,168,225,0.3) !important; }
.plat-btn-DISNEY .stButton > button { color: #7DD3FC !important; border-color: rgba(0,110,153,0.25) !important; }
.plat-btn-DISNEY .stButton > button:hover { background: linear-gradient(145deg, #082030, #0A3347) !important; color: #BAE6FD !important; border-color: #006E99 !important; box-shadow: 0 8px 24px rgba(0,110,153,0.3) !important; }
.plat-btn-VIX .stButton > button { color: #FB923C !important; border-color: rgba(255,90,0,0.25) !important; }
.plat-btn-VIX .stButton > button:hover { background: linear-gradient(145deg, #431407, #7C2D12) !important; color: #FED7AA !important; border-color: #FF5A00 !important; box-shadow: 0 8px 24px rgba(255,90,0,0.3) !important; }
.plat-btn-CRUNCHY .stButton > button { color: #FDA663 !important; border-color: rgba(244,117,33,0.25) !important; }
.plat-btn-CRUNCHY .stButton > button:hover { background: linear-gradient(145deg, #3D1A02, #7B3202) !important; color: #FDE68A !important; border-color: #F47521 !important; box-shadow: 0 8px 24px rgba(244,117,33,0.3) !important; }

/* ── BOTONES PLATAFORMA ACTIVOS ── */
.plat-active-NETFLIX .stButton > button { background: linear-gradient(145deg, #4A0909, #7B0D0D) !important; color: #FCA5A5 !important; border-color: #E50914 !important; box-shadow: 0 4px 16px rgba(229,9,20,0.3) !important; }
.plat-active-MAX .stButton > button { background: linear-gradient(145deg, #2E1065, #4C1D95) !important; color: #E9D5FF !important; border-color: #7B2CBF !important; box-shadow: 0 4px 16px rgba(123,44,191,0.3) !important; }
.plat-active-PRIME .stButton > button { background: linear-gradient(145deg, #0C2436, #0E3D5C) !important; color: #A5F3FC !important; border-color: #00A8E1 !important; box-shadow: 0 4px 16px rgba(0,168,225,0.3) !important; }
.plat-active-DISNEY .stButton > button { background: linear-gradient(145deg, #082030, #0A3347) !important; color: #BAE6FD !important; border-color: #006E99 !important; box-shadow: 0 4px 16px rgba(0,110,153,0.3) !important; }
.plat-active-VIX .stButton > button { background: linear-gradient(145deg, #431407, #7C2D12) !important; color: #FED7AA !important; border-color: #FF5A00 !important; box-shadow: 0 4px 16px rgba(255,90,0,0.3) !important; }
.plat-active-CRUNCHY .stButton > button { background: linear-gradient(145deg, #3D1A02, #7B3202) !important; color: #FDE68A !important; border-color: #F47521 !important; box-shadow: 0 4px 16px rgba(244,117,33,0.3) !important; }

/* ── BOTONES ACCION ── */
.btn-sell .stButton > button { background: linear-gradient(135deg, #065F46, #047857) !important; border-color: rgba(16,185,129,0.4) !important; color: #6EE7B7 !important; }
.btn-sell .stButton > button:hover { background: linear-gradient(135deg, #047857, #059669) !important; box-shadow: 0 8px 24px rgba(16,185,129,0.35) !important; color: #D1FAE5 !important; transform: translateY(-2px) scale(1.01) !important; }
.btn-renew .stButton > button { background: linear-gradient(135deg, #1E1B4B, #2E2970) !important; border-color: rgba(99,102,241,0.4) !important; color: #A5B4FC !important; }
.btn-renew .stButton > button:hover { background: linear-gradient(135deg, #3730A3, #4338CA) !important; box-shadow: 0 8px 24px rgba(99,102,241,0.35) !important; color: #E0E7FF !important; transform: translateY(-2px) scale(1.01) !important; }
.btn-cut .stButton > button { background: linear-gradient(135deg, #450A0A, #7F1D1D) !important; border-color: rgba(239,68,68,0.35) !important; color: #FCA5A5 !important; }
.btn-cut .stButton > button:hover { background: linear-gradient(135deg, #991B1B, #DC2626) !important; box-shadow: 0 8px 24px rgba(239,68,68,0.35) !important; color: #FEE2E2 !important; transform: translateY(-2px) scale(1.01) !important; }
.btn-edit .stButton > button { background: linear-gradient(135deg, #1C1917, #292524) !important; border-color: rgba(251,191,36,0.3) !important; color: #FCD34D !important; }
.btn-edit .stButton > button:hover { background: linear-gradient(135deg, #78350F, #92400E) !important; box-shadow: 0 8px 24px rgba(251,191,36,0.3) !important; color: #FEF08A !important; transform: translateY(-2px) scale(1.01) !important; }
.btn-danger .stButton > button { background: linear-gradient(135deg, #450A0A, #7F1D1D) !important; border-color: rgba(239,68,68,0.35) !important; color: #FCA5A5 !important; }
.btn-danger .stButton > button:hover { background: linear-gradient(135deg, #DC2626, #EF4444) !important; box-shadow: 0 8px 24px rgba(239,68,68,0.4) !important; color: white !important; transform: translateY(-2px) scale(1.02) !important; }

/* ── INPUTS ── */
.stTextInput input, .stNumberInput input, .stDateInput input {
    background: #0D0F1A !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #E2E8F0 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 10px 14px !important;
    transition: all 0.2s ease !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12), inset 0 2px 4px rgba(0,0,0,0.3) !important;
}
.stSelectbox div[data-baseweb="select"] > div {
    background: #0D0F1A !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #E2E8F0 !important;
}
label { color: #64748B !important; font-size: 0.8rem !important; font-weight: 500 !important; letter-spacing: 0.06em !important; }

/* ── FORM ── */
.stForm {
    background: linear-gradient(145deg, #0D0F1A, #0A0C15) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 20px !important;
    padding: 28px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4) !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: linear-gradient(145deg, #0D0F1A, #111320) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
    color: #CBD5E1 !important;
    font-weight: 600 !important;
}
.streamlit-expanderHeader:hover { border-color: rgba(99,102,241,0.3) !important; }
.streamlit-expanderContent {
    background: #080A12 !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-top: none !important;
    border-radius: 0 0 14px 14px !important;
    padding: 16px !important;
}

/* ── TARJETAS ── */
.card {
    background: linear-gradient(145deg, #0D0F1A, #111320);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 18px 22px;
    margin: 8px 0;
    transition: all 0.25s ease;
}
.card:hover { border-color: rgba(99,102,241,0.2); transform: translateX(2px); }

.badge { display: inline-flex; align-items: center; gap: 5px; border-radius: 8px; padding: 4px 12px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; }
.badge-libre { background: rgba(16,185,129,0.12); color: #34D399; border: 1px solid rgba(16,185,129,0.25); }
.badge-vendido { background: rgba(239,68,68,0.12); color: #F87171; border: 1px solid rgba(239,68,68,0.25); }
.badge-disponible { background: rgba(16,185,129,0.12); color: #34D399; border: 1px solid rgba(16,185,129,0.25); }
.badge-entregado { background: rgba(239,68,68,0.12); color: #F87171; border: 1px solid rgba(239,68,68,0.25); }

/* ── LOGIN ── */
.login-wrap {
    background: linear-gradient(145deg, #0C0E1A, #0A0C17);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 28px;
    padding: 52px 44px;
    box-shadow: 0 50px 100px rgba(0,0,0,0.7);
    position: relative; overflow: hidden;
}
.login-wrap::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, #7C3AED, #06B6D4, transparent);
}
.login-logo {
    width: 80px; height: 80px;
    background: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);
    border-radius: 24px;
    display: flex; align-items: center; justify-content: center;
    font-size: 2.2rem; margin: 0 auto 28px; text-align: center;
    box-shadow: 0 16px 40px rgba(124,58,237,0.4);
}
.login-title { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF, #7C3AED); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 4px; }
.login-sub { color: #374151; font-size: 0.78rem; text-align: center; margin-bottom: 36px; letter-spacing: 0.15em; text-transform: uppercase; }

/* ── USER BADGE ── */
.user-badge {
    background: linear-gradient(145deg, #0D0F1A, #111320);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 18px 16px; margin-bottom: 24px; text-align: center;
}
.user-avatar {
    width: 52px; height: 52px; border-radius: 16px;
    background: linear-gradient(135deg, #7C3AED, #06B6D4);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; margin: 0 auto 10px;
    box-shadow: 0 8px 20px rgba(124,58,237,0.35);
}
.user-name { color: #F1F5F9 !important; font-weight: 700; font-size: 0.95rem; font-family: 'Syne', sans-serif; }
.user-role { display: inline-block; margin-top: 6px; color: #7C3AED !important; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.15em; background: rgba(124,58,237,0.1); border: 1px solid rgba(124,58,237,0.2); border-radius: 6px; padding: 3px 10px; }

/* ── MODO CARDS ── */
.modo-card {
    background: linear-gradient(145deg, #0D0F1A, #111320);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 24px; padding: 44px 32px; text-align: center;
    transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.modo-card:hover { border-color: rgba(99,102,241,0.3); transform: translateY(-6px); box-shadow: 0 24px 60px rgba(99,102,241,0.15); }
.modo-icon { font-size: 3.2rem; margin-bottom: 18px; }
.modo-title { font-family: 'Syne', sans-serif; color: #F1F5F9; font-weight: 800; font-size: 1.15rem; margin-bottom: 10px; }
.modo-desc { color: #475569; font-size: 0.85rem; line-height: 1.6; }

/* ── PLAT HEADER ── */
.plat-header {
    display: flex; align-items: center; gap: 16px;
    background: linear-gradient(145deg, #0D0F1A, #111320);
    border: 1px solid rgba(255,255,255,0.07); border-radius: 16px;
    padding: 16px 22px; margin-bottom: 24px;
}
.plat-dot { width: 12px; height: 12px; border-radius: 50%; }

/* ── SEPARADORES ── */
.divider { border: none; border-top: 1px solid rgba(255,255,255,0.05); margin: 24px 0; }
.glow-divider { border: none; height: 1px; margin: 28px 0; background: linear-gradient(90deg, transparent, rgba(99,102,241,0.3), rgba(6,182,212,0.3), transparent); }

/* ── KEY BOX ── */
.key-box { background: #080A12; border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 10px 16px; color: #34D399; font-family: 'DM Mono', monospace; font-size: 0.88rem; margin-bottom: 14px; }

/* ── DIAS ALERTA ── */
.d-ok { color: #34D399; font-weight: 700; }
.d-warn { color: #FBBF24; font-weight: 700; }
.d-danger { color: #F87171; font-weight: 700; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #060810; }
::-webkit-scrollbar-thumb { background: #1E1B4B; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- UTILIDADES ---
def moneda(v): return f"S/ {v:,.2f}"

def calcular_dias(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%d/%m/%Y")
        return (f - datetime.now()).days + 1
    except: return 0

def dias_html(d):
    cls = "d-ok" if d > 7 else ("d-warn" if d > 3 else "d-danger")
    icon = "✅" if d > 7 else ("⚠️" if d > 3 else "🔴")
    return f"<span class='{cls}'>{icon} {d} días</span>"

PLATAFORMAS = {
    "NETFLIX":  {"color": "#E50914", "emoji": "🔴"},
    "MAX":      {"color": "#7B2CBF", "emoji": "🟣"},
    "PRIME":    {"color": "#00A8E1", "emoji": "🔵"},
    "DISNEY":   {"color": "#006E99", "emoji": "🏰"},
    "VIX":      {"color": "#FF5A00", "emoji": "🟠"},
    "CRUNCHY":  {"color": "#F47521", "emoji": "🍊"},
}

# --- SESSION STATE ---
for k, v in [('auth', False), ('modo', None), ('p_sel', 'NETFLIX'), ('edit_perfil_id', None)]:
    if k not in st.session_state: st.session_state[k] = v

conn = get_db()

# ══════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════
if not st.session_state['auth']:
    _, col_log, _ = st.columns([1, 1.2, 1])
    with col_log:
        st.markdown("""
        <div class='login-wrap'>
            <div class='login-logo'>▶</div>
            <div class='login-title'>STREAMING VIP</div>
            <div class='login-sub'>Sistema de Gestión Profesional</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        u = st.text_input("USUARIO", placeholder="Ingresa tu usuario...", key="u_in")
        p = st.text_input("CONTRASEÑA", type="password", placeholder="••••••••", key="p_in")
        st.write("")
        if st.button("▶  INGRESAR AL SISTEMA", use_container_width=True):
            cursor = conn.cursor()
            cursor.execute("SELECT id, rango, password FROM usuarios WHERE user=?", (u,))
            res = cursor.fetchone()
            if res and res[2] == hash_pass(p):
                st.session_state.update({'auth': True, 'u_id': res[0], 'u_nom': u, 'u_ran': res[1], 'modo': None})
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
        st.markdown("<div style='text-align:center;margin-top:20px;color:#374151;font-size:0.78rem;'>¿Problemas? Contacta a <b style='color:#7C3AED'>Saúl</b></div>", unsafe_allow_html=True)
    st.stop()

uid = st.session_state['u_id']

# ══════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════
with st.sidebar:
    rango_label = "ADMINISTRADOR" if st.session_state['u_ran'] == 'ADMIN_GLOBAL' else "OPERADOR"
    st.markdown(f"""
    <div class='user-badge'>
        <div class='user-avatar'>👤</div>
        <div class='user-name'>{st.session_state['u_nom'].upper()}</div>
        <div class='user-role'>{rango_label}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('modo'):
        modo_txt = "👤 Perfiles" if st.session_state['modo'] == 'PERFILES' else "📧 Cuentas Completas"
        st.markdown(f"""
        <div style='background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:12px 14px;margin-bottom:12px;'>
            <div style='color:#6366F1;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;'>Modo activo</div>
            <div style='color:#A5B4FC;font-weight:700;font-size:0.9rem;'>{modo_txt}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⇄  Cambiar modo", use_container_width=True):
            st.session_state['modo'] = None; st.rerun()
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    if st.session_state['u_ran'] == 'ADMIN_GLOBAL':
        menu = st.radio("", ["📊  Dashboard", "🌐  Plataformas", "📱  Gestión", "🔔  Alertas", "💰  Finanzas", "🗑️  Eliminar", "👥  Usuarios", "🚪  Salir"], label_visibility="collapsed")
    else:
        menu = st.radio("", ["📊  Dashboard", "🌐  Plataformas", "📱  Gestión", "🔔  Alertas", "💰  Finanzas", "🔑  Mi Clave", "🚪  Salir"], label_visibility="collapsed")

# ══════════════════════════════════════════
# SELECTOR DE MODO
# ══════════════════════════════════════════
if st.session_state['modo'] is None and "📱" not in menu:
    st.markdown("<div class='title-main'>BIENVENIDO</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Elige cómo trabajar hoy</div>", unsafe_allow_html=True)
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        <div class='modo-card'>
            <div class='modo-icon'>👤</div>
            <div class='modo-title'>VENTA POR PERFILES</div>
            <div class='modo-desc'>Gestiona perfiles individuales de cuentas compartidas. Vende, renueva y envía credenciales.</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("ENTRAR — PERFILES", use_container_width=True, key="m_per"):
            st.session_state['modo'] = "PERFILES"; st.rerun()
    with col2:
        st.markdown("""
        <div class='modo-card'>
            <div class='modo-icon'>📧</div>
            <div class='modo-title'>CUENTAS COMPLETAS</div>
            <div class='modo-desc'>Entrega acceso completo a cuentas premium. Gestiona correo y contraseña por cliente.</div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("ENTRAR — CUENTAS", use_container_width=True, key="m_cta"):
            st.session_state['modo'] = "CUENTAS"; st.rerun()
    st.stop()
elif st.session_state['modo'] is None and "📱" in menu:
    st.session_state['modo'] = "PERFILES"

# ══════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════
if "📊" in menu:
    st.markdown("<div class='title-main'>DASHBOARD</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Resumen general del negocio</div>", unsafe_allow_html=True)
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    modo = st.session_state.get('modo', 'PERFILES')

    if modo == 'PERFILES':
        total_cuentas = pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0]
        vendidos = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0]
        libres = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='LIBRE' AND creador_id={uid}", conn).iloc[0,0]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("📦 Cuentas Maestras", total_cuentas)
        c2.metric("✅ Perfiles Vendidos", vendidos)
        c3.metric("🔓 Perfiles Libres", libres)
        c4.metric("📊 Total Perfiles", vendidos + libres)
    else:
        total = pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas_completas WHERE creador_id={uid}", conn).iloc[0,0]
        entregadas = pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas_completas WHERE estado='ENTREGADA' AND creador_id={uid}", conn).iloc[0,0]
        disponibles = pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas_completas WHERE estado='DISPONIBLE' AND creador_id={uid}", conn).iloc[0,0]
        c1,c2,c3 = st.columns(3)
        c1.metric("📦 Cuentas Totales", total)
        c2.metric("✅ Entregadas", entregadas)
        c3.metric("🔓 Disponibles", disponibles)

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    st.markdown("### Actividad por plataforma")
    if modo == 'PERFILES':
        vt = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0]
        for plat, info in PLATAFORMAS.items():
            cnt = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE plataforma='{plat}' AND estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0]
            if cnt > 0:
                pct = int((cnt / vt * 100) if vt > 0 else 0)
                st.markdown(f"""<div style='display:flex;align-items:center;gap:16px;margin:12px 0;'>
                    <span style='color:{info["color"]};font-weight:700;width:96px;font-family:Syne,sans-serif;'>{info["emoji"]} {plat}</span>
                    <div style='flex:1;background:#0D0F1A;border-radius:8px;height:6px;overflow:hidden;'>
                        <div style='width:{pct}%;height:6px;background:linear-gradient(90deg,{info["color"]}88,{info["color"]});border-radius:8px;'></div>
                    </div>
                    <span style='color:#475569;font-size:0.82rem;width:80px;text-align:right;'>{cnt} vendidos</span>
                </div>""", unsafe_allow_html=True)
    else:
        et = pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas_completas WHERE estado='ENTREGADA' AND creador_id={uid}", conn).iloc[0,0]
        for plat, info in PLATAFORMAS.items():
            cnt = pd.read_sql_query(f"SELECT COUNT(*) FROM cuentas_completas WHERE plataforma='{plat}' AND estado='ENTREGADA' AND creador_id={uid}", conn).iloc[0,0]
            if cnt > 0:
                pct = int((cnt / et * 100) if et > 0 else 0)
                st.markdown(f"""<div style='display:flex;align-items:center;gap:16px;margin:12px 0;'>
                    <span style='color:{info["color"]};font-weight:700;width:96px;font-family:Syne,sans-serif;'>{info["emoji"]} {plat}</span>
                    <div style='flex:1;background:#0D0F1A;border-radius:8px;height:6px;overflow:hidden;'>
                        <div style='width:{pct}%;height:6px;background:linear-gradient(90deg,{info["color"]}88,{info["color"]});border-radius:8px;'></div>
                    </div>
                    <span style='color:#475569;font-size:0.82rem;width:80px;text-align:right;'>{cnt} entregadas</span>
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# PLATAFORMAS — REGISTRO
# ══════════════════════════════════════════
elif "🌐" in menu:
    modo = st.session_state.get('modo', 'PERFILES')

    if modo == 'PERFILES':
        st.markdown("<div class='title-main'>REGISTRO DE CUENTAS</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle'>Agregar cuenta maestra con perfiles</div>", unsafe_allow_html=True)
        st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

        with st.form("reg_cuenta_perfiles"):
            c1, c2 = st.columns(2)
            plat = c1.selectbox("🎬 PLATAFORMA", list(PLATAFORMAS.keys()))
            mail = c2.text_input("📧 CORREO ELECTRÓNICO")
            clv  = c1.text_input("🔑 CONTRASEÑA MAESTRA")
            cst  = c2.number_input("💵 COSTO (S/)", min_value=0.0, step=0.5)
            vnc  = c1.date_input("📅 VENCIMIENTO PROVEEDOR")
            num_p = c2.number_input("👤 NÚMERO DE PERFILES", min_value=1, max_value=10, value=5)
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown("<div style='color:#94A3B8;font-weight:600;font-size:0.88rem;letter-spacing:0.06em;margin-bottom:12px;'>⚙️ CONFIGURAR PERFILES</div>", unsafe_allow_html=True)
            perfiles_data = []
            pcols = st.columns(min(int(num_p), 5))
            for i in range(int(num_p)):
                pnombre = pcols[i % 5].text_input(f"Perfil {i+1}", placeholder=f"Nombre{i+1}", key=f"pn_{i}")
                ppin    = pcols[i % 5].text_input(f"PIN {i+1}", placeholder="0000", key=f"pp_{i}")
                perfiles_data.append((pnombre, ppin))
            if st.form_submit_button("🚀  ACTIVAR CUENTA MAESTRA", use_container_width=True):
                if mail and clv:
                    try:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO cuentas (tipo_negocio,plataforma,email,password,fecha_proveedor,costo,creador_id) VALUES ('SOCIO VIP',?,?,?,?,?,?)",
                                    (plat, mail, clv, vnc.strftime("%d/%m/%Y"), cst, uid))
                        added = sum(1 for pn,_ in perfiles_data if pn)
                        for pnombre, ppin in perfiles_data:
                            if pnombre:
                                cur.execute("INSERT INTO perfiles (email,plataforma,nombre,pin,estado,creador_id) VALUES (?,?,?,?,'LIBRE',?)",
                                            (mail, plat, pnombre, ppin, uid))
                        conn.commit()
                        st.success(f"✅ Cuenta {mail} activada con {added} perfiles.")
                    except Exception as e: st.error(f"❌ {e}")
                else: st.warning("Completa correo y contraseña.")

        st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
        st.markdown("### Cuentas registradas")
        ctas_df = pd.read_sql_query(f"SELECT * FROM cuentas WHERE creador_id={uid} ORDER BY plataforma", conn)
        if not ctas_df.empty:
            for _, row in ctas_df.iterrows():
                info = PLATAFORMAS.get(row['plataforma'], {"color":"#6366F1","emoji":"▶"})
                np_ = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE email='{row['email']}' AND creador_id={uid}", conn).iloc[0,0]
                nv_ = pd.read_sql_query(f"SELECT COUNT(*) FROM perfiles WHERE email='{row['email']}' AND estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0]
                st.markdown(f"""<div class='card' style='border-left:3px solid {info["color"]}33;'>
                    <div style='display:flex;align-items:center;gap:16px;'>
                        <span style='font-size:1.6rem;'>{info["emoji"]}</span>
                        <div style='flex:1;'>
                            <div style='color:#F1F5F9;font-weight:700;font-family:Syne,sans-serif;'>{row['email']}</div>
                            <div style='color:#475569;font-size:0.8rem;margin-top:4px;'>{row['plataforma']} · Vence: {row['fecha_proveedor']} · Costo: {moneda(row['costo'])}</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='color:#F1F5F9;font-weight:700;'>{nv_}/{np_} vendidos</div>
                            <div style='color:{info["color"]};font-size:0.78rem;margin-top:4px;font-family:DM Mono,monospace;'>● ACTIVA</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else: st.info("No tienes cuentas registradas aún.")

    else:  # CUENTAS COMPLETAS
        st.markdown("<div class='title-main'>REGISTRO DE CUENTAS</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle'>Agregar cuenta completa para entregar</div>", unsafe_allow_html=True)
        st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

        with st.form("reg_cuenta_completa"):
            c1, c2 = st.columns(2)
            plat = c1.selectbox("🎬 PLATAFORMA", list(PLATAFORMAS.keys()))
            mail = c2.text_input("📧 CORREO ELECTRÓNICO")
            clv  = c1.text_input("🔑 CONTRASEÑA")
            cst  = c2.number_input("💵 COSTO (S/)", min_value=0.0, step=0.5)
            vnc  = c1.date_input("📅 VENCIMIENTO PROVEEDOR")
            if st.form_submit_button("➕  AGREGAR CUENTA", use_container_width=True):
                if mail and clv:
                    try:
                        conn.cursor().execute(
                            "INSERT INTO cuentas_completas (plataforma,email,password,estado,costo,creador_id,fecha_proveedor) VALUES (?,?,?,'DISPONIBLE',?,?,?)",
                            (plat, mail, clv, cst, uid, vnc.strftime("%d/%m/%Y")))
                        conn.commit()
                        st.success(f"✅ Cuenta {mail} registrada.")
                    except Exception as e: st.error(f"❌ {e}")
                else: st.warning("Completa correo y contraseña.")

        st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
        st.markdown("### Cuentas registradas")
        ctas_df = pd.read_sql_query(f"SELECT * FROM cuentas_completas WHERE creador_id={uid} ORDER BY plataforma", conn)
        if not ctas_df.empty:
            for _, row in ctas_df.iterrows():
                info = PLATAFORMAS.get(row['plataforma'], {"color":"#6366F1","emoji":"▶"})
                badge = f"<span class='badge badge-disponible'>DISPONIBLE</span>" if row['estado'] == 'DISPONIBLE' else f"<span class='badge badge-entregado'>ENTREGADA</span>"
                st.markdown(f"""<div class='card' style='border-left:3px solid {info["color"]}33;'>
                    <div style='display:flex;align-items:center;gap:16px;'>
                        <span style='font-size:1.5rem;'>{info["emoji"]}</span>
                        <div style='flex:1;'>
                            <div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>
                                <span style='color:#F1F5F9;font-weight:700;'>{row['email']}</span>{badge}
                            </div>
                            <div style='color:#475569;font-size:0.8rem;'>{row['plataforma']} · Vence: {row.get('fecha_proveedor','—')}</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else: st.info("No tienes cuentas registradas aún.")

# ══════════════════════════════════════════
# GESTION
# ══════════════════════════════════════════
elif "📱" in menu:
    modo = st.session_state.get('modo', 'PERFILES')

    # ─── MODO PERFILES ───
    if modo == 'PERFILES':
        st.markdown("<div class='title-main'>GESTIÓN DE PERFILES</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle'>Administra, vende y renueva perfiles</div>", unsafe_allow_html=True)
        st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

        plat_list = list(PLATAFORMAS.keys())
        pcols = st.columns(6)
        for i, name in enumerate(plat_list):
            info = PLATAFORMAS[name]
            with pcols[i]:
                is_active = st.session_state['p_sel'] == name
                css_class = f"plat-active-{name}" if is_active else f"plat-btn-{name}"
                st.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
                if st.button(f"{info['emoji']} {name}", key=f"pb_{name}", use_container_width=True):
                    st.session_state['p_sel'] = name; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        p_sel = st.session_state['p_sel']
        info_p = PLATAFORMAS[p_sel]
        st.markdown(f"""<div class='plat-header'>
            <div class='plat-dot' style='background:{info_p["color"]};'></div>
            <div style='flex:1;'>
                <span style='color:#F1F5F9;font-weight:800;font-size:1.05rem;font-family:Syne,sans-serif;'>{p_sel}</span>
                <span style='color:#475569;font-size:0.82rem;margin-left:12px;'>Panel de administración</span>
            </div>
        </div>""", unsafe_allow_html=True)

        ctas = pd.read_sql_query(f"SELECT email, password FROM cuentas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)

        if ctas.empty:
            st.markdown("""<div style='text-align:center;padding:60px 20px;color:#374151;'>
                <div style='font-size:3rem;margin-bottom:16px;'>📭</div>
                <div style='font-weight:700;font-size:1rem;color:#64748B;'>Sin cuentas registradas para esta plataforma</div>
                <div style='font-size:0.85rem;margin-top:8px;'>Ve a "Plataformas" para agregar una cuenta maestra.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for _, c in ctas.iterrows():
                with st.expander(f"📧  {c['email']}"):
                    st.markdown(f"<div class='key-box'>🔑 &nbsp; {c['password']}</div>", unsafe_allow_html=True)

                    # Agregar perfil
                    with st.expander("➕  Agregar nuevo perfil"):
                        np_c1, np_c2, np_c3 = st.columns(3)
                        nuevo_nombre = np_c1.text_input("Nombre del perfil", key=f"nn_{c['email']}")
                        nuevo_pin    = np_c2.text_input("PIN", key=f"np_{c['email']}")
                        np_c3.write("")
                        np_c3.write("")
                        if np_c3.button("➕ AGREGAR", key=f"add_{c['email']}", use_container_width=True):
                            if nuevo_nombre:
                                conn.cursor().execute(
                                    "INSERT INTO perfiles (email,plataforma,nombre,pin,estado,creador_id) VALUES (?,?,?,?,'LIBRE',?)",
                                    (c['email'], p_sel, nuevo_nombre, nuevo_pin, uid))
                                conn.commit(); st.rerun()
                            else: st.warning("Ingresa el nombre del perfil")

                    perfs = pd.read_sql_query(f"SELECT * FROM perfiles WHERE email='{c['email']}' AND creador_id={uid}", conn)
                    if perfs.empty:
                        st.markdown("<div style='color:#475569;text-align:center;padding:20px;font-size:0.88rem;'>Sin perfiles. Agrega uno arriba.</div>", unsafe_allow_html=True)
                    else:
                        for _, row in perfs.iterrows():
                            estado_badge = "<span class='badge badge-libre'>LIBRE</span>" if row['estado'] == 'LIBRE' else "<span class='badge badge-vendido'>VENDIDO</span>"

                            # Modo edición
                            if st.session_state.get('edit_perfil_id') == row['id']:
                                st.markdown(f"<div style='background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:16px;margin:8px 0;'>", unsafe_allow_html=True)
                                st.markdown(f"<div style='color:#A5B4FC;font-size:0.8rem;font-weight:700;letter-spacing:0.08em;margin-bottom:12px;'>✏️  EDITANDO: {row['nombre']}</div>", unsafe_allow_html=True)
                                ec1, ec2 = st.columns(2)
                                e_nombre = ec1.text_input("Nombre", value=row['nombre'], key=f"en_{row['id']}")
                                e_pin    = ec2.text_input("PIN",    value=str(row['pin']) if row['pin'] else '', key=f"ep_{row['id']}")
                                eb1, eb2 = st.columns(2)
                                with eb1:
                                    if st.button("💾 GUARDAR", key=f"save_{row['id']}", use_container_width=True):
                                        conn.cursor().execute("UPDATE perfiles SET nombre=?, pin=? WHERE id=?", (e_nombre, e_pin, row['id']))
                                        conn.commit(); st.session_state['edit_perfil_id'] = None; st.rerun()
                                with eb2:
                                    if st.button("✖  CANCELAR", key=f"cancel_{row['id']}", use_container_width=True):
                                        st.session_state['edit_perfil_id'] = None; st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                                continue

                            # Vista normal
                            wa_str = f"📱 {row['whatsapp']}" if row['whatsapp'] and row['estado'] == 'VENDIDO' else ''
                            st.markdown(f"""<div class='card'>
                                <div style='display:flex;align-items:center;gap:14px;flex-wrap:wrap;'>
                                    {estado_badge}
                                    <span style='color:#E2E8F0;font-weight:600;'>👤 {row['nombre']}</span>
                                    <span style='color:#475569;font-size:0.83rem;'>PIN: <span style='font-family:DM Mono,monospace;color:#FBBF24;'>{row['pin'] or '—'}</span></span>
                                    <span style='color:#94A3B8;font-size:0.8rem;'>{wa_str}</span>
                                </div>
                            </div>""", unsafe_allow_html=True)

                            if row['estado'] == 'LIBRE':
                                vi1, vi2 = st.columns([3, 1])
                                wa_input = vi1.text_input("📱 WhatsApp cliente", placeholder="51987654321", key=f"wa_{row['id']}", label_visibility="collapsed")
                                precio_v = vi1.number_input("S/ Precio venta", min_value=0.0, key=f"pv_{row['id']}", label_visibility="collapsed")
                                ac1, ac2 = vi2.columns(2)
                                with ac1:
                                    st.markdown("<div class='btn-sell'>", unsafe_allow_html=True)
                                    if st.button("🛒\nVENDER", key=f"sell_{row['id']}", use_container_width=True):
                                        if wa_input:
                                            vence = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                            conn.cursor().execute(
                                                "UPDATE perfiles SET estado='VENDIDO',whatsapp=?,fecha_vence=?,precio_venta=?,fecha_venta=? WHERE id=?",
                                                (wa_input, vence, precio_v, datetime.now().strftime("%d/%m/%Y"), row['id']))
                                            conn.commit(); st.rerun()
                                        else: st.warning("Ingresa el WhatsApp")
                                    st.markdown("</div>", unsafe_allow_html=True)
                                with ac2:
                                    st.markdown("<div class='btn-edit'>", unsafe_allow_html=True)
                                    if st.button("✏️\nEDITAR", key=f"edit_{row['id']}", use_container_width=True):
                                        st.session_state['edit_perfil_id'] = row['id']; st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)

                            else:
                                d = calcular_dias(row['fecha_vence'])
                                st.markdown(f"<div style='margin:6px 0 10px;font-size:0.83rem;'>📅 Vence: <b style='color:#E2E8F0;'>{row['fecha_vence']}</b> &nbsp;·&nbsp; {dias_html(d)}</div>", unsafe_allow_html=True)
                                ba1, ba2, ba3, ba4 = st.columns(4)
                                with ba1:
                                    st.markdown("<div class='btn-renew'>", unsafe_allow_html=True)
                                    if st.button("🔄 RENOVAR", key=f"ren_{row['id']}", use_container_width=True):
                                        try: nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                                        except: nueva = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                        conn.cursor().execute("UPDATE perfiles SET fecha_vence=? WHERE id=?", (nueva, row['id']))
                                        conn.commit(); st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)
                                with ba2:
                                    st.markdown("<div class='btn-cut'>", unsafe_allow_html=True)
                                    if st.button("✂️ CORTAR", key=f"cut_{row['id']}", use_container_width=True):
                                        conn.cursor().execute("UPDATE perfiles SET estado='LIBRE',whatsapp=NULL,precio_venta=0 WHERE id=?", (row['id'],))
                                        conn.commit(); st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)
                                with ba3:
                                    st.markdown("<div class='btn-edit'>", unsafe_allow_html=True)
                                    if st.button("✏️ EDITAR", key=f"edit2_{row['id']}", use_container_width=True):
                                        st.session_state['edit_perfil_id'] = row['id']; st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)
                                with ba4:
                                    wa_num = row['whatsapp'] if row['whatsapp'] else ''
                                    msg = f"*🎬 ENTREGA {p_sel}*\n\n📧 Correo: {c['email']}\n🔑 Clave: {c['password']}\n👤 Perfil: {row['nombre']}\n🔢 PIN: {row['pin']}\n📅 Vence: {row['fecha_vence']}\n\n✅ ¡Gracias por tu compra!"
                                    wa_link = f"https://wa.me/{wa_num}?text={urllib.parse.quote(msg)}"
                                    st.markdown(f"""<a href="{wa_link}" target="_blank" style="text-decoration:none;">
                                        <div style="background:linear-gradient(135deg,#14532D,#166534);color:#86EFAC;border:1px solid rgba(34,197,94,0.3);
                                            border-radius:12px;padding:10px;text-align:center;font-weight:700;font-size:0.8rem;
                                            box-shadow:0 4px 12px rgba(22,163,74,0.2);">💬 WA</div>
                                    </a>""", unsafe_allow_html=True)

    # ─── MODO CUENTAS COMPLETAS ───
    else:
        st.markdown("<div class='title-main'>GESTIÓN DE CUENTAS</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle'>Entrega accesos completos a clientes</div>", unsafe_allow_html=True)
        st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

        plat_list = list(PLATAFORMAS.keys())
        pcols = st.columns(6)
        for i, name in enumerate(plat_list):
            info = PLATAFORMAS[name]
            with pcols[i]:
                is_active = st.session_state['p_sel'] == name
                css_class = f"plat-active-{name}" if is_active else f"plat-btn-{name}"
                st.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
                if st.button(f"{info['emoji']} {name}", key=f"cpb_{name}", use_container_width=True):
                    st.session_state['p_sel'] = name; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        p_sel = st.session_state['p_sel']
        info_p = PLATAFORMAS[p_sel]
        st.markdown(f"""<div class='plat-header'>
            <div class='plat-dot' style='background:{info_p["color"]};'></div>
            <div style='flex:1;'>
                <span style='color:#F1F5F9;font-weight:800;font-size:1.05rem;font-family:Syne,sans-serif;'>{p_sel}</span>
                <span style='color:#475569;font-size:0.82rem;margin-left:12px;'>Cuentas completas</span>
            </div>
        </div>""", unsafe_allow_html=True)

        cuentas = pd.read_sql_query(f"SELECT * FROM cuentas_completas WHERE plataforma='{p_sel}' AND creador_id={uid}", conn)

        if cuentas.empty:
            st.markdown("""<div style='text-align:center;padding:60px 20px;color:#374151;'>
                <div style='font-size:3rem;margin-bottom:16px;'>📭</div>
                <div style='font-weight:700;font-size:1rem;color:#64748B;'>Sin cuentas para esta plataforma</div>
                <div style='font-size:0.85rem;margin-top:8px;'>Ve a "Plataformas" para agregar cuentas.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for _, row in cuentas.iterrows():
                estado_icon = "📧" if row['estado'] == 'DISPONIBLE' else "✅"
                with st.expander(f"{estado_icon}  {row['email']}  —  {row['estado']}"):
                    st.markdown(f"""
                    <div class='key-box'>📧 &nbsp; {row['email']}</div>
                    <div class='key-box'>🔑 &nbsp; {row['password']}</div>
                    """, unsafe_allow_html=True)

                    if row['estado'] == 'DISPONIBLE':
                        g1, g2 = st.columns(2)
                        wa_c     = g1.text_input("📱 WhatsApp del cliente", placeholder="51987654321", key=f"cwa_{row['id']}")
                        precio_c = g2.number_input("💵 Precio de venta (S/)", min_value=0.0, key=f"cpv_{row['id']}")
                        fecha_v  = g1.date_input("📅 Fecha vencimiento", key=f"cfv_{row['id']}", value=datetime.now() + timedelta(days=30))
                        gc1, gc2 = st.columns(2)
                        with gc1:
                            st.markdown("<div class='btn-sell'>", unsafe_allow_html=True)
                            if st.button("🛒 ENTREGAR CUENTA", key=f"csell_{row['id']}", use_container_width=True):
                                if wa_c:
                                    conn.cursor().execute(
                                        "UPDATE cuentas_completas SET estado='ENTREGADA',whatsapp=?,fecha_vence=?,precio_venta=?,fecha_venta=? WHERE id=?",
                                        (wa_c, fecha_v.strftime("%d/%m/%Y"), precio_c, datetime.now().strftime("%d/%m/%Y"), row['id']))
                                    conn.commit(); st.rerun()
                                else: st.warning("Ingresa el WhatsApp del cliente")
                            st.markdown("</div>", unsafe_allow_html=True)
                        with gc2:
                            msg_prev = f"*🎬 CUENTA {p_sel}*\n\n📧 Correo: {row['email']}\n🔑 Clave: {row['password']}\n\n✅ ¡Gracias por tu compra!"
                            wa_link_prev = f"https://wa.me/{wa_c if wa_c else ''}?text={urllib.parse.quote(msg_prev)}"
                            st.markdown(f"""<a href="{wa_link_prev}" target="_blank" style="text-decoration:none;">
                                <div style="background:linear-gradient(135deg,#14532D,#166534);color:#86EFAC;border:1px solid rgba(34,197,94,0.3);
                                    border-radius:12px;padding:10px;text-align:center;font-weight:700;font-size:0.85rem;margin-top:28px;
                                    box-shadow:0 4px 12px rgba(22,163,74,0.2);">💬 ENVIAR POR WHATSAPP</div>
                            </a>""", unsafe_allow_html=True)
                    else:
                        d = calcular_dias(row['fecha_vence']) if row.get('fecha_vence') else 0
                        st.markdown(f"""<div style='margin:8px 0;font-size:0.85rem;'>
                            📱 Cliente: <b style='color:#E2E8F0;'>{row.get('whatsapp','—')}</b> &nbsp;·&nbsp;
                            📅 Vence: <b style='color:#E2E8F0;'>{row.get('fecha_vence','—')}</b> &nbsp;·&nbsp;
                            {dias_html(d)}
                        </div>""", unsafe_allow_html=True)
                        dr1, dr2, dr3 = st.columns(3)
                        with dr1:
                            st.markdown("<div class='btn-renew'>", unsafe_allow_html=True)
                            if st.button("🔄 RENOVAR", key=f"cren_{row['id']}", use_container_width=True):
                                try: nueva = (datetime.strptime(row['fecha_vence'], "%d/%m/%Y") + timedelta(days=30)).strftime("%d/%m/%Y")
                                except: nueva = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                                conn.cursor().execute("UPDATE cuentas_completas SET fecha_vence=? WHERE id=?", (nueva, row['id']))
                                conn.commit(); st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        with dr2:
                            st.markdown("<div class='btn-cut'>", unsafe_allow_html=True)
                            if st.button("✂️ LIBERAR", key=f"cfree_{row['id']}", use_container_width=True):
                                conn.cursor().execute("UPDATE cuentas_completas SET estado='DISPONIBLE',whatsapp=NULL,precio_venta=0 WHERE id=?", (row['id'],))
                                conn.commit(); st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        with dr3:
                            wa_n = row.get('whatsapp','')
                            msg = f"*🎬 CUENTA {p_sel}*\n\n📧 Correo: {row['email']}\n🔑 Clave: {row['password']}\n📅 Vence: {row.get('fecha_vence','—')}\n\n✅ ¡Gracias por tu compra!"
                            wa_link = f"https://wa.me/{wa_n}?text={urllib.parse.quote(msg)}"
                            st.markdown(f"""<a href="{wa_link}" target="_blank" style="text-decoration:none;">
                                <div style="background:linear-gradient(135deg,#14532D,#166534);color:#86EFAC;border:1px solid rgba(34,197,94,0.3);
                                    border-radius:12px;padding:10px;text-align:center;font-weight:700;font-size:0.82rem;
                                    box-shadow:0 4px 12px rgba(22,163,74,0.2);">💬 ENVIAR WA</div>
                            </a>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# ALERTAS
# ══════════════════════════════════════════
elif "🔔" in menu:
    st.markdown("<div class='title-main'>ALERTAS</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Clientes próximos a vencer</div>", unsafe_allow_html=True)
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    modo = st.session_state.get('modo', 'PERFILES')
    items = []

    if modo == 'PERFILES':
        perfs = pd.read_sql_query(f"SELECT p.*, c.password as clave_maestra FROM perfiles p JOIN cuentas c ON p.email=c.email WHERE p.estado='VENDIDO' AND p.creador_id={uid}", conn)
        for _, row in perfs.iterrows():
            d = calcular_dias(row['fecha_vence'])
            if d <= 7: items.append((d, row, 'perfil'))
    else:
        ctas = pd.read_sql_query(f"SELECT * FROM cuentas_completas WHERE estado='ENTREGADA' AND creador_id={uid}", conn)
        for _, row in ctas.iterrows():
            if row.get('fecha_vence'):
                d = calcular_dias(row['fecha_vence'])
                if d <= 7: items.append((d, row, 'cuenta'))

    if not items:
        st.markdown("""<div style='text-align:center;padding:60px 20px;'>
            <div style='font-size:3rem;margin-bottom:16px;'>✅</div>
            <div style='color:#34D399;font-weight:700;font-size:1rem;'>Todo al día</div>
            <div style='color:#374151;font-size:0.85rem;margin-top:8px;'>No hay clientes con vencimiento en los próximos 7 días.</div>
        </div>""", unsafe_allow_html=True)
    else:
        items.sort(key=lambda x: x[0])
        for d, row, tipo in items:
            color = "#EF4444" if d <= 2 else ("#FBBF24" if d <= 5 else "#34D399")
            alerta = "🔴" if d <= 2 else ("🟡" if d <= 5 else "🟢")
            nombre_label = row.get('nombre', row.get('email','—')) if tipo == 'perfil' else row.get('email','—')
            st.markdown(f"""<div class='card' style='border-left:3px solid {color}44;'>
                <div style='display:flex;align-items:center;gap:14px;flex-wrap:wrap;'>
                    <span style='font-size:1.4rem;'>{alerta}</span>
                    <div style='flex:1;'>
                        <div style='color:#F1F5F9;font-weight:700;'>{nombre_label} — {row['plataforma']}</div>
                        <div style='color:#475569;font-size:0.8rem;margin-top:3px;'>📱 {row.get('whatsapp','—')} · 📅 {row.get('fecha_vence','—')}</div>
                    </div>
                    <div style='color:{color};font-weight:800;font-size:1.3rem;font-family:Syne,sans-serif;'>{d}d</div>
                </div>
            </div>""", unsafe_allow_html=True)
            wa_num = row.get('whatsapp','')
            if wa_num:
                nombre_msg = row.get('nombre', row.get('email',''))
                msg = f"⚠️ *RENOVACIÓN {row['plataforma']}*\n\nHola! Tu {'perfil *' + nombre_msg + '*' if tipo == 'perfil' else 'cuenta'} vence el {row.get('fecha_vence','—')}.\n¿Deseas renovar? 🎬"
                wa_link = f"https://wa.me/{wa_num}?text={urllib.parse.quote(msg)}"
                st.markdown(f"""<a href="{wa_link}" target="_blank" style="text-decoration:none;display:inline-block;margin:4px 0 12px;">
                    <div style="background:linear-gradient(135deg,#14532D,#166534);color:#86EFAC;border:1px solid rgba(34,197,94,0.25);
                        border-radius:10px;padding:8px 20px;font-weight:700;font-size:0.8rem;
                        box-shadow:0 4px 12px rgba(22,163,74,0.15);">💬 Avisar por WhatsApp</div>
                </a>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# FINANZAS
# ══════════════════════════════════════════
elif "💰" in menu:
    st.markdown("<div class='title-main'>FINANZAS</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Análisis económico de tu operación</div>", unsafe_allow_html=True)
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    modo = st.session_state.get('modo', 'PERFILES')

    if modo == 'PERFILES':
        ingresos = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0] or 0
        costos   = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE creador_id={uid}", conn).iloc[0,0] or 0
    else:
        ingresos = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM cuentas_completas WHERE estado='ENTREGADA' AND creador_id={uid}", conn).iloc[0,0] or 0
        costos   = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas_completas WHERE creador_id={uid}", conn).iloc[0,0] or 0

    ganancia = ingresos - costos
    margen = (ganancia / ingresos * 100) if ingresos > 0 else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💵 Ingresos", moneda(ingresos))
    c2.metric("📤 Costos", moneda(costos))
    c3.metric("💰 Ganancia", moneda(ganancia))
    c4.metric("📈 Margen", f"{margen:.1f}%")

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    st.markdown("### Detalle por plataforma")
    for plat, info in PLATAFORMAS.items():
        if modo == 'PERFILES':
            ing_p = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM perfiles WHERE plataforma='{plat}' AND estado='VENDIDO' AND creador_id={uid}", conn).iloc[0,0] or 0
            cst_p = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas WHERE plataforma='{plat}' AND creador_id={uid}", conn).iloc[0,0] or 0
        else:
            ing_p = pd.read_sql_query(f"SELECT SUM(precio_venta) FROM cuentas_completas WHERE plataforma='{plat}' AND estado='ENTREGADA' AND creador_id={uid}", conn).iloc[0,0] or 0
            cst_p = pd.read_sql_query(f"SELECT SUM(costo) FROM cuentas_completas WHERE plataforma='{plat}' AND creador_id={uid}", conn).iloc[0,0] or 0
        if ing_p > 0 or cst_p > 0:
            gan_p = ing_p - cst_p
            st.markdown(f"""<div class='card' style='border-left:3px solid {info["color"]}33;'>
                <div style='display:flex;align-items:center;gap:14px;'>
                    <span style='font-size:1.5rem;'>{info["emoji"]}</span>
                    <div style='flex:1;'>
                        <div style='color:#F1F5F9;font-weight:700;font-family:Syne,sans-serif;'>{plat}</div>
                        <div style='color:#475569;font-size:0.78rem;margin-top:3px;'>Costo: {moneda(cst_p)}</div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='color:#34D399;font-weight:700;'>+{moneda(ing_p)}</div>
                        <div style='color:{"#34D399" if gan_p >= 0 else "#F87171"};font-size:0.83rem;margin-top:3px;'>Ganancia: {moneda(gan_p)}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# USUARIOS (solo ADMIN)
# ══════════════════════════════════════════
elif "👥" in menu and st.session_state['u_ran'] == 'ADMIN_GLOBAL':
    st.markdown("<div class='title-main'>USUARIOS</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Administrar accesos al sistema</div>", unsafe_allow_html=True)
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)

    with st.form("nuevo_user"):
        c1, c2, c3 = st.columns(3)
        nu = c1.text_input("USUARIO")
        np = c2.text_input("CONTRASEÑA", type="password")
        nr = c3.selectbox("ROL", ["OPERADOR", "ADMIN_GLOBAL"])
        if st.form_submit_button("➕  CREAR USUARIO", use_container_width=True):
            if nu and np:
                try:
                    conn.cursor().execute("INSERT INTO usuarios (user, password, rango) VALUES (?,?,?)", (nu, hash_pass(np), nr))
                    conn.commit(); st.success(f"✅ Usuario {nu} creado.")
                except: st.error("El usuario ya existe.")

    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    users = pd.read_sql_query("SELECT id, user, rango FROM usuarios", conn)
    for _, row in users.iterrows():
        icono = "👑" if row['rango'] == 'ADMIN_GLOBAL' else "👤"
        st.markdown(f"""<div class='card'>
            <div style='display:flex;align-items:center;gap:14px;'>
                <span style='font-size:1.4rem;'>{icono}</span>
                <div style='flex:1;'>
                    <div style='color:#F1F5F9;font-weight:700;font-family:Syne,sans-serif;'>{row["user"]}</div>
                    <div style='color:#475569;font-size:0.78rem;margin-top:2px;'>{row["rango"]}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# ELIMINAR (solo ADMIN)
# ══════════════════════════════════════════
elif "🗑️" in menu and st.session_state['u_ran'] == 'ADMIN_GLOBAL':
    st.markdown("<div class='title-main'>ELIMINAR DATOS</div>", unsafe_allow_html=True)
    st.markdown("""<div style='background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:14px;padding:16px 20px;margin-bottom:24px;'>
        <span style='color:#F87171;font-weight:700;'>⚠️ Zona peligrosa</span>
        <span style='color:#FCA5A5;font-size:0.88rem;margin-left:8px;'>Esta acción no se puede deshacer.</span>
    </div>""", unsafe_allow_html=True)

    modo = st.session_state.get('modo', 'PERFILES')
    if modo == 'PERFILES':
        ctas_e = pd.read_sql_query(f"SELECT email FROM cuentas WHERE creador_id={uid}", conn)
        if not ctas_e.empty:
            mail_del = st.selectbox("Selecciona cuenta maestra a eliminar", ctas_e['email'].tolist())
            st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
            if st.button("🗑️  ELIMINAR CUENTA Y TODOS SUS PERFILES", use_container_width=True):
                conn.cursor().execute("DELETE FROM perfiles WHERE email=?", (mail_del,))
                conn.cursor().execute("DELETE FROM cuentas WHERE email=?", (mail_del,))
                conn.commit(); st.success("Cuenta eliminada."); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("No hay cuentas para eliminar.")
    else:
        ctas_e = pd.read_sql_query(f"SELECT id, email FROM cuentas_completas WHERE creador_id={uid}", conn)
        if not ctas_e.empty:
            mail_del = st.selectbox("Selecciona cuenta a eliminar", ctas_e['email'].tolist())
            id_del = ctas_e[ctas_e['email'] == mail_del]['id'].values[0]
            st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
            if st.button("🗑️  ELIMINAR CUENTA", use_container_width=True):
                conn.cursor().execute("DELETE FROM cuentas_completas WHERE id=?", (int(id_del),))
                conn.commit(); st.success("Cuenta eliminada."); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("No hay cuentas para eliminar.")

# ══════════════════════════════════════════
# CAMBIAR CLAVE
# ══════════════════════════════════════════
elif "🔑" in menu:
    st.markdown("<div class='title-main'>CAMBIAR CONTRASEÑA</div>", unsafe_allow_html=True)
    st.markdown("<div class='glow-divider'></div>", unsafe_allow_html=True)
    with st.form("cambio_clave"):
        p_actual = st.text_input("Contraseña actual", type="password")
        p_nueva  = st.text_input("Nueva contraseña", type="password")
        p_conf   = st.text_input("Confirmar nueva contraseña", type="password")
        if st.form_submit_button("🔒  ACTUALIZAR CONTRASEÑA", use_container_width=True):
            cur = conn.cursor()
            cur.execute("SELECT password FROM usuarios WHERE id=?", (uid,))
            res = cur.fetchone()
            if res and res[0] == hash_pass(p_actual):
                if p_nueva == p_conf and len(p_nueva) >= 6:
                    cur.execute("UPDATE usuarios SET password=? WHERE id=?", (hash_pass(p_nueva), uid))
                    conn.commit(); st.success("✅ Contraseña actualizada.")
                else: st.error("Las contraseñas no coinciden o son muy cortas (mín. 6 caracteres).")
            else: st.error("Contraseña actual incorrecta.")

# ══════════════════════════════════════════
# SALIR
# ══════════════════════════════════════════
elif "🚪" in menu:
    _, cc, _ = st.columns([1.5, 1, 1.5])
    with cc:
        st.markdown("<div style='padding:60px 0 30px;text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<div class='title-main' style='text-align:center;'>¿CERRAR SESIÓN?</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#374151;text-align:center;margin:16px 0 32px;font-size:0.9rem;'>Tu sesión será terminada de forma segura.</p>", unsafe_allow_html=True)
        st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
        if st.button("🚪  SÍ, SALIR", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)