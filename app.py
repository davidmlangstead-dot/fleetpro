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
import os
import json

st.set_page_config(page_title="Enterprise Command Centre | Fleet • Staff • Safety • Office",layout="wide",page_icon="🏢",initial_sidebar_state="expanded",manifest={"name":"Enterprise Command","short_name":"EntCmd","start_url":"/","display":"standalone","background_color":"#0a0e27","theme_color":"#3b82f6"})

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{font-family:'Inter',sans-serif}
.stApp{background:linear-gradient(145deg,#0a0e27 0%,#1a1040 100%);background-attachment:fixed}
.glass-card{background:linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01));backdrop-filter:blur(30px);border:1px solid rgba(255,255,255,0.06);border-radius:20px;padding:24px;transition:all 0.3s ease}
.glass-card:hover{border-color:rgba(59,130,246,0.3);box-shadow:0 20px 60px rgba(0,0,0,0.4)}
.metric-card{background:linear-gradient(135deg,rgba(59,130,246,0.08),rgba(139,92,246,0.06));border:1px solid rgba(59,130,246,0.15);border-radius:18px;padding:24px;position:relative;overflow:hidden}
.metric-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#3b82f6,#8b5cf6)}
.metric-value{font-size:2.5em;font-weight:900;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:8px 0}
.metric-label{color:#94a3b8;font-size:.75em;font-weight:500;text-transform:uppercase;letter-spacing:3px}
.badge-pass{background:#10b981;color:#fff;padding:6px 16px;border-radius:20px;font-weight:600;font-size:.85em}
.badge-major{background:#ef4444;color:#fff;padding:6px 16px;border-radius:20px;font-weight:600;font-size:.85em}
.badge-vor{background:#7c3aed;color:#fff;padding:6px 16px;border-radius:20px;font-weight:600;font-size:.85em;animation:pulse 2s infinite}
.badge-critical{background:#dc2626;color:#fff;padding:6px 16px;border-radius:20px;font-weight:600;font-size:.85em;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.7}}
.stButton>button{border-radius:14px;font-weight:600;border:none;background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff;padding:14px 28px}
.stButton>button:hover{transform:translateY(-3px);box-shadow:0 15px 35px rgba(59,130,246,0.4)}
.stTextInput>div>div>input,.stSelectbox>div>div>select,.stTextArea>div>div>textarea{border-radius:14px;border:2px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.02);color:#fff}
[data-testid="stSidebar"]{background:rgba(10,14,39,0.97);border-right:1px solid rgba(255,255,255,0.04)}
h1{font-weight:900;letter-spacing:-1px}
h2{font-weight:700;color:#e2e8f0}
h3{font-weight:600;color:#cbd5e1}
.instruction-step{background:linear-gradient(135deg,rgba(59,130,246,0.1),rgba(139,92,246,0.05));border-left:4px solid #3b82f6;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px}
.message-bubble{background:rgba(59,130,246,0.15);padding:12px 16px;border-radius:16px;margin-bottom:8px;max-width:80%}
.message-mine{background:rgba(16,185,129,0.15);margin-left:auto}
.task-pending{border-left:4px solid #f59e0b}
.task-done{border-left:4px solid #10b981;opacity:0.7}
.tacho-display{background:#000;border:3px solid #3b82f6;border-radius:20px;padding:20px;text-align:center}
.tacho-time{font-size:3em;font-weight:900;color:#10b981;font-family:'Courier New',monospace}
.tacho-label{color:#94a3b8;font-size:0.8em;text-transform:uppercase;letter-spacing:2px}
</style>
""",unsafe_allow_html=True)

# ============================================
# DATABASE
# ============================================
DB_PATH = Path(__file__).parent / "enterprise.db"
def get_db():
    conn = sqlite3.connect(str(DB_PATH)); conn.row_factory = sqlite3.Row; return conn

conn = get_db()
conn.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, branding_color DEFAULT '#3b82f6', email_alerts TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'worker', full_name TEXT, phone TEXT, email TEXT, emergency_contact TEXT, company_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS sites (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, name TEXT, address TEXT, lat REAL, lon REAL, manager TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT, type TEXT, make TEXT, model TEXT, fleet_number TEXT, site_id INTEGER, company_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(reg, company_id))")
conn.execute("CREATE TABLE IF NOT EXISTS ops (id INTEGER PRIMARY KEY AUTOINCREMENT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reg TEXT, mileage REAL, status TEXT, notes TEXT, driver TEXT, company_id INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS shifts (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, site_id INTEGER, shift_date DATE, start_time TEXT, end_time TEXT, clock_in TIMESTAMP, clock_out TIMESTAMP, status TEXT DEFAULT 'Scheduled')")
conn.execute("CREATE TABLE IF NOT EXISTS certifications (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, cert_name TEXT, expiry_date DATE, status TEXT DEFAULT 'Valid')")
conn.execute("CREATE TABLE IF NOT EXISTS training (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, title TEXT, description TEXT, video_url TEXT, required_roles TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS training_records (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, training_id INTEGER, completed_at TIMESTAMP, score REAL)")
conn.execute("CREATE TABLE IF NOT EXISTS near_misses (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, site_id INTEGER, reporter TEXT, title TEXT, description TEXT, severity TEXT, category TEXT, location TEXT, lat REAL, lon REAL, photo_data TEXT, investigation TEXT, corrective_action TEXT, status TEXT DEFAULT 'Reported', reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS custom_forms (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, form_name TEXT, form_fields TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS form_submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, form_id INTEGER, user_id INTEGER, submission_data TEXT, submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS lone_worker_checkins (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, site_id INTEGER, checkin_time TIMESTAMP, location TEXT, status TEXT DEFAULT 'Safe')")
conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, sender_id INTEGER, recipient_id INTEGER, subject TEXT, body TEXT, read BOOLEAN DEFAULT 0, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS calendar_events (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, title TEXT, description TEXT, event_date DATE, start_time TEXT, end_time TEXT, created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, filename TEXT, description TEXT, uploaded_by INTEGER, file_data TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, title TEXT, description TEXT, assigned_to INTEGER, assigned_by INTEGER, priority TEXT DEFAULT 'Normal', status TEXT DEFAULT 'Pending', due_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, customer_name TEXT, description TEXT, status DEFAULT 'Pending', quoted_amount REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, job_id INTEGER, customer_name TEXT, total REAL, status DEFAULT 'Unpaid', due_date DATE)")
conn.execute("CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, vehicle_reg TEXT, service_type TEXT, due_date DATE, status DEFAULT 'Scheduled')")
conn.execute("CREATE TABLE IF NOT EXISTS fuel_log (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, vehicle_reg TEXT, date DATE, litres REAL, cost REAL, mileage REAL, mpg REAL, driver TEXT)")
conn.commit(); conn.close()

class DB:
    def query(self, sql, params=None):
        c = get_db()
        try: return pd.read_sql_query(sql, c, params=params or ())
        finally: c.close()
    def execute(self, sql, params=None):
        c = get_db()
        try: c.execute(sql, params or ()); c.commit()
        finally: c.close()

db = DB()
OPENAI_API_KEY = 'sk-proj-TC2fgnfimB9wR4k08IXW5g'

class Security:
    @staticmethod
    def hash(p): s=secrets.token_hex(16); return f"{s}${hashlib.sha256(f'{s}{p}'.encode()).hexdigest()}"
    @staticmethod
    def verify(p, h):
        try: s, hv = h.split('$'); return hashlib.sha256(f'{s}{p}'.encode()).hexdigest() == hv
        except: return False

def ai_analyze(prompt):
    if not OPENAI_API_KEY: return "AI offline"
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"},
            json={"model":"gpt-4o-mini","messages":[{"role":"system","content":"Expert. 3 bullet points max."},{"role":"user","content":prompt}],"max_tokens":200},timeout=10)
        return r.json()["choices"][0]["message"]["content"]
    except: return "AI unavailable"

class Analytics:
    @staticmethod
    def health(df):
        if df.empty: return 100.0
        t=len(df);vor=len(df[df['status'].str.contains('VOR|Dangerous',case=False,na=False)]);maj=len(df[df['status'].str.contains('Major',case=False,na=False)])
        return round(max(0,100-((vor*35+maj*15)/max(t,1))),1)
    @staticmethod
    def gen_gps(reg):
        random.seed(hash(reg)%100000)
        return {'lat':51.3+random.uniform(-1,1),'lon':-0.5+random.uniform(-1.2,1.2),'speed':random.randint(0,70)}

class TachoEngine:
    def __init__(self):
        if 'ts' not in st.session_state: st.session_state.ts=None
        if 'td' not in st.session_state: st.session_state.td=timedelta(0)
    def start(self): st.session_state.ts=datetime.now();st.session_state.td=timedelta(0)
    def stop(self):
        if st.session_state.ts: st.session_state.td+=datetime.now()-st.session_state.ts
        st.session_state.ts=None
    def status(self):
        md=timedelta(hours=4,minutes=30);mx=timedelta(hours=9)
        t=st.session_state.td
        if st.session_state.ts: t+=datetime.now()-st.session_state.ts
        tl=md-(t%md) if t>timedelta(0) else md;dl=mx-t
        w=""
        if dl<=timedelta(0): w="DAILY LIMIT EXCEEDED"
        elif dl<timedelta(hours=1): w=f"{int(dl.total_seconds()//60)}min left"
        elif tl<timedelta(minutes=15): w=f"BREAK in {int(tl.total_seconds()//60)}min"
        return {'total':t,'until_break':max(timedelta(0),tl),'day_left':max(timedelta(0),dl),'warning':w,'driving':st.session_state.ts is not None}

DVSA = {"Structure":["Cab undamaged","Body panels secure","Doors working"],"Visibility":["Windscreen clear","Wipers OK","Mirrors clean"],"Lighting":["Headlights","Indicators","Brake lights"],"Tyres":["Tread legal","No cuts","Wheel nuts present"],"Brakes":["Service brake OK","Parking holds","No leaks"],"Engine":["Oil correct","Coolant correct","No leaks"],"Safety":["Seatbelts","Horn","Extinguisher","First aid"],"Load":["Load distributed","Load secured","Doors locked"]}
NEAR_MISS_CATEGORIES = ["Slip/Trip/Fall","Vehicle/Plant","Manual Handling","Working at Height","Electrical","Fire/Explosion","Chemical Spill","Equipment Failure","Structural","Other"]
SEVERITY_LEVELS = ["Low — Near Miss","Medium — Minor Injury Possible","High — Serious Injury Possible","Critical — Fatality Risk"]

tacho = TachoEngine()

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False;st.session_state.user=None;st.session_state.role=None;st.session_state.cid=None

if not st.session_state.logged_in:
    c1,c2,c3=st.columns([1,2.5,1])
    with c2:
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;margin-bottom:40px;"><div style="font-size:4em;">🏢</div><h1 style="font-size:3em;font-weight:900;margin:0;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Enterprise Command</h1><p style="color:#94a3b8;font-size:1.1em;">FLEET • STAFF • SAFETY • OFFICE • PWA • AI</p></div>""",unsafe_allow_html=True)
        t1,t2=st.tabs(["Login","Register"])
        with t1:
            with st.form("login"):
                u=st.text_input("Username");p=st.text_input("Password",type="password")
                if st.form_submit_button("Login",type="primary",use_container_width=True):
                    c=get_db();r=c.execute("SELECT password,role,company_id FROM users WHERE username=?",(u,)).fetchone();c.close()
                    if r and Security.verify(p,r[0]): st.session_state.logged_in=True;st.session_state.user=u;st.session_state.role=r[1];st.session_state.cid=r[2];st.rerun()
                    else: st.error("Invalid credentials")
        with t2:
            with st.form("register"):
                co=st.text_input("Company*");au=st.text_input("Admin Username*");ap=st.text_input("Password*",type="password")
                if st.form_submit_button("Deploy Platform",type="primary",use_container_width=True):
                    if not co or not au or not ap: st.error("Fill all fields")
                    elif len(ap)<8: st.error("Password: 8+ chars")
                    else:
                        try:
                            c=get_db();c.execute("INSERT INTO companies (name) VALUES (?)",(co,));cid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
                            c.execute("INSERT INTO users (username,password,role,company_id) VALUES (?,?,'admin',?)",(au,Security.hash(ap),cid));c.commit();c.close()
                            st.success("✅ Deployed! Go to Login.");st.balloons()
                        except: st.error("Company/username exists")
    st.stop()

cid=st.session_state.cid;role=st.session_state.role

def sq(sql,p=None):
    try: return db.query(sql,p)
    except: return pd.DataFrame()

with st.sidebar:
    st.markdown('<div style="text-align:center;"><h3 style="font-weight:900;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🏢 Enterprise</h3></div>',unsafe_allow_html=True)
    st.markdown(f"**{st.session_state.user}** ({role.upper()})")
    if role=="admin":
        page=st.radio("",["📖 Help Guide","🏠 Command","🚛 Fleet","👥 Staff","⚠️ Near Miss","📍 Sites","🗺️ Map","📧 Messages","📅 Calendar","📁 Documents","✅ Tasks","🔧 Workshop","💰 Jobs","⛽ Fuel","🔔 Maintenance","🔍 Inspection","⏱️ Tacho","📸 Photos","🏆 Safety League","🎓 Training","📋 Forms","🆘 Lone Worker","📊 Compliance","🤖 AI","📋 Reports","⚙️ Settings"],label_visibility="collapsed")
    elif role=="driver": page=st.radio("",["📖 Help Guide","🔍 Inspection","⏱️ Tacho","📸 Photos"],label_visibility="collapsed")
    elif role=="worker": page=st.radio("",["📖 Help Guide","⚠️ Near Miss","📸 Photos","👥 My Shifts","🆘 Lone Worker","📧 Messages","✅ Tasks"],label_visibility="collapsed")
    elif role=="manager": page=st.radio("",["📖 Help Guide","🏠 Command","⚠️ Near Miss","👥 Staff","📊 Compliance","🎓 Training","📋 Reports","📧 Messages","📅 Calendar","✅ Tasks"],label_visibility="collapsed")
    else: page=st.radio("",["📖 Help Guide","⚠️ Near Miss"],label_visibility="collapsed")
    st.markdown("---")
    if st.button("Logout",use_container_width=True): st.session_state.clear();st.rerun()
    # ============================================
# 📖 HELP GUIDE
# ============================================
if page=="📖 Help Guide":
    st.markdown("<h1>📖 Enterprise Command Centre — Complete Guide</h1>",unsafe_allow_html=True);st.markdown("---")
    with st.expander("🚀 GETTING STARTED — Read This First",expanded=True):
        st.markdown("""<div class="instruction-step"><h3>1️⃣ Register Your Company</h3><p>Click <b>Register</b> tab on the login page. Enter company name, admin username and password (8+ characters).</p></div>
        <div class="instruction-step"><h3>2️⃣ Add Your Sites</h3><p>Go to <b>📍 Sites</b>. Add each location — depot, warehouse, office.</p></div>
        <div class="instruction-step"><h3>3️⃣ Add Your Team</h3><p>Go to <b>👥 Staff → ➕ Add Staff</b>. Roles: Admin, Manager, Driver, Workshop, Worker.</p></div>
        <div class="instruction-step"><h3>4️⃣ Add Your Vehicles</h3><p>Go to <b>🚛 Fleet</b>. Enter registration, type, make, model.</p></div>""",unsafe_allow_html=True)
    with st.expander("🚛 FLEET MANAGEMENT"):
        st.markdown("""<div class="instruction-step"><b>🔍 DVSA Inspection:</b> Drivers check each item. Defects auto-alert workshop.</div>
        <div class="instruction-step"><b>⏱️ Tacho Timer:</b> Start/stop driving. Tracks 4.5hr limits.</div>
        <div class="instruction-step"><b>🔧 Workshop:</b> See open defects. Mark repairs complete.</div>""",unsafe_allow_html=True)
    with st.expander("⚠️ NEAR MISS REPORTING"):
        st.markdown("""<div class="instruction-step"><b>📝 Report:</b> Describe what happened, choose severity. Photo evidence.</div>
        <div class="instruction-step"><b>🔍 Investigation:</b> 5 Whys method. Root cause analysis. Corrective actions.</div>""",unsafe_allow_html=True)
    with st.expander("🏢 OFFICE 365 SUITE"):
        st.markdown("""<div class="instruction-step"><b>📧 Messages:</b> Internal messaging between staff.</div>
        <div class="instruction-step"><b>📅 Calendar:</b> Company events and schedule.</div>
        <div class="instruction-step"><b>📁 Documents:</b> Upload and share policies, manuals.</div>
        <div class="instruction-step"><b>✅ Tasks:</b> Assign and track team tasks.</div>""",unsafe_allow_html=True)

# ============================================
# 🏠 COMMAND CENTRE
# ============================================
elif page=="🏠 Command":
    st.markdown(f"<h1>Enterprise Command Centre</h1><p style='color:#94a3b8;'>{datetime.now().strftime('%A, %d %B %Y — %H:%M')}</p>",unsafe_allow_html=True);st.markdown("---")
    ops=sq("SELECT * FROM ops WHERE company_id=? ORDER BY time DESC",(cid,));nm=sq("SELECT * FROM near_misses WHERE company_id=?",(cid,))
    vc=sq("SELECT COUNT(*) as c FROM vehicles WHERE company_id=?",(cid,)).iloc[0,0];sc=sq("SELECT COUNT(*) as c FROM users WHERE company_id=?",(cid,)).iloc[0,0]
    nc=sq("SELECT COUNT(*) as c FROM near_misses WHERE company_id=? AND status='Reported'",(cid,)).iloc[0,0]
    tc=sq("SELECT COUNT(*) as c FROM tasks WHERE company_id=? AND status!='Completed'",(cid,)).iloc[0,0]
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{Analytics.health(ops)}%</div></div>',unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">Open Near Misses</div><div class="metric-value" style="color:{"#ef4444" if nc>0 else "#10b981"};">{nc}</div></div>',unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-label">Open Tasks</div><div class="metric-value">{tc}</div></div>',unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-label">Team</div><div class="metric-value">{sc}</div></div>',unsafe_allow_html=True)
    st.markdown("---")
    col_a,col_b=st.columns(2)
    with col_a:
        st.markdown("### Recent Near Misses")
        if not nm.empty:
            for _,n in nm.head(5).iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{n["title"]}</b> — <span class="{"badge-critical" if "Critical" in str(n["severity"]) else "badge-major"}">{str(n["severity"])[:20]}</span></div>',unsafe_allow_html=True)
    with col_b:
        st.markdown("### Recent Fleet Activity")
        if not ops.empty:
            for _,r in ops.head(5).iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{r["reg"]}</b> — <span class="{"badge-pass" if r["status"]=="PASS" else "badge-vor"}">{r["status"]}</span></div>',unsafe_allow_html=True)

# ============================================
# 📧 MESSAGES
# ============================================
elif page=="📧 Messages":
    st.markdown("<h1>📧 Internal Messages</h1>",unsafe_allow_html=True);st.markdown("---")
    tab_m1,tab_m2=st.tabs(["📥 Inbox","✉️ Send"])
    with tab_m1:
        uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0]
        msgs=sq("SELECT m.*, u.full_name as sender_name FROM messages m JOIN users u ON m.sender_id=u.id WHERE m.recipient_id=? OR m.sender_id=? ORDER BY m.sent_at DESC LIMIT 30",(uid,uid))
        if not msgs.empty:
            for _,m in msgs.iterrows():
                is_mine=m['sender_id']==uid
                st.markdown(f'<div class="message-bubble {"message-mine" if is_mine else ""}"><b>{m["sender_name"]}</b> • {m["sent_at"]}<br><b>{m["subject"]}</b><br>{m["body"][:200]}</div>',unsafe_allow_html=True)
                if not is_mine and m['read']==0: db.execute("UPDATE messages SET read=1 WHERE id=?",(m['id'],))
    with tab_m2:
        with st.form("send_msg"):
            users=sq("SELECT id,full_name FROM users WHERE company_id=? AND id!=?",(cid,uid));recipient=st.selectbox("To",users['id'].tolist(),format_func=lambda x:users[users['id']==x]['full_name'].iloc[0]) if not users.empty else None
            subject=st.text_input("Subject");body=st.text_area("Message")
            if st.form_submit_button("Send",type="primary",use_container_width=True):
                if recipient and body: db.execute("INSERT INTO messages (company_id,sender_id,recipient_id,subject,body) VALUES (?,?,?,?,?)",(cid,uid,recipient,subject,body));st.success("✅ Sent!");st.rerun()

# ============================================
# 📅 CALENDAR
# ============================================
elif page=="📅 Calendar":
    st.markdown("<h1>📅 Company Calendar</h1>",unsafe_allow_html=True);st.markdown("---")
    with st.form("add_event"):
        c1,c2=st.columns(2)
        with c1: title=st.text_input("Event Title*");ed=st.date_input("Date")
        with c2: stt=st.time_input("Start",datetime.strptime("09:00","%H:%M").time());et=st.time_input("End",datetime.strptime("10:00","%H:%M").time())
        desc=st.text_area("Description")
        if st.form_submit_button("Add Event",type="primary",use_container_width=True):
            if title: db.execute("INSERT INTO calendar_events (company_id,title,description,event_date,start_time,end_time,created_by) VALUES (?,?,?,?,?,?,?)",(cid,title,desc,ed.strftime('%Y-%m-%d'),stt.strftime('%H:%M'),et.strftime('%H:%M'),st.session_state.user));st.success("✅ Added!");st.rerun()
    events=sq("SELECT * FROM calendar_events WHERE company_id=? AND event_date >= ? ORDER BY event_date LIMIT 20",(cid,datetime.now().strftime('%Y-%m-%d')))
    if not events.empty:
        for _,e in events.iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><b>{e["title"]}</b> — {e["event_date"]} {e["start_time"]}-{e["end_time"]}<br><span style="color:#94a3b8;">{e.get("description","")}</span></div>',unsafe_allow_html=True)

# ============================================
# 📁 DOCUMENTS
# ============================================
elif page=="📁 Documents":
    st.markdown("<h1>📁 Document Library</h1>",unsafe_allow_html=True);st.markdown("---")
    with st.form("upload_doc"):
        filename=st.text_input("Document Name*");desc=st.text_area("Description");file=st.file_uploader("Upload File",type=["pdf","docx","txt","csv","jpg","png"])
        if st.form_submit_button("Upload",type="primary",use_container_width=True):
            if filename and file:
                content=base64.b64encode(file.read()).decode()[:1000]
                uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0]
                db.execute("INSERT INTO documents (company_id,filename,description,uploaded_by,file_data) VALUES (?,?,?,?,?)",(cid,filename,desc,uid,content));st.success("✅ Uploaded!");st.rerun()
    docs=sq("SELECT d.*, u.full_name FROM documents d JOIN users u ON d.uploaded_by=u.id WHERE d.company_id=? ORDER BY d.uploaded_at DESC",(cid,))
    if not docs.empty:
        for _,d in docs.iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><b>📄 {d["filename"]}</b> — {d["description"]}<br><span style="color:#94a3b8;">Uploaded by {d["full_name"]} • {d["uploaded_at"]}</span></div>',unsafe_allow_html=True)

# ============================================
# ✅ TASKS
# ============================================
elif page=="✅ Tasks":
    st.markdown("<h1>✅ Task Manager</h1>",unsafe_allow_html=True);st.markdown("---")
    with st.form("add_task"):
        c1,c2=st.columns(2)
        with c1: title=st.text_input("Task Title*");priority=st.selectbox("Priority",["Low","Normal","High","Urgent"])
        with c2: users=sq("SELECT id,full_name FROM users WHERE company_id=?",(cid,));assign_to=st.selectbox("Assign To",users['id'].tolist(),format_func=lambda x:users[users['id']==x]['full_name'].iloc[0]) if not users.empty else None;due=st.date_input("Due Date")
        desc=st.text_area("Description")
        uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0]
        if st.form_submit_button("Create Task",type="primary",use_container_width=True):
            if title: db.execute("INSERT INTO tasks (company_id,title,description,assigned_to,assigned_by,priority,due_date) VALUES (?,?,?,?,?,?,?)",(cid,title,desc,assign_to,uid,priority,due.strftime('%Y-%m-%d')));st.success("✅ Created!");st.rerun()
    my_uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0]
    tasks=sq("SELECT t.*, u.full_name as assigned_name FROM tasks t JOIN users u ON t.assigned_to=u.id WHERE t.company_id=? AND (t.assigned_to=? OR t.assigned_by=?) ORDER BY t.created_at DESC",(cid,my_uid,my_uid))
    if not tasks.empty:
        for _,t in tasks.iterrows():
            done=t['status']=='Completed'
            st.markdown(f'<div class="glass-card {"task-done" if done else "task-pending"}" style="margin-bottom:6px;padding:12px;"><b>{"✅" if done else "⏳"} {t["title"]}</b> — {t["priority"]} — Due: {t["due_date"]}<br><span style="color:#94a3b8;">Assigned to: {t["assigned_name"]}</span></div>',unsafe_allow_html=True)
            if not done:
                if st.button(f"✅ Complete #{t['id']}",key=f"task_{t['id']}"): db.execute("UPDATE tasks SET status='Completed',completed_at=? WHERE id=?",(datetime.now(),t['id']));st.success("✅ Done!");st.rerun()

# ============================================
# 🚛 FLEET
# ============================================
elif page=="🚛 Fleet":
    st.markdown("<h1>🚛 Fleet Registry</h1>",unsafe_allow_html=True);st.markdown("---")
    veh=sq("SELECT * FROM vehicles WHERE company_id=?",(cid,));cv,ca=st.columns([2,1])
    with cv:
        if not veh.empty:
            for _,v in veh.iterrows():
                with st.expander(f"🚛 {v['reg']} — {v.get('type','N/A')}"): st.write(f"Type: {v.get('type','N/A')} | Make: {v.get('make','N/A')}")
    with ca:
        with st.form("add_v"): reg=st.text_input("Reg*").upper();t=st.selectbox("Type*",["HGV Artic","HGV Rigid","Van","Car"]);make=st.text_input("Make");model=st.text_input("Model")
            if st.form_submit_button("Add",type="primary",use_container_width=True):
                if reg:
                    try: c=get_db();c.execute("INSERT INTO vehicles (reg,type,make,model,company_id) VALUES (?,?,?,?,?)",(reg,t,make,model,cid));c.commit();c.close();st.success(f"✅ {reg} added!");st.rerun()
                    except: st.error("Exists")

# ============================================
# 👥 STAFF
# ============================================
elif page=="👥 Staff":
    st.markdown("<h1>👥 Staff Management</h1>",unsafe_allow_html=True)
    staff=sq("SELECT * FROM users WHERE company_id=?",(cid,))
    if not staff.empty: st.dataframe(staff[['username','full_name','role','email']],use_container_width=True,hide_index=True)
    with st.form("add_staff"): c1,c2=st.columns(2)
        with c1: nu=st.text_input("Username*");nf=st.text_input("Full Name")
        with c2: np=st.text_input("Password*",type="password");nr=st.selectbox("Role*",["worker","driver","workshop","manager"])
        if st.form_submit_button("Add",type="primary",use_container_width=True):
            if nu and np and len(np)>=8:
                try: c=get_db();c.execute("INSERT INTO users (username,password,role,full_name,company_id) VALUES (?,?,?,?,?)",(nu,Security.hash(np),nr,nf,cid));c.commit();c.close();st.success(f"✅ {nu} added!");st.rerun()
                except: st.error("Username exists")

# ============================================
# ⚠️ NEAR MISS
# ============================================
elif page=="⚠️ Near Miss":
    st.markdown("<h1>⚠️ Near Miss Reporting</h1>",unsafe_allow_html=True);st.markdown("---")
    with st.form("near_miss"): title=st.text_input("Title*");desc=st.text_area("Description*");cat=st.selectbox("Category*",NEAR_MISS_CATEGORIES);sev=st.selectbox("Severity*",SEVERITY_LEVELS);reporter=st.text_input("Reporter*",value=st.session_state.user)
        if st.form_submit_button("Submit",type="primary",use_container_width=True):
            if title and desc: db.execute("INSERT INTO near_misses (company_id,reporter,title,description,severity,category) VALUES (?,?,?,?,?,?)",(cid,reporter,title,desc,sev,cat));st.success("✅ Reported!");st.rerun()
    nm=sq("SELECT * FROM near_misses WHERE company_id=? ORDER BY reported_at DESC",(cid,))
    if not nm.empty:
        for _,n in nm.head(20).iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{n["title"]}</b> — <span class="{"badge-critical" if "Critical" in str(n["severity"]) else "badge-major"}">{str(n["severity"])[:20]}</span></div>',unsafe_allow_html=True)

# ============================================
# 📍 SITES
# ============================================
elif page=="📍 Sites":
    st.markdown("<h1>📍 Sites</h1>",unsafe_allow_html=True)
    sites=sq("SELECT * FROM sites WHERE company_id=?",(cid,))
    if not sites.empty:
        for _,s in sites.iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{s["name"]}</b> — {s.get("address","N/A")}</div>',unsafe_allow_html=True)
    with st.form("add_site"): sn=st.text_input("Site Name*");sa=st.text_input("Address")
        if st.form_submit_button("Add",type="primary",use_container_width=True):
            if sn: db.execute("INSERT INTO sites (company_id,name,address) VALUES (?,?,?)",(cid,sn,sa));st.success("✅ Added!");st.rerun()

# ============================================
# 🗺️ MAP
# ============================================
elif page=="🗺️ Map":
    st.markdown("<h1>🗺️ Map</h1>",unsafe_allow_html=True)
    vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,))
    if not vehs.empty:
        pos=[Analytics.gen_gps(v['reg']) for _,v in vehs.iterrows()];df=pd.DataFrame(pos);df['reg']=vehs['reg'].tolist()
        fig=go.Figure()
        for _,v in df.iterrows(): fig.add_trace(go.Scattermapbox(lat=[v['lat']],lon=[v['lon']],mode='markers+text',marker=dict(size=14,color='#3b82f6'),text=v['reg']))
        fig.update_layout(mapbox=dict(style='carto-darkmatter',center=dict(lat=51.5,lon=-0.1),zoom=9),height=500,margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig,use_container_width=True)

# ============================================
# 🔧 WORKSHOP
# ============================================
elif page=="🔧 Workshop":
    st.markdown("<h1>🔧 Workshop</h1>",unsafe_allow_html=True)
    defects=sq("SELECT * FROM ops WHERE company_id=? AND status!='PASS' AND status!='REPAIRED' ORDER BY time DESC",(cid,))
    if not defects.empty:
        for _,d in defects.iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{d["reg"]}</b> — {d["status"]}<br>{str(d["notes"])[:100]}</div>',unsafe_allow_html=True)
    with st.form("repair"): vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"]);rn=st.text_area("Repair Notes")
        if st.form_submit_button("Mark Repaired",type="primary",use_container_width=True):
            c=get_db();c.execute("INSERT INTO ops (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,0,'REPAIRED',?,?,?)",(datetime.now(),reg,rn,st.session_state.user,cid));c.commit();c.close();st.success("✅ Repaired!");st.rerun()

# ============================================
# 💰 JOBS
# ============================================
elif page=="💰 Jobs":
    st.markdown("<h1>💰 Jobs & Invoices</h1>",unsafe_allow_html=True)
    with st.form("new_job"): cn=st.text_input("Customer*");de=st.text_area("Description*");qa=st.number_input("Quote (£)",0.0,100000.0,0.0)
        if st.form_submit_button("Create",type="primary",use_container_width=True):
            if cn and de: db.execute("INSERT INTO jobs (company_id,customer_name,description,quoted_amount) VALUES (?,?,?,?)",(cid,cn,de,qa));st.success("✅ Created!");st.rerun()
    jobs=sq("SELECT * FROM jobs WHERE company_id=? ORDER BY created_at DESC",(cid,))
    if not jobs.empty:
        for _,j in jobs.iterrows():
            with st.expander(f"{j['customer_name']} — £{j['quoted_amount']:,.2f}"):
                if j['status']!='Completed' and st.button(f"Complete #{j['id']}",key=f"j{j['id']}"): db.execute("UPDATE jobs SET status='Completed' WHERE id=?",(j['id'],));total=round(j['quoted_amount']*1.2,2);db.execute("INSERT INTO invoices (company_id,job_id,customer_name,total,status,due_date) VALUES (?,?,?,?,'Unpaid',?)",(cid,j['id'],j['customer_name'],total,(datetime.now()+timedelta(days=30)).strftime('%Y-%m-%d')));st.success("✅ Invoiced!");st.rerun()

# ============================================
# ⛽ FUEL
# ============================================
elif page=="⛽ Fuel":
    st.markdown("<h1>⛽ Fuel</h1>",unsafe_allow_html=True)
    with st.form("fuel"): vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"]);lit=st.number_input("Litres",0.0,1000.0,0.0);cost=st.number_input("Cost (£)",0.0,10000.0,0.0);mil=st.number_input("Mileage",0,999999,0)
        if st.form_submit_button("Log",type="primary",use_container_width=True): db.execute("INSERT INTO fuel_log (company_id,vehicle_reg,date,litres,cost,mileage,driver) VALUES (?,?,?,?,?,?,?)",(cid,reg,datetime.now().strftime('%Y-%m-%d'),lit,cost,mil,st.session_state.user));st.success("✅ Logged!");st.rerun()

# ============================================
# 🔔 MAINTENANCE
# ============================================
elif page=="🔔 Maintenance":
    st.markdown("<h1>🔔 Maintenance</h1>",unsafe_allow_html=True)
    with st.form("maint"): vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"]);stp=st.selectbox("Type",["Oil Change","Brake Service","MOT","Annual Service"]);dd=st.date_input("Due Date")
        if st.form_submit_button("Schedule",type="primary",use_container_width=True): db.execute("INSERT INTO maintenance (company_id,vehicle_reg,service_type,due_date) VALUES (?,?,?,?)",(cid,reg,stp,dd.strftime('%Y-%m-%d')));st.success("✅ Scheduled!");st.rerun()

# ============================================
# 🔍 INSPECTION
# ============================================
elif page=="🔍 Inspection":
    st.markdown("<h1>🔍 DVSA Walkaround</h1>",unsafe_allow_html=True);st.markdown("---")
    vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,))
    if vehs.empty: st.warning("No vehicles");st.stop()
    with st.form("insp"):
        reg=st.selectbox("Vehicle",vehs['reg'].tolist());mil=st.number_input("Mileage",0,step=1000)
        chk={}
        for cat,items in DVSA.items():
            st.markdown(f"**{cat}**");cs=st.columns(3)
            for i,it in enumerate(items):
                with cs[i%3]: chk[it]=st.checkbox(it,value=True)
        ok=all(chk.values());nt=""
        if not ok: fl=[i for i,c in chk.items() if not c];st.error(f"Defects: {', '.join(fl)}");nt=st.text_area("Description*",height=100);sv=st.selectbox("Severity*",["Minor","Major","VOR"])
        sg=st.text_input("Signature*")
        if st.form_submit_button("Submit",type="primary",use_container_width=True):
            if not ok and not nt: st.error("Description required")
            elif not sg: st.error("Signature required")
            else:
                sts="PASS" if ok else f"DEFECT - {sv}"
                c=get_db();c.execute("INSERT INTO ops (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,?,?,?,?,?)",(datetime.now(),reg,mil,sts,nt or "Passed",st.session_state.user,cid));c.commit();c.close()
                if ok: st.success("PASS!");st.balloons()
                else: st.warning("Defect logged")
                time.sleep(2);st.rerun()

# ============================================
# ⏱️ TACHO
# ============================================
elif page=="⏱️ Tacho":
    st.markdown("<h1>⏱️ Tacho</h1>",unsafe_allow_html=True)
    s=tacho.status()
    c1,c2,c3=st.columns(3)
    with c1: h=int(s['total'].total_seconds()//3600);m=int((s['total'].total_seconds()%3600)//60);st.markdown(f'<div class="tacho-display"><div class="tacho-label">DRIVING</div><div class="tacho-time">{h:02d}:{m:02d}</div></div>',unsafe_allow_html=True)
    with c2: bh=int(s['until_break'].total_seconds()//3600);bm=int((s['until_break'].total_seconds()%3600)//60);st.markdown(f'<div class="tacho-display"><div class="tacho-label">BREAK IN</div><div class="tacho-time">{bh:02d}:{bm:02d}</div></div>',unsafe_allow_html=True)
    with c3: dh=int(max(timedelta(0),s['day_left']).total_seconds()//3600);dm=int((max(timedelta(0),s['day_left']).total_seconds()%3600)//60);st.markdown(f'<div class="tacho-display"><div class="tacho-label">DAY LEFT</div><div class="tacho-time">{dh:02d}:{dm:02d}</div></div>',unsafe_allow_html=True)
    if s['warning']: st.error(s['warning'])
    cc1,cc2=st.columns(2)
    with cc1:
        if not s['driving']:
            if st.button("🟢 Start",type="primary",use_container_width=True): tacho.start();st.rerun()
        else:
            if st.button("🔴 Stop",use_container_width=True): tacho.stop();st.rerun()
    with cc2:
        if st.button("🌙 Reset",use_container_width=True): tacho.stop();st.session_state.td=timedelta(0);st.rerun()

# ============================================
# 📸 PHOTOS
# ============================================
elif page=="📸 Photos": st.markdown("<h1>📸 Photos</h1>",unsafe_allow_html=True);st.camera_input("Take photo");st.button("Save")

# ============================================
# 🏆 SAFETY LEAGUE
# ============================================
elif page=="🏆 Safety League":
    st.markdown("<h1>🏆 Safety League</h1>",unsafe_allow_html=True)
    nm=sq("SELECT reporter, COUNT(*) as reports FROM near_misses WHERE company_id=? GROUP BY reporter ORDER BY reports",(cid,))
    if not nm.empty:
        for i,(_,r) in enumerate(nm.iterrows()): st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;">{{0:"🥇",1:"🥈",2:"🥉"}.get(i,f"#{i+1}")} <b>{r["reporter"]}</b> — {r["reports"]} reports</div>',unsafe_allow_html=True)

# ============================================
# 🎓 TRAINING
# ============================================
elif page=="🎓 Training":
    st.markdown("<h1>🎓 Training</h1>",unsafe_allow_html=True)
    training=sq("SELECT * FROM training WHERE company_id=?",(cid,))
    if not training.empty:
        for _,t in training.iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{t["title"]}</b></div>',unsafe_allow_html=True)
    with st.form("add_training"): title=st.text_input("Course Title*");desc=st.text_area("Description")
        if st.form_submit_button("Add",type="primary",use_container_width=True):
            if title: db.execute("INSERT INTO training (company_id,title,description) VALUES (?,?,?)",(cid,title,desc));st.success("✅ Added!");st.rerun()

# ============================================
# 📋 FORMS
# ============================================
elif page=="📋 Forms":
    st.markdown("<h1>📋 Forms</h1>",unsafe_allow_html=True)
    with st.form("new_form"): fn=st.text_input("Form Name*");fields=st.text_area("Fields (one per line)")
        if st.form_submit_button("Create",type="primary",use_container_width=True):
            if fn: db.execute("INSERT INTO custom_forms (company_id,form_name,form_fields) VALUES (?,?,?)",(cid,fn,fields));st.success("✅ Created!");st.rerun()

# ============================================
# 🆘 LONE WORKER
# ============================================
elif page=="🆘 Lone Worker":
    st.markdown("<h1>🆘 Lone Worker</h1>",unsafe_allow_html=True)
    st.button("✅ Check In — I'm Safe",type="primary",use_container_width=True)
    st.button("🚨 EMERGENCY — SEND HELP",type="secondary",use_container_width=True)

# ============================================
# 📊 COMPLIANCE
# ============================================
elif page=="📊 Compliance":
    st.markdown("<h1>📊 Compliance</h1>",unsafe_allow_html=True)
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,));nm=sq("SELECT * FROM near_misses WHERE company_id=?",(cid,))
    c1,c2=st.columns(2)
    with c1: st.metric("Fleet Pass Rate",f"{Analytics.health(ops)}%")
    with c2: st.metric("Near Misses (30d)",len(nm[nm['reported_at']>str(datetime.now()-timedelta(days=30))]) if not nm.empty else 0)

# ============================================
# 🤖 AI
# ============================================
elif page=="🤖 AI":
    st.markdown("<h1>🤖 AI Analysis</h1>",unsafe_allow_html=True)
    prompt=st.text_area("Ask AI","Analyze safety trends")
    if st.button("Run AI",type="primary"): st.info(ai_analyze(prompt))

# ============================================
# 📋 REPORTS
# ============================================
elif page=="📋 Reports":
    st.markdown("<h1>📋 Reports</h1>",unsafe_allow_html=True)
    nm=sq("SELECT * FROM near_misses WHERE company_id=?",(cid,));ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,))
    if not nm.empty: st.download_button("📊 Near Miss CSV",nm.to_csv(index=False),"near_misses.csv")
    if not ops.empty: st.download_button("📊 Fleet CSV",ops.to_csv(index=False),"fleet_ops.csv")

# ============================================
# ⚙️ SETTINGS
# ============================================
elif page=="⚙️ Settings":
    st.markdown("<h1>⚙️ Settings</h1>",unsafe_allow_html=True)
    with st.form("pwd"): cur=st.text_input("Current",type="password");new=st.text_input("New",type="password")
        if st.form_submit_button("Update",type="primary"):
            if cur and new and len(new)>=8:
                c=get_db();r=c.execute("SELECT password FROM users WHERE username=? AND company_id=?",(st.session_state.user,cid)).fetchone()
                if r and Security.verify(cur,r[0]): c.execute("UPDATE users SET password=? WHERE username=? AND company_id=?",(Security.hash(new),st.session_state.user,cid));c.commit();st.success("✅ Done!")
                else: st.error("Wrong password")
                c.close()

# ============================================
# 👥 MY SHIFTS
# ============================================
elif page=="👥 My Shifts":
    st.markdown("<h1>👥 My Shifts</h1>",unsafe_allow_html=True)
    uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,))
    if not uid.empty:
        shifts=sq("SELECT * FROM shifts WHERE user_id=? ORDER BY shift_date DESC LIMIT 20",(uid.iloc[0,0],))
        if not shifts.empty:
            for _,s in shifts.iterrows(): st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{s["shift_date"]}</b> — {s["start_time"]} to {s["end_time"]}</div>',unsafe_allow_html=True)
    st.button("🟢 Clock In",type="primary",use_container_width=True)
    st.button("🔴 Clock Out",use_container_width=True)

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748b;">🏢 Enterprise Command Centre • Fleet • Staff • Safety • Office Suite • PWA Ready</div>',unsafe_allow_html=True)
