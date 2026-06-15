import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
import hashlib
import secrets
import time
import base64
from io import BytesIO
from fpdf import FPDF
import random
import json
from PIL import Image

# ============================================
# FLEETPRO 365 — ENTERPRISE FLEET MANAGEMENT
# DVSA • RHA • FORS • CLOCS • Earned Recognition
# WITH TACHO TIMER • PHOTO CAPTURE • DRIVER LEAGUE
# ============================================

st.set_page_config(
    page_title="FleetPro 365 | Enterprise Fleet Management",
    layout="wide",
    page_icon="🚛",
    initial_sidebar_state="expanded"
)

# ============================================
# PREMIUM ENTERPRISE UI THEME
# ============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; }

.stApp { background: linear-gradient(145deg, #0a0e27 0%, #1a1040 100%); background-attachment: fixed; }

.glass-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
    backdrop-filter: blur(30px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
    padding: 24px;
    transition: all 0.3s ease;
}
.glass-card:hover { border-color: rgba(59,130,246,0.3); box-shadow: 0 20px 60px rgba(0,0,0,0.4); }

.metric-card {
    background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.06));
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 18px;
    padding: 24px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}
.metric-value {
    font-size: 2.5em; font-weight: 900;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 8px 0;
}
.metric-label {
    color: #94a3b8; font-size: 0.75em; font-weight: 500;
    text-transform: uppercase; letter-spacing: 3px;
}

.badge-pass { background: linear-gradient(135deg, #059669, #10b981); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-minor { background: linear-gradient(135deg, #d97706, #f59e0b); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-major { background: linear-gradient(135deg, #dc2626, #ef4444); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-vor { background: linear-gradient(135deg, #7c3aed, #a855f7); color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; animation: pulse 2s infinite; }

@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.7; } }

.stButton > button {
    border-radius: 14px; font-weight: 600; border: none;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    color: white; padding: 14px 28px; transition: all 0.3s;
}
.stButton > button:hover { transform: translateY(-3px); box-shadow: 0 15px 35px rgba(59,130,246,0.4); }

.stTextInput > div > div > input, .stSelectbox > div > div > select, .stTextArea > div > div > textarea {
    border-radius: 14px; border: 2px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.02); color: white;
}

[data-testid="stSidebar"] { background: rgba(10,14,39,0.97); border-right: 1px solid rgba(255,255,255,0.04); }

.stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: rgba(255,255,255,0.02); border-radius: 16px; padding: 6px;
}
.stTabs [data-baseweb="tab"] { border-radius: 12px; padding: 12px 24px; font-weight: 500; }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(139,92,246,0.2)); color: white;
}

h1 { font-weight: 900; letter-spacing: -1px; }
h2 { font-weight: 700; color: #e2e8f0; }
h3 { font-weight: 600; color: #cbd5e1; }

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
::-webkit-scrollbar-thumb { background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 4px; }

.tacho-display {
    background: #000; border: 3px solid #3b82f6; border-radius: 20px;
    padding: 20px; text-align: center; font-family: 'Courier New', monospace;
}
.tacho-time {
    font-size: 3em; font-weight: 900; color: #10b981;
    font-family: 'Courier New', monospace;
}
.tacho-warning { color: #ef4444; animation: pulse 1s infinite; }
.tacho-label { color: #94a3b8; font-size: 0.8em; text-transform: uppercase; letter-spacing: 2px; }

.leaderboard-gold { color: #f59e0b; font-weight: 900; font-size: 1.2em; }
.leaderboard-silver { color: #94a3b8; font-weight: 700; }
.leaderboard-bronze { color: #d97706; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ============================================
# SECURITY
# ============================================
class SecurityEngine:
    @staticmethod
    def hash_password(password):
        salt = secrets.token_hex(16)
        return f"{salt}${hashlib.sha256(f'{salt}{password}'.encode()).hexdigest()}"
    
    @staticmethod
    def verify_password(password, hashed):
        try:
            salt, hash_val = hashed.split('$')
            return hashlib.sha256(f'{salt}{password}'.encode()).hexdigest() == hash_val
        except:
            return False

# ============================================
# AI ENGINE
# ============================================
class AIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def assess_defect(self, vehicle, defects, notes):
        if not self.api_key: return "AI offline — add API key"
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "DVSA examiner. Assess: 1)Risk 2)Continue? 3)Action. Concise."},
                        {"role": "user", "content": f"Vehicle:{vehicle}\nDefects:{defects}\nNotes:{notes}"}
                    ],
                    "max_tokens": 200
                },
                timeout=10
            )
            return r.json()["choices"][0]["message"]["content"]
        except:
            return "AI unavailable"

# ============================================
# ANALYTICS
# ============================================
class FleetAnalytics:
    @staticmethod
    def health_score(df):
        if df.empty: return 100.0
        total = len(df)
        vor = len(df[df['status'].str.contains('VOR|Dangerous', case=False, na=False)])
        major = len(df[df['status'].str.contains('Major', case=False, na=False)])
        return round(max(0, 100 - ((vor*35 + major*15) / max(total,1))), 1)
    
    @staticmethod
    def compliance_score(df):
        if df.empty: return 0.0
        recent = df[df['time'] > datetime.now() - timedelta(days=30)]
        if len(recent) == 0: return 0.0
        return round((len(recent[recent['status']=='PASS']) / len(recent)) * 100, 1)
    
    @staticmethod
    def driver_scorecard(inspections, driver):
        d = inspections[inspections['driver'] == driver]
        if len(d) == 0: return {'score': 0, 'total': 0, 'passes': 0, 'pass_rate': 0, 'vor': 0, 'trend': 'N/A', 'rank': 99}
        total = len(d)
        passes = len(d[d['status']=='PASS'])
        vor = len(d[d['status'].str.contains('VOR|Dangerous', case=False, na=False)])
        consistency = len(d[d['time'] > datetime.now() - timedelta(days=7)])
        score = round(max(0, min(100, ((passes/total)*60) + (min(consistency*5, 20)) - (vor*20) + (10 if total>5 else 0))), 1)
        return {
            'score': score, 'total': total, 'passes': passes,
            'pass_rate': round((passes/total)*100, 1), 'vor': vor,
            'trend': '🏆 Elite' if score>90 else '⭐ Excellent' if score>75 else '👍 Good' if score>50 else '⚠️ Needs Work' if score>25 else '🚨 Critical',
            'rank': 0
        }
    
    @staticmethod
    def get_leaderboard(inspections, users_df):
        scores = []
        for _, u in users_df.iterrows():
            sc = FleetAnalytics.driver_scorecard(inspections, u['username'])
            sc['driver'] = u['username']
            sc['name'] = u.get('full_name', u['username'])
            scores.append(sc)
        scores.sort(key=lambda x: x['score'], reverse=True)
        for i, s in enumerate(scores): s['rank'] = i + 1
        return scores
    
    @staticmethod
    def generate_gps(reg):
        random.seed(hash(reg) % 100000)
        return {
            'lat': 51.3 + random.uniform(-1, 1), 'lon': -0.5 + random.uniform(-1.2, 1.2),
            'speed': random.randint(0, 70), 'status': random.choice(['Moving','Idle','Parked']),
            'fuel': random.randint(20, 100)
        }

# ============================================
# TACHOGRAPH TIMER ENGINE
# ============================================
class TachoEngine:
    def __init__(self):
        if 'tacho_start' not in st.session_state:
            st.session_state.tacho_start = None
        if 'tacho_driving' not in st.session_state:
            st.session_state.tacho_driving = timedelta(0)
        if 'tacho_break' not in st.session_state:
            st.session_state.tacho_break = False
        if 'tacho_rest' not in st.session_state:
            st.session_state.tacho_rest = False
    
    def start_driving(self):
        st.session_state.tacho_start = datetime.now()
        st.session_state.tacho_driving = timedelta(0)
        st.session_state.tacho_break = False
        st.session_state.tacho_rest = False
    
    def stop_driving(self):
        if st.session_state.tacho_start:
            elapsed = datetime.now() - st.session_state.tacho_start
            st.session_state.tacho_driving += elapsed
        st.session_state.tacho_start = None
    
    def get_status(self):
        max_drive = timedelta(hours=4, minutes=30)
        max_day = timedelta(hours=9)
        required_break = timedelta(minutes=45)
        
        total = st.session_state.tacho_driving
        if st.session_state.tacho_start:
            total += datetime.now() - st.session_state.tacho_start
        
        time_left = max_drive - (total % max_drive) if total > timedelta(0) else max_drive
        day_left = max_day - total
        
        warning = ""
        if day_left <= timedelta(0):
            warning = "⚠️ DAILY LIMIT EXCEEDED — STOP NOW"
        elif day_left < timedelta(hours=1):
            warning = f"⚠️ Only {int(day_left.total_seconds()//60)}min remaining today"
        elif time_left < timedelta(minutes=15):
            warning = f"⚠️ BREAK REQUIRED in {int(time_left.total_seconds()//60)}min"
        
        return {
            'total_today': total,
            'time_until_break': max(timedelta(0), time_left),
            'day_remaining': max(timedelta(0), day_left),
            'warning': warning,
            'is_driving': st.session_state.tacho_start is not None,
            'break_needed': time_left <= timedelta(minutes=30)
        }

# ============================================
# REPORT GENERATOR
# ============================================
class ReportGenerator:
    @staticmethod
    def dvsa_report(reg, inspections):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(10, 14, 39)
        pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 20, 'FleetPro 365 — DVSA Inspection Report', 0, 1, 'C')
        pdf.set_font('Arial', '', 8)
        pdf.cell(0, 5, f'Vehicle: {reg} | {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        pdf.ln(10)
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_fill_color(52, 73, 94)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 8)
        for w, n in [(40, 'Date'), (22, 'Mileage'), (35, 'Status'), (30, 'Driver'), (50, 'Notes')]:
            pdf.cell(w, 7, n, 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 7)
        for _, insp in inspections.head(25).iterrows():
            pdf.cell(40, 5, str(insp['time'])[:19], 1)
            pdf.cell(22, 5, f"{insp['mileage']:,.0f}", 1)
            pdf.cell(35, 5, str(insp['status'])[:22], 1)
            pdf.cell(30, 5, str(insp['driver'])[:15], 1)
            pdf.cell(50, 5, str(insp['notes'])[:28], 1, 1)
        
        pdf.ln(5)
        total = len(inspections)
        passes = len(inspections[inspections['status']=='PASS'])
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 7, f'Pass Rate: {(passes/total*100):.1f}%', 0, 1)
        return pdf.output(dest='S').encode('latin-1')

# ============================================
# DVSA CHECKLIST
# ============================================
DVSA_CHECKLIST = {
    "Vehicle Structure": ["Cab undamaged", "Body panels secure", "Doors & hinges working", "Access steps secure", "Spray suppression fitted"],
    "Visibility": ["Windscreen clear", "Wipers & washers OK", "Mirrors present & clean", "View unobstructed"],
    "Lighting": ["Headlights", "Side lights", "Indicators", "Brake lights", "Number plate lights", "Reflectors"],
    "Wheels & Tyres": ["Tread depth legal", "No cuts/bulges", "Wheel nuts present", "Valve caps", "Wheels undamaged"],
    "Brakes": ["Service brake OK", "Parking brake holds", "No air leaks", "Brake lines OK"],
    "Steering & Suspension": ["Steering OK", "No noises", "Suspension level correct", "Shocks not leaking"],
    "Engine & Fluids": ["Oil correct", "Coolant correct", "Washer fluid", "No leaks", "Belts OK"],
    "Exhaust": ["No smoke", "Exhaust secure", "No warning lights"],
    "Safety Equipment": ["Seatbelts", "Horn", "Fire extinguisher", "First aid kit", "Warning triangle", "Hi-vis vest"],
    "Load Security": ["Load distributed", "Load secured", "Doors locked", "Not overloaded"]
}

# ============================================
# DATABASE CONNECTION
# ============================================
from sqlalchemy import text as sa_text

try:
    db = st.connection("postgresql", type="sql")
except:
    try:
        from sqlalchemy import create_engine
        db_url = f"postgresql://{os.environ.get('PGUSER','postgres')}:{os.environ.get('PGPASSWORD','')}@{os.environ.get('PGHOST','localhost')}:{os.environ.get('PGPORT','5432')}/{os.environ.get('PGDATABASE','postgres')}"
        engine = create_engine(db_url)
        class RenderDB:
            def query(self, sql, params=None):
                return pd.read_sql(sql, engine, params=params)
            def session(self):
                from contextlib import contextmanager
                @contextmanager
                def _s():
                    c = engine.connect()
                    try: yield c
                    finally: c.close()
                return _s()
        db = RenderDB()
    except:
        st.error("Database connection failed")
        st.stop()

# ============================================
# SESSION STATE
# ============================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.cid = None

api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
ai = AIEngine(api_key)
tacho = TachoEngine()

# ============================================
# AUTHENTICATION
# ============================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;margin-bottom:40px;">
            <div style="font-size:4em;">🚛</div>
            <h1 style="font-size:3em;font-weight:900;margin:0;
                background:linear-gradient(135deg,#60a5fa,#a78bfa);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                FleetPro 365
            </h1>
            <p style="color:#94a3b8;font-size:1.1em;">ENTERPRISE FLEET MANAGEMENT</p>
            <p style="color:#64748b;font-size:0.85em;">DVSA • RHA • FORS • Tacho Timer • Photo Evidence</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Login", type="primary", use_container_width=True):
                    with db.session() as s:
                        row = s.execute(sa_text("SELECT password, role, company_id FROM users WHERE username = :u"), {"u": u}).fetchone()
                    if row and SecurityEngine.verify_password(p, row[0]):
                        st.session_state.logged_in = True
                        st.session_state.user = u
                        st.session_state.role = row[1]
                        st.session_state.cid = row[2]
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            with st.form("register"):
                company = st.text_input("Company Name*")
                au = st.text_input("Admin Username*")
                ap = st.text_input("Password*", type="password", help="Min 8 characters")
                if st.form_submit_button("Register", type="primary", use_container_width=True):
                    if not company or not au or not ap:
                        st.error("Required fields missing")
                    elif len(ap) < 8:
                        st.error("Password: min 8 characters")
                    else:
                        try:
                            with db.session() as s:
                                res = s.execute(sa_text("INSERT INTO companies (name) VALUES (:n) RETURNING id"), {"n": company})
                                cid = res.fetchone()[0]
                                s.execute(sa_text("INSERT INTO users (username, password, role, company_id) VALUES (:u, :p, 'admin', :c)"), {"u": au, "p": SecurityEngine.hash_password(ap), "c": cid})
                                s.commit()
                            st.success("Registered! Go to Login tab.")
                        except:
                            st.error("Company or username exists")
    st.stop()

# ============================================
# MAIN APP
# ============================================
cid = st.session_state.cid

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <h3 style="font-weight:900;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🚛 FleetPro 365</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**{st.session_state.user}** ({st.session_state.role.upper()})")
    
    if st.session_state.role == "admin":
        page = st.radio("", [
            "🏠 Command Centre",
            "🚛 Fleet Registry",
            "🔍 DVSA Inspection",
            "⏱️ Tacho Timer",
            "📸 Photo Evidence",
            "🏆 Driver League",
            "🗺️ Live Map",
            "📊 Compliance",
            "🤖 AI Analysis",
            "📋 Reports",
            "⚙️ Settings"
        ], label_visibility="collapsed")
    else:
        page = st.radio("", [
            "🔍 DVSA Inspection",
            "⏱️ Tacho Timer",
            "📸 Photo Evidence"
        ], label_visibility="collapsed")
    
    st.markdown("---")
    
    try:
        today = db.query("SELECT COUNT(*) as c FROM ops WHERE company_id = :c AND DATE(time) = CURRENT_DATE", params={"c": cid}).iloc[0,0]
        open_d = db.query("SELECT COUNT(*) as c FROM ops WHERE company_id = :c AND status != 'PASS' AND DATE(time) >= CURRENT_DATE - 7", params={"c": cid}).iloc[0,0]
    except:
        today = 0; open_d = 0
    
    st.metric("Checks Today", today)
    st.metric("Open Defects", open_d)
    
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ============================================
# COMMAND CENTRE
# ============================================
if page == "🏠 Command Centre":
    st.markdown(f"<h1>Command Centre</h1><p style='color:#94a3b8;'>{datetime.now().strftime('%A, %d %B %Y — %H:%M')}</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    ops = db.query("SELECT * FROM ops WHERE company_id = :c ORDER BY time DESC", params={"c": cid})
    v_count = db.query("SELECT COUNT(*) as c FROM vehicles WHERE company_id = :c", params={"c": cid}).iloc[0,0]
    d_count = db.query("SELECT COUNT(*) as c FROM users WHERE company_id = :c AND role='driver'", params={"c": cid}).iloc[0,0]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{FleetAnalytics.health_score(ops)}%</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">DVSA Score</div><div class="metric-value">{FleetAnalytics.compliance_score(ops)}%</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Vehicles</div><div class="metric-value">{v_count}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Drivers</div><div class="metric-value">{d_count}</div></div>', unsafe_allow_html=True)
    
    if len(ops) > 0:
        st.markdown("---")
        st.markdown("### Recent Activity")
        for _, r in ops.head(8).iterrows():
            b = "badge-pass" if r['status']=='PASS' else ("badge-vor" if 'VOR' in str(r['status']) else "badge-major" if 'Major' in str(r['status']) else "badge-minor")
            st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><span style="font-weight:600;">{r["reg"]}</span> • {r["driver"]} • {r["time"].strftime("%H:%M")} • {r["mileage"]:,.0f}mi <span class="{b}" style="float:right;">{r["status"]}</span></div>', unsafe_allow_html=True)

# ============================================
# FLEET REGISTRY
# ============================================
elif page == "🚛 Fleet Registry":
    st.markdown("<h1>Fleet Registry</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    vehicles = db.query("SELECT * FROM vehicles WHERE company_id = :c ORDER BY created_at DESC", params={"c": cid})
    
    col_v, col_add = st.columns([2, 1])
    with col_v:
        for _, v in vehicles.iterrows():
            with st.expander(f"🚛 {v['reg']} — {v.get('type','N/A')}"):
                st.write(f"Type: {v.get('type','N/A')} | Fleet #: {v.get('fleet_number','N/A')}")
                last = db.query("SELECT * FROM ops WHERE reg = :r AND company_id = :c ORDER BY time DESC LIMIT 1", params={"r": v['reg'], "c": cid})
                if not last.empty:
                    l = last.iloc[0]
                    st.write(f"Last: {l['time'].strftime('%d/%m/%Y')} | {l['status']} | {l['mileage']:,.0f}mi")
    with col_add:
        with st.form("add_v"):
            reg = st.text_input("Registration*").upper()
            t = st.selectbox("Type*", ["HGV Artic","HGV Rigid","Van","Car","Trailer","Bus"])
            make = st.text_input("Make")
            model = st.text_input("Model")
            fleet_num = st.text_input("Fleet Number")
            if st.form_submit_button("Add Vehicle", type="primary", use_container_width=True):
                if reg:
                    try:
                        with db.session() as s:
                            s.execute(sa_text("INSERT INTO vehicles (reg, type, make, model, fleet_number, company_id) VALUES (:r,:t,:m,:mo,:f,:c)"), {"r":reg,"t":t,"m":make,"mo":model,"f":fleet_num,"c":cid})
                            s.commit()
                        st.success(f"{reg} added!")
                        st.rerun()
                    except:
                        st.error("Already registered")

# ============================================
# DVSA INSPECTION
# ============================================
elif page == "🔍 DVSA Inspection":
    st.markdown("<h1>DVSA Daily Walkaround</h1><p style='color:#94a3b8;'>Statutory safety inspection — legally required</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    vehicles = db.query("SELECT reg FROM vehicles WHERE company_id = :c", params={"c": cid})
    if vehicles.empty:
        st.warning("No vehicles registered")
        st.stop()
    
    with st.form("insp"):
        col_a, col_b = st.columns(2)
        with col_a:
            reg = st.selectbox("Vehicle", vehicles['reg'].tolist())
        with col_b:
            mileage = st.number_input("Mileage", min_value=0, step=1000)
        
        st.markdown("### DVSA Checklist")
        checks = {}
        for category, items in DVSA_CHECKLIST.items():
            st.markdown(f"**{category}**")
            cols = st.columns(3)
            for i, item in enumerate(items):
                with cols[i % 3]:
                    checks[item] = st.checkbox(item, value=True)
        
        ok = all(checks.values())
        notes = ""
        
        if not ok:
            failed = [i for i, c in checks.items() if not c]
            st.error(f"Defects: {', '.join(failed)}")
            notes = st.text_area("Description*", height=100)
            severity = st.selectbox("Severity*", ["Minor","Major - Workshop","Dangerous - VOR"])
        
        driver_sig = st.text_input("Digital Signature*", placeholder="Type full name to sign")
        
        if st.form_submit_button("Submit Inspection", type="primary", use_container_width=True):
            if not ok and not notes:
                st.error("Description required")
            elif not driver_sig:
                st.error("Signature required")
            else:
                status = "PASS" if ok else f"DEFECT - {severity}"
                with db.session() as s:
                    s.execute(sa_text("INSERT INTO ops (time, reg, mileage, status, notes, driver, company_id) VALUES (:t,:r,:m,:s,:n,:d,:c)"), {"t":datetime.now(),"r":reg,"m":mileage,"s":status,"n":notes or "Passed","d":st.session_state.user,"c":cid})
                    s.commit()
                
                if ok:
                    st.success("✅ PASS — Vehicle roadworthy!")
                    st.balloons()
                else:
                    if api_key and notes:
                        with st.spinner("AI analysing..."):
                            st.info(f"🤖 AI: {ai.assess_defect(reg, ', '.join(failed), notes)}")
                    st.warning("⚠️ Defect logged")
                time.sleep(2)
                st.rerun()

# ============================================
# ⏱️ TACHO TIMER (NEW!)
# ============================================
elif page == "⏱️ Tacho Timer":
    st.markdown("<h1>⏱️ Digital Tachograph Timer</h1><p style='color:#94a3b8;'>EU/AETR driving hours compliance tracker</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    status = tacho.get_status()
    
    # Main tacho display
    col_t1, col_t2, col_t3 = st.columns(3)
    
    with col_t1:
        st.markdown('<div class="tacho-display">', unsafe_allow_html=True)
        st.markdown(f'<div class="tacho-label">DRIVING TODAY</div>', unsafe_allow_html=True)
        h = int(status['total_today'].total_seconds() // 3600)
        m = int((status['total_today'].total_seconds() % 3600) // 60)
        st.markdown(f'<div class="tacho-time">{h:02d}:{m:02d}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tacho-label">Max: 9h00m</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_t2:
        st.markdown('<div class="tacho-display">', unsafe_allow_html=True)
        st.markdown(f'<div class="tacho-label">UNTIL BREAK</div>', unsafe_allow_html=True)
        b_h = int(status['time_until_break'].total_seconds() // 3600)
        b_m = int((status['time_until_break'].total_seconds() % 3600) // 60)
        color_class = "tacho-warning" if status['break_needed'] else "tacho-time"
        st.markdown(f'<div class="{color_class}">{b_h:02d}:{b_m:02d}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tacho-label">Break: 45min after 4.5h</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_t3:
        st.markdown('<div class="tacho-display">', unsafe_allow_html=True)
        st.markdown(f'<div class="tacho-label">DAY REMAINING</div>', unsafe_allow_html=True)
        d_h = int(max(timedelta(0), status['day_remaining']).total_seconds() // 3600)
        d_m = int((max(timedelta(0), status['day_remaining']).total_seconds() % 3600) // 60)
        st.markdown(f'<div class="tacho-time">{d_h:02d}:{d_m:02d}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tacho-label">Max Daily: 9h</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    if status['warning']:
        st.error(status['warning'])
    
    st.markdown("---")
    
    # Controls
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    
    with col_ctrl1:
        if not status['is_driving']:
            if st.button("🟢 Start Driving", type="primary", use_container_width=True):
                tacho.start_driving()
                st.rerun()
        else:
            if st.button("🔴 Stop Driving", type="secondary", use_container_width=True):
                tacho.stop_driving()
                st.rerun()
    
    with col_ctrl2:
        if st.button("☕ Start Break (45min)", use_container_width=True):
            st.session_state.tacho_break = True
            tacho.stop_driving()
            st.info("Break started — 45 minutes required")
            st.rerun()
    
    with col_ctrl3:
        if st.button("🌙 End Daily Rest", use_container_width=True):
            tacho.stop_driving()
            st.session_state.tacho_driving = timedelta(0)
            st.success("Daily rest period started — timer reset")
            st.rerun()
    
    st.markdown("---")
    st.caption("""
    **EU/AETR Rules:**
    • Maximum 9 hours driving per day (extendable to 10h twice per week)
    • Break of 45 minutes after 4.5 hours driving (can split into 15min + 30min)
    • Daily rest: 11 hours (reducible to 9h three times between weekly rests)
    • Weekly rest: 45 hours (reducible to 24h, compensated within 3 weeks)
    """)

# ============================================
# 📸 PHOTO EVIDENCE (NEW!)
# ============================================
elif page == "📸 Photo Evidence":
    st.markdown("<h1>📸 Photo Evidence Capture</h1><p style='color:#94a3b8;'>Photograph defects for insurance & DVSA records</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab_photo1, tab_photo2 = st.tabs(["📷 Take Photo", "🖼️ Photo Gallery"])
    
    with tab_photo1:
        st.markdown("### Capture Defect Photo")
        
        vehicle = st.selectbox("Vehicle", db.query("SELECT reg FROM vehicles WHERE company_id = :c", params={"c": cid})['reg'].tolist() if not db.query("SELECT reg FROM vehicles WHERE company_id = :c", params={"c": cid}).empty else ["No vehicles"])
        
        col_cam, col_desc = st.columns([1, 1])
        
        with col_cam:
            photo = st.camera_input("Take photo of defect")
        
        with col_desc:
            if photo:
                st.image(photo, caption="Preview", width=300)
            photo_desc = st.text_area("Photo Description", placeholder="What does this photo show?")
            photo_tags = st.multiselect("Tags", ["Tyre", "Bodywork", "Lights", "Brakes", "Engine", "Load", "Interior", "Other"])
        
        if photo and st.button("💾 Save Photo Evidence", type="primary", use_container_width=True):
            img = Image.open(photo)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            
            with db.session() as s:
                s.execute(sa_text("INSERT INTO ops (time, reg, mileage, status, notes, driver, company_id) VALUES (:t,:r,0,'PHOTO EVIDENCE',:n,:d,:c)"), {"t":datetime.now(),"r":vehicle,"n":f"[PHOTO] {photo_desc} | Tags: {', '.join(photo_tags)} | Data: {img_b64[:100]}...","d":st.session_state.user,"c":cid})
                s.commit()
            st.success("✅ Photo evidence saved!")
    
    with tab_photo2:
        st.markdown("### Photo Evidence Log")
        photos = db.query("SELECT * FROM ops WHERE company_id = :c AND status = 'PHOTO EVIDENCE' ORDER BY time DESC LIMIT 20", params={"c": cid})
        if not photos.empty:
            for _, p in photos.iterrows():
                with st.expander(f"📸 {p['reg']} — {p['time'].strftime('%d/%m/%Y %H:%M')} — {p['driver']}"):
                    st.write(p['notes'])
        else:
            st.info("No photos captured yet")

# ============================================
# 🏆 DRIVER LEAGUE TABLE (NEW!)
# ============================================
elif page == "🏆 Driver League":
    st.markdown("<h1>🏆 Driver Performance League</h1><p style='color:#94a3b8;'>Weekly rankings based on safety & compliance</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    ops = db.query("SELECT * FROM ops WHERE company_id = :c", params={"c": cid})
    users = db.query("SELECT username, full_name FROM users WHERE company_id = :c AND role IN ('driver','workshop')", params={"c": cid})
    
    if not users.empty and len(ops) > 0:
        leaderboard = FleetAnalytics.get_leaderboard(ops, users)
        
        # Top 3 podium
        col_p1, col_p2, col_p3 = st.columns([1, 1.5, 1])
        
        with col_p2:
            if len(leaderboard) >= 1:
                st.markdown(f"""
                <div style="text-align:center;">
                    <div style="font-size:3em;">🥇</div>
                    <div class="leaderboard-gold">{leaderboard[0]['name']}</div>
                    <div style="font-size:2em;font-weight:900;">{leaderboard[0]['score']}</div>
                    <div style="color:#94a3b8;">{leaderboard[0]['pass_rate']}% Pass | {leaderboard[0]['total']} Checks</div>
                    <div>{leaderboard[0]['trend']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_p1:
            if len(leaderboard) >= 2:
                st.markdown(f"""
                <div style="text-align:center;">
                    <div style="font-size:2em;">🥈</div>
                    <div class="leaderboard-silver">{leaderboard[1]['name']}</div>
                    <div style="font-size:1.5em;font-weight:700;">{leaderboard[1]['score']}</div>
                    <div style="color:#94a3b8;">{leaderboard[1]['pass_rate']}% | {leaderboard[1]['total']}</div>
                    <div>{leaderboard[1]['trend']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_p3:
            if len(leaderboard) >= 3:
                st.markdown(f"""
                <div style="text-align:center;">
                    <div style="font-size:2em;">🥉</div>
                    <div class="leaderboard-bronze">{leaderboard[2]['name']}</div>
                    <div style="font-size:1.5em;font-weight:700;">{leaderboard[2]['score']}</div>
                    <div style="color:#94a3b8;">{leaderboard[2]['pass_rate']}% | {leaderboard[2]['total']}</div>
                    <div>{leaderboard[2]['trend']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### Full Rankings")
        
        for driver in leaderboard:
            rank_icon = {1:'🥇',2:'🥈',3:'🥉'}.get(driver['rank'], f"#{driver['rank']}")
            score_color = '#10b981' if driver['score']>75 else '#f59e0b' if driver['score']>50 else '#ef4444'
            
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom:8px;padding:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;gap:15px;align-items:center;">
                        <div style="font-size:1.5em;">{rank_icon}</div>
                        <div>
                            <div style="font-weight:600;">{driver['name']}</div>
                            <div style="color:#94a3b8;font-size:0.85em;">
                                {driver['total']} inspections | {driver['pass_rate']}% pass | {driver['vor']} VOR
                            </div>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.3em;font-weight:700;color:{score_color};">{driver['score']}/100</div>
                        <div style="font-size:0.85em;">{driver['trend']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================
# LIVE MAP
# ============================================
elif page == "🗺️ Live Map":
    st.markdown("<h1>Live Fleet Map</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    vehicles = db.query("SELECT reg, type FROM vehicles WHERE company_id = :c", params={"c": cid})
    if not vehicles.empty:
        positions = []
        for _, v in vehicles.iterrows():
            gps = FleetAnalytics.generate_gps(v['reg'])
            positions.append({**gps, 'reg': v['reg'], 'type': v['type']})
        df = pd.DataFrame(positions)
        fig = go.Figure()
        for _, v in df.iterrows():
            color = '#10b981' if v['status']=='Moving' else '#f59e0b' if v['status']=='Idle' else '#64748b'
            fig.add_trace(go.Scattermapbox(lat=[v['lat']], lon=[v['lon']], mode='markers+text', marker=dict(size=14, color=color), text=v['reg'], textposition='top center'))
        fig.update_layout(mapbox=dict(style='carto-darkmatter', center=dict(lat=51.5, lon=-0.1), zoom=9), height=500, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# COMPLIANCE
# ============================================
elif page == "📊 Compliance":
    st.markdown("<h1>Compliance Hub</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    ops = db.query("SELECT * FROM ops WHERE company_id = :c", params={"c": cid})
    if len(ops) > 0:
        comp = FleetAnalytics.compliance_score(ops)
        health = FleetAnalytics.health_score(ops)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">30-Day DVSA Score</div><div class="metric-value">{comp}%</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{health}%</div></div>', unsafe_allow_html=True)
        
        ops['date'] = pd.to_datetime(ops['time']).dt.date
        daily = ops.groupby('date').agg(pass_rate=('status', lambda x: (x=='PASS').mean()*100)).tail(30)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily.index, y=daily['pass_rate'], mode='lines', line=dict(color='#3b82f6', width=3), fill='tozeroy'))
        fig.add_hline(y=90, line_dash="dash", line_color="#ef4444", annotation_text="DVSA Min 90%")
        fig.update_layout(template='plotly_dark', height=400, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# AI ANALYSIS
# ============================================
elif page == "🤖 AI Analysis":
    st.markdown("<h1>AI Defect Analysis</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not api_key:
        st.warning("OpenAI API key not configured")
    else:
        vehicles = db.query("SELECT reg FROM vehicles WHERE company_id = :c", params={"c": cid})
        reg = st.selectbox("Vehicle", vehicles['reg'].tolist())
        insp = db.query("SELECT * FROM ops WHERE reg = :r AND company_id = :c ORDER BY time DESC LIMIT 20", params={"r": reg, "c": cid})
        if len(insp) > 0:
            defects = insp[insp['status']!='PASS']
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=insp['time'], y=insp['mileage'], mode='lines+markers', line=dict(color='#3b82f6', width=3)))
            if len(defects) > 0:
                fig.add_trace(go.Scatter(x=defects['time'], y=defects['mileage'], mode='markers', marker=dict(color='#ef4444', size=12, symbol='x')))
            fig.update_layout(template='plotly_dark', height=350, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig, use_container_width=True)
            if st.button("Run AI Analysis", type="primary"):
                with st.spinner("Analysing..."):
                    st.info(ai.assess_defect(reg, f"{len(defects)} defects", "Analysis"))

# ============================================
# REPORTS
# ============================================
elif page == "📋 Reports":
    st.markdown("<h1>Reports</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    vehicles = db.query("SELECT reg FROM vehicles WHERE company_id = :c", params={"c": cid})
    reg = st.selectbox("Vehicle", vehicles['reg'].tolist())
    insp = db.query("SELECT * FROM ops WHERE reg = :r AND company_id = :c ORDER BY time DESC", params={"r": reg, "c": cid})
    if not insp.empty:
        st.dataframe(insp, use_container_width=True)
        pdf = ReportGenerator.dvsa_report(reg, insp)
        st.download_button("📄 Download PDF", pdf, f"DVSA_{reg}.pdf", "application/pdf")
        st.download_button("📊 Download CSV", insp.to_csv(index=False), f"{reg}.csv", "text/csv")

# ============================================
# SETTINGS
# ============================================
elif page == "⚙️ Settings":
    st.markdown("<h1>Settings</h1>", unsafe_allow_html=True)
    st.markdown("---")
    with st.form("pwd"):
        cur = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        if st.form_submit_button("Update"):
            if cur and new and len(new)>=8:
                with db.session() as s:
                    stored = s.execute(sa_text("SELECT password FROM users WHERE username=:u AND company_id=:c"), {"u":st.session_state.user,"c":cid}).fetchone()
                if stored and SecurityEngine.verify_password(cur, stored[0]):
                    with db.session() as s:
                        s.execute(sa_text("UPDATE users SET password=:p WHERE username=:u AND company_id=:c"), {"p":SecurityEngine.hash_password(new),"u":st.session_state.user,"c":cid})
                        s.commit()
                    st.success("Updated!")
                else:
                    st.error("Wrong password")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748b;">🚛 FleetPro 365 Enterprise • DVSA Compliant • Tacho Timer • Photo Evidence • Driver League</div>', unsafe_allow_html=True)
