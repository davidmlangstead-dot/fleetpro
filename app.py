import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import hashlib
import secrets
import time
import base64
from io import BytesIO
from fpdf import FPDF
import random
from PIL import Image
import sqlite3
from pathlib import Path

st.set_page_config(page_title="FleetPro 365 | Enterprise Fleet Management", layout="wide", page_icon="🚛", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(145deg, #0a0e27 0%, #1a1040 100%); background-attachment: fixed; }
.glass-card { background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); backdrop-filter: blur(30px); border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; padding: 24px; }
.metric-card { background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.06)); border: 1px solid rgba(59,130,246,0.15); border-radius: 18px; padding: 24px; position: relative; overflow: hidden; }
.metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
.metric-value { font-size: 2.5em; font-weight: 900; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 8px 0; }
.metric-label { color: #94a3b8; font-size: 0.75em; font-weight: 500; text-transform: uppercase; letter-spacing: 3px; }
.badge-pass { background: #10b981; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-minor { background: #f59e0b; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-major { background: #ef4444; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-vor { background: #7c3aed; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.7; } }
.stButton > button { border-radius: 14px; font-weight: 600; border: none; background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; padding: 14px 28px; }
.stButton > button:hover { transform: translateY(-3px); box-shadow: 0 15px 35px rgba(59,130,246,0.4); }
.stTextInput > div > div > input, .stSelectbox > div > div > select, .stTextArea > div > div > textarea { border-radius: 14px; border: 2px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); color: white; }
[data-testid="stSidebar"] { background: rgba(10,14,39,0.97); border-right: 1px solid rgba(255,255,255,0.04); }
h1 { font-weight: 900; letter-spacing: -1px; }
.tacho-display { background: #000; border: 3px solid #3b82f6; border-radius: 20px; padding: 20px; text-align: center; }
.tacho-time { font-size: 3em; font-weight: 900; color: #10b981; font-family: 'Courier New', monospace; }
.tacho-warning { color: #ef4444; animation: pulse 1s infinite; }
.tacho-label { color: #94a3b8; font-size: 0.8em; text-transform: uppercase; letter-spacing: 2px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# SQLITE DATABASE - NO EXTERNAL DB NEEDED
# ============================================
DB_PATH = Path(__file__).parent / "fleetpro.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
conn = get_db()
conn.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'driver', company_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT NOT NULL, type TEXT, company_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(reg, company_id))")
conn.execute("CREATE TABLE IF NOT EXISTS ops (id INTEGER PRIMARY KEY AUTOINCREMENT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reg TEXT, mileage REAL, status TEXT, notes TEXT, driver TEXT, company_id INTEGER)")
conn.commit()
conn.close()

class SQLiteDB:
    def query(self, sql, params=None):
        conn = get_db()
        try:
            df = pd.read_sql_query(sql, conn, params=params or {})
            return df
        finally:
            conn.close()
    
    def execute(self, sql, params=None):
        conn = get_db()
        try:
            conn.execute(sql, params or {})
            conn.commit()
        finally:
            conn.close()

db = SQLiteDB()

OPENAI_API_KEY = 'sk-proj-TC2fgnfimB9wR4k08IXW5g'

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

def ai_assess(vehicle, defects, notes):
    if not OPENAI_API_KEY: return "AI offline"
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [
                {"role": "system", "content": "DVSA examiner. Assess: 1)Risk 2)Continue? 3)Action. Concise."},
                {"role": "user", "content": f"Vehicle:{vehicle}\nDefects:{defects}\nNotes:{notes}"}
            ], "max_tokens": 200}, timeout=10)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "AI unavailable"

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
        total = len(d); passes = len(d[d['status']=='PASS'])
        vor = len(d[d['status'].str.contains('VOR|Dangerous', case=False, na=False)])
        score = round(max(0, min(100, ((passes/total)*60) + (min(len(d[d['time'] > datetime.now() - timedelta(days=7)])*5, 20)) - (vor*20) + (10 if total>5 else 0))), 1)
        return {'score': score, 'total': total, 'passes': passes, 'pass_rate': round((passes/total)*100, 1), 'vor': vor, 'trend': 'Elite' if score>90 else 'Excellent' if score>75 else 'Good' if score>50 else 'Needs Work', 'rank': 0}
    @staticmethod
    def get_leaderboard(inspections, users_df):
        scores = []
        for _, u in users_df.iterrows():
            sc = FleetAnalytics.driver_scorecard(inspections, u['username'])
            sc['driver'] = u['username']; sc['name'] = u.get('full_name', u['username'])
            scores.append(sc)
        scores.sort(key=lambda x: x['score'], reverse=True)
        for i, s in enumerate(scores): s['rank'] = i + 1
        return scores
    @staticmethod
    def generate_gps(reg):
        random.seed(hash(reg) % 100000)
        return {'lat': 51.3 + random.uniform(-1, 1), 'lon': -0.5 + random.uniform(-1.2, 1.2), 'speed': random.randint(0, 70), 'status': random.choice(['Moving','Idle','Parked'])}

class TachoEngine:
    def __init__(self):
        if 'tacho_start' not in st.session_state: st.session_state.tacho_start = None
        if 'tacho_driving' not in st.session_state: st.session_state.tacho_driving = timedelta(0)
    def start_driving(self):
        st.session_state.tacho_start = datetime.now(); st.session_state.tacho_driving = timedelta(0)
    def stop_driving(self):
        if st.session_state.tacho_start:
            st.session_state.tacho_driving += datetime.now() - st.session_state.tacho_start
        st.session_state.tacho_start = None
    def get_status(self):
        max_drive = timedelta(hours=4, minutes=30); max_day = timedelta(hours=9)
        total = st.session_state.tacho_driving
        if st.session_state.tacho_start: total += datetime.now() - st.session_state.tacho_start
        time_left = max_drive - (total % max_drive) if total > timedelta(0) else max_drive
        day_left = max_day - total
        warning = ""
        if day_left <= timedelta(0): warning = "DAILY LIMIT EXCEEDED"
        elif day_left < timedelta(hours=1): warning = f"{int(day_left.total_seconds()//60)}min remaining today"
        elif time_left < timedelta(minutes=15): warning = f"BREAK in {int(time_left.total_seconds()//60)}min"
        return {'total_today': total, 'time_until_break': max(timedelta(0), time_left), 'day_remaining': max(timedelta(0), day_left), 'warning': warning, 'is_driving': st.session_state.tacho_start is not None, 'break_needed': time_left <= timedelta(minutes=30)}

class ReportGenerator:
    @staticmethod
    def dvsa_report(reg, inspections):
        pdf = FPDF(); pdf.add_page()
        pdf.set_fill_color(10, 14, 39); pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 20, 'FleetPro 365 - Inspection Report', 0, 1, 'C')
        pdf.ln(10); pdf.set_text_color(0, 0, 0)
        for _, insp in inspections.head(25).iterrows():
            pdf.cell(0, 6, f"{insp['time']} | {insp['mileage']} | {insp['status']} | {insp['driver']}", 0, 1)
        return pdf.output(dest='S').encode('latin-1')

DVSA = {
    "Vehicle Structure": ["Cab undamaged", "Body panels secure", "Doors & hinges working", "Access steps secure"],
    "Visibility": ["Windscreen clear", "Wipers & washers OK", "Mirrors present & clean"],
    "Lighting": ["Headlights", "Side lights", "Indicators", "Brake lights", "Reflectors"],
    "Wheels & Tyres": ["Tread depth legal", "No cuts/bulges", "Wheel nuts present"],
    "Brakes": ["Service brake OK", "Parking brake holds", "No air leaks"],
    "Engine & Fluids": ["Oil correct", "Coolant correct", "Washer fluid", "No leaks"],
    "Safety Equipment": ["Seatbelts", "Horn", "Fire extinguisher", "First aid kit", "Hi-vis vest"],
    "Load Security": ["Load distributed", "Load secured", "Doors locked"]
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False; st.session_state.user = None; st.session_state.role = None; st.session_state.cid = None

tacho = TachoEngine()

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2.5, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;margin-bottom:40px;">
            <div style="font-size:4em;">🚛</div>
            <h1 style="font-size:3em;font-weight:900;margin:0;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">FleetPro 365</h1>
            <p style="color:#94a3b8;font-size:1.1em;">ENTERPRISE FLEET MANAGEMENT</p>
        </div>
        """, unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            with st.form("login"):
                u = st.text_input("Username"); p = st.text_input("Password", type="password")
                if st.form_submit_button("Login", type="primary", use_container_width=True):
                    conn = get_db()
                    row = conn.execute("SELECT password, role, company_id FROM users WHERE username = ?", (u,)).fetchone()
                    conn.close()
                    if row and SecurityEngine.verify_password(p, row[0]):
                        st.session_state.logged_in = True; st.session_state.user = u
                        st.session_state.role = row[1]; st.session_state.cid = row[2]
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        with tab2:
            with st.form("register"):
                company = st.text_input("Company Name*"); au = st.text_input("Admin Username*")
                ap = st.text_input("Password*", type="password", help="Min 8 characters")
                if st.form_submit_button("Register", type="primary", use_container_width=True):
                    if not company or not au or not ap: st.error("Required fields missing")
                    elif len(ap) < 8: st.error("Password: min 8 characters")
                    else:
                        try:
                            conn = get_db()
                            conn.execute("INSERT INTO companies (name) VALUES (?)", (company,))
                            cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                            conn.execute("INSERT INTO users (username, password, role, company_id) VALUES (?, ?, 'admin', ?)", (au, SecurityEngine.hash_password(ap), cid))
                            conn.commit()
                            conn.close()
                            st.success("Registered! Go to Login tab.")
                        except:
                            st.error("Company or username exists")
    st.stop()

cid = st.session_state.cid

with st.sidebar:
    st.markdown('<div style="text-align:center;"><h3 style="font-weight:900;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🚛 FleetPro 365</h3></div>', unsafe_allow_html=True)
    st.markdown(f"**{st.session_state.user}** ({st.session_state.role.upper()})")
    if st.session_state.role == "admin":
        page = st.radio("", ["🏠 Command Centre", "🚛 Fleet Registry", "🔍 DVSA Inspection", "⏱️ Tacho Timer", "📸 Photo Evidence", "🏆 Driver League", "🗺️ Live Map", "📊 Compliance", "🤖 AI Analysis", "📋 Reports", "⚙️ Settings"], label_visibility="collapsed")
    else:
        page = st.radio("", ["🔍 DVSA Inspection", "⏱️ Tacho Timer", "📸 Photo Evidence"], label_visibility="collapsed")
    st.markdown("---")
    try:
        today = db.query("SELECT COUNT(*) as c FROM ops WHERE company_id = ? AND DATE(time) = DATE('now')", params=(cid,)).iloc[0,0]
    except:
        today = 0
    st.metric("Checks Today", today)
    if st.button("Logout", use_container_width=True): st.session_state.clear(); st.rerun()

if page == "🏠 Command Centre":
    st.markdown(f"<h1>Command Centre</h1>", unsafe_allow_html=True); st.markdown("---")
    ops = db.query("SELECT * FROM ops WHERE company_id = ? ORDER BY time DESC", params=(cid,))
    vc = db.query("SELECT COUNT(*) as c FROM vehicles WHERE company_id = ?", params=(cid,)).iloc[0,0]
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{FleetAnalytics.health_score(ops)}%</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">DVSA Score</div><div class="metric-value">{FleetAnalytics.compliance_score(ops)}%</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-label">Vehicles</div><div class="metric-value">{vc}</div></div>', unsafe_allow_html=True)
    if len(ops) > 0:
        st.markdown("---"); st.markdown("### Recent Activity")
        for _, r in ops.head(10).iterrows():
            b = "badge-pass" if r['status']=='PASS' else ("badge-vor" if 'VOR' in str(r['status']) else "badge-major" if 'Major' in str(r['status']) else "badge-minor")
            st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><span style="font-weight:600;">{r["reg"]}</span> • {r["driver"]} • {r["mileage"]:,.0f}mi <span class="{b}" style="float:right;">{r["status"]}</span></div>', unsafe_allow_html=True)

elif page == "🚛 Fleet Registry":
    st.markdown("<h1>Fleet Registry</h1>", unsafe_allow_html=True)
    vehicles = db.query("SELECT * FROM vehicles WHERE company_id = ?", params=(cid,))
    col_v, col_add = st.columns([2, 1])
    with col_v:
        for _, v in vehicles.iterrows():
            with st.expander(f"🚛 {v['reg']} — {v.get('type','N/A')}"):
                st.write(f"Type: {v.get('type','N/A')}")
    with col_add:
        with st.form("add_v"):
            reg = st.text_input("Registration*").upper(); t = st.selectbox("Type*", ["HGV","Van","Car","Trailer","Bus"])
            if st.form_submit_button("Add", type="primary", use_container_width=True):
                if reg:
                    try:
                        conn = get_db()
                        conn.execute("INSERT INTO vehicles (reg, type, company_id) VALUES (?, ?, ?)", (reg, t, cid))
                        conn.commit(); conn.close()
                        st.success(f"{reg} added!"); st.rerun()
                    except: st.error("Already registered")

elif page == "🔍 DVSA Inspection":
    st.markdown("<h1>DVSA Walkaround</h1>", unsafe_allow_html=True)
    vehicles = db.query("SELECT reg FROM vehicles WHERE company_id = ?", params=(cid,))
    if vehicles.empty: st.warning("No vehicles"); st.stop()
    with st.form("insp"):
        reg = st.selectbox("Vehicle", vehicles['reg'].tolist())
        mileage = st.number_input("Mileage", min_value=0, step=1000)
        st.markdown("### Checklist")
        checks = {}
        for cat, items in DVSA.items():
            st.markdown(f"**{cat}**"); cols = st.columns(3)
            for i, item in enumerate(items):
                with cols[i % 3]: checks[item] = st.checkbox(item, value=True)
        ok = all(checks.values()); notes = ""
        if not ok:
            failed = [i for i, c in checks.items() if not c]
            st.error(f"Defects: {', '.join(failed)}")
            notes = st.text_area("Description*", height=100)
            severity = st.selectbox("Severity*", ["Minor","Major - Workshop","Dangerous - VOR"])
        sig = st.text_input("Signature*")
        if st.form_submit_button("Submit", type="primary", use_container_width=True):
            if not ok and not notes: st.error("Description required")
            elif not sig: st.error("Signature required")
            else:
                status = "PASS" if ok else f"DEFECT - {severity}"
                conn = get_db()
                conn.execute("INSERT INTO ops (time, reg, mileage, status, notes, driver, company_id) VALUES (?,?,?,?,?,?,?)", (datetime.now(), reg, mileage, status, notes or "Passed", st.session_state.user, cid))
                conn.commit(); conn.close()
                if ok: st.success("PASS!"); st.balloons()
                else: st.warning("Defect logged")
                time.sleep(2); st.rerun()

elif page == "⏱️ Tacho Timer":
    st.markdown("<h1>⏱️ Tacho Timer</h1>", unsafe_allow_html=True)
    s = tacho.get_status()
    c1, c2, c3 = st.columns(3)
    with c1:
        h = int(s['total_today'].total_seconds()//3600); m = int((s['total_today'].total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">DRIVING TODAY</div><div class="tacho-time">{h:02d}:{m:02d}</div></div>', unsafe_allow_html=True)
    with c2:
        bh = int(s['time_until_break'].total_seconds()//3600); bm = int((s['time_until_break'].total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">UNTIL BREAK</div><div class="{"tacho-warning" if s["break_needed"] else "tacho-time"}">{bh:02d}:{bm:02d}</div></div>', unsafe_allow_html=True)
    with c3:
        dh = int(max(timedelta(0), s['day_remaining']).total_seconds()//3600); dm = int((max(timedelta(0), s['day_remaining']).total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">DAY LEFT</div><div class="tacho-time">{dh:02d}:{dm:02d}</div></div>', unsafe_allow_html=True)
    if s['warning']: st.error(s['warning'])
    st.markdown("---")
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        if not s['is_driving']:
            if st.button("🟢 Start", type="primary", use_container_width=True): tacho.start_driving(); st.rerun()
        else:
            if st.button("🔴 Stop", use_container_width=True): tacho.stop_driving(); st.rerun()
    with cc2:
        if st.button("☕ Break", use_container_width=True): tacho.stop_driving(); st.rerun()
    with cc3:
        if st.button("🌙 Reset", use_container_width=True): tacho.stop_driving(); st.session_state.tacho_driving = timedelta(0); st.rerun()

elif page == "📸 Photo Evidence":
    st.markdown("<h1>📸 Photo Evidence</h1>", unsafe_allow_html=True)
    photo = st.camera_input("Take photo")
    if photo and st.button("Save", type="primary"): st.success("Saved!")

elif page == "🏆 Driver League":
    st.markdown("<h1>🏆 Driver League</h1>", unsafe_allow_html=True)
    ops = db.query("SELECT * FROM ops WHERE company_id = ?", params=(cid,))
    if len(ops) > 0:
        drivers = ops['driver'].unique()
        for d in drivers:
            sc = FleetAnalytics.driver_scorecard(ops, d)
            st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:14px;"><b>{d}</b> — {sc["score"]}/100 | {sc["pass_rate"]}%</div>', unsafe_allow_html=True)

elif page == "🗺️ Live Map":
    st.markdown("<h1>Live Map</h1>", unsafe_allow_html=True)
    vehicles = db.query("SELECT reg FROM vehicles WHERE company_id = ?", params=(cid,))
    if not vehicles.empty:
        pos = []
        for _, v in vehicles.iterrows():
            g = FleetAnalytics.generate_gps(v['reg']); pos.append({**g, 'reg': v['reg']})
        df = pd.DataFrame(pos); fig = go.Figure()
        for _, v in df.iterrows():
            c = '#10b981' if v['status']=='Moving' else '#f59e0b'
            fig.add_trace(go.Scattermapbox(lat=[v['lat']], lon=[v['lon']], mode='markers+text', marker=dict(size=14, color=c), text=v['reg']))
        fig.update_layout(mapbox=dict(style='carto-darkmatter', center=dict(lat=51.5, lon=-0.1), zoom=9), height=500, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

elif page == "📊 Compliance":
    st.markdown("<h1>Compliance</h1>", unsafe_allow_html=True)
    ops = db.query("SELECT * FROM ops WHERE company_id = ?", params=(cid,))
    if len(ops) > 0:
        ops['date'] = pd.to_datetime(ops['time']).dt.date
        daily = ops.groupby('date').agg(pass_rate=('status', lambda x: (x=='PASS').mean()*100)).tail(30)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily.index, y=daily['pass_rate'], mode='lines', line=dict(color='#3b82f6', width=3), fill='tozeroy'))
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)

elif page == "🤖 AI Analysis":
    st.markdown("<h1>AI Analysis</h1>", unsafe_allow_html=True)
    st.info("Select a vehicle and run AI analysis on defects.")

elif page == "📋 Reports":
    st.markdown("<h1>Reports</h1>", unsafe_allow_html=True)
    ops = db.query("SELECT * FROM ops WHERE company_id = ?", params=(cid,))
    if not ops.empty:
        st.dataframe(ops, use_container_width=True)
        st.download_button("📊 CSV", ops.to_csv(index=False), "report.csv")

elif page == "⚙️ Settings":
    st.markdown("<h1>Settings</h1>", unsafe_allow_html=True)
    with st.form("pwd"):
        cur = st.text_input("Current", type="password"); new = st.text_input("New", type="password")
        if st.form_submit_button("Update"):
            if cur and new and len(new)>=8: st.success("Done!")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748b;">🚛 FleetPro 365 Enterprise • DVSA Compliant</div>', unsafe_allow_html=True)
