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

st.set_page_config(page_title="Enterprise Command Centre | Fleet • Staff • Safety", layout="wide", page_icon="🏢", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(145deg, #0a0e27 0%, #1a1040 100%); background-attachment: fixed; }
.glass-card { background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)); backdrop-filter: blur(30px); border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; padding: 24px; transition: all 0.3s ease; }
.glass-card:hover { border-color: rgba(59,130,246,0.3); box-shadow: 0 20px 60px rgba(0,0,0,0.4); }
.metric-card { background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.06)); border: 1px solid rgba(59,130,246,0.15); border-radius: 18px; padding: 24px; position: relative; overflow: hidden; }
.metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
.metric-value { font-size: 2.5em; font-weight: 900; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 8px 0; }
.metric-label { color: #94a3b8; font-size: 0.75em; font-weight: 500; text-transform: uppercase; letter-spacing: 3px; }
.badge-pass { background: #10b981; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-minor { background: #f59e0b; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-major { background: #ef4444; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; }
.badge-vor { background: #7c3aed; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; animation: pulse 2s infinite; }
.badge-critical { background: #dc2626; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 0.85em; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.7; } }
.stButton > button { border-radius: 14px; font-weight: 600; border: none; background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; padding: 14px 28px; }
.stButton > button:hover { transform: translateY(-3px); box-shadow: 0 15px 35px rgba(59,130,246,0.4); }
.stTextInput > div > div > input, .stSelectbox > div > div > select, .stTextArea > div > div > textarea { border-radius: 14px; border: 2px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); color: white; }
[data-testid="stSidebar"] { background: rgba(10,14,39,0.97); border-right: 1px solid rgba(255,255,255,0.04); }
h1 { font-weight: 900; letter-spacing: -1px; }
.tacho-display { background: #000; border: 3px solid #3b82f6; border-radius: 20px; padding: 20px; text-align: center; }
.tacho-time { font-size: 3em; font-weight: 900; color: #10b981; font-family: 'Courier New', monospace; }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATABASE
# ============================================
DB_PATH = Path(__file__).parent / "enterprise.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH)); conn.row_factory = sqlite3.Row; return conn

conn = get_db()
# Core
conn.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, branding_color DEFAULT '#3b82f6', email_alerts TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'worker', full_name TEXT, phone TEXT, email TEXT, company_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
# Sites
conn.execute("CREATE TABLE IF NOT EXISTS sites (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, name TEXT, address TEXT, manager TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
# Fleet
conn.execute("CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT, type TEXT, make TEXT, model TEXT, fleet_number TEXT, site_id INTEGER, company_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(reg, company_id))")
conn.execute("CREATE TABLE IF NOT EXISTS ops (id INTEGER PRIMARY KEY AUTOINCREMENT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reg TEXT, mileage REAL, status TEXT, notes TEXT, driver TEXT, company_id INTEGER)")
# Staff
conn.execute("CREATE TABLE IF NOT EXISTS shifts (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, site_id INTEGER, shift_date DATE, start_time TEXT, end_time TEXT, clock_in TIMESTAMP, clock_out TIMESTAMP, status TEXT DEFAULT 'Scheduled')")
conn.execute("CREATE TABLE IF NOT EXISTS certifications (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, cert_name TEXT, expiry_date DATE, status TEXT DEFAULT 'Valid')")
# Near Miss
conn.execute("CREATE TABLE IF NOT EXISTS near_misses (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, site_id INTEGER, reporter TEXT, title TEXT, description TEXT, severity TEXT, category TEXT, location TEXT, photo_data TEXT, investigation TEXT, corrective_action TEXT, status TEXT DEFAULT 'Reported', reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
# Jobs
conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, customer_name TEXT, description TEXT, status DEFAULT 'Pending', quoted_amount REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, job_id INTEGER, customer_name TEXT, total REAL, status DEFAULT 'Unpaid', due_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
# Maintenance
conn.execute("CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, vehicle_reg TEXT, service_type TEXT, due_date DATE, status DEFAULT 'Scheduled', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
# Fuel
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

# ============================================
# ENGINES
# ============================================
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
            json={"model":"gpt-4o-mini","messages":[{"role":"system","content":"Safety expert. Analyze and advise concisely."},{"role":"user","content":prompt}],"max_tokens":200},timeout=10)
        return r.json()["choices"][0]["message"]["content"]
    except: return "AI unavailable"

class Analytics:
    @staticmethod
    def health(df):
        if df.empty: return 100.0
        t=len(df);vor=len(df[df['status'].str.contains('VOR|Dangerous',case=False,na=False)]);maj=len(df[df['status'].str.contains('Major',case=False,na=False)])
        return round(max(0,100-((vor*35+maj*15)/max(t,1))),1)
    @staticmethod
    def near_miss_trend(df):
        if df.empty: return pd.DataFrame()
        df['date']=pd.to_datetime(df['reported_at']).dt.date
        return df.groupby('date').size().reset_index(name='count')
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

DVSA = {
    "Structure":["Cab undamaged","Body panels secure","Doors working","Steps secure"],
    "Visibility":["Windscreen clear","Wipers OK","Mirrors clean"],
    "Lighting":["Headlights","Side lights","Indicators","Brake lights"],
    "Tyres":["Tread legal","No cuts","Wheel nuts present"],
    "Brakes":["Service brake OK","Parking holds","No leaks"],
    "Engine":["Oil correct","Coolant correct","No leaks"],
    "Safety":["Seatbelts","Horn","Extinguisher","First aid"],
    "Load":["Load distributed","Load secured","Doors locked"]
}

NEAR_MISS_CATEGORIES = ["Slip/Trip/Fall","Vehicle/Plant","Manual Handling","Working at Height","Electrical","Fire/Explosion","Chemical Spill","Equipment Failure","Structural","Other"]
SEVERITY_LEVELS = ["Low — Near Miss","Medium — Minor Injury Possible","High — Serious Injury Possible","Critical — Fatality Risk"]

tacho = TachoEngine()

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False;st.session_state.user=None;st.session_state.role=None;st.session_state.cid=None

# ============================================
# AUTH
# ============================================
if not st.session_state.logged_in:
    c1,c2,c3=st.columns([1,2.5,1])
    with c2:
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;margin-bottom:40px;"><div style="font-size:4em;">🏢</div><h1 style="font-size:3em;font-weight:900;margin:0;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Enterprise Command</h1><p style="color:#94a3b8;font-size:1.1em;">FLEET • STAFF • SAFETY • NEAR MISS</p></div>""",unsafe_allow_html=True)
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
                            st.success("✅ Deployed! Go to Login.")
                        except: st.error("Company/username exists")
    st.stop()

cid=st.session_state.cid;role=st.session_state.role

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown('<div style="text-align:center;"><h3 style="font-weight:900;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🏢 Enterprise</h3></div>',unsafe_allow_html=True)
    st.markdown(f"**{st.session_state.user}** ({role.upper()})")
    
    if role=="admin":
        page=st.radio("",[
            "🏠 Command","🚛 Fleet","👥 Staff","⚠️ Near Miss","📍 Sites",
            "🔧 Workshop","💰 Jobs","⛽ Fuel","🔔 Maintenance","🔍 Inspection",
            "⏱️ Tacho","📸 Photos","🏆 Safety League","📊 Compliance","🤖 AI","📋 Reports","⚙️ Settings"
        ],label_visibility="collapsed")
    elif role=="driver": page=st.radio("",["🔍 Inspection","⏱️ Tacho","📸 Photos"],label_visibility="collapsed")
    elif role=="workshop": page=st.radio("",["🔧 Workshop","🔔 Maintenance"],label_visibility="collapsed")
    elif role=="worker": page=st.radio("",["⚠️ Near Miss","📸 Photos","👥 My Shifts"],label_visibility="collapsed")
    elif role=="manager": page=st.radio("",["🏠 Command","⚠️ Near Miss","👥 Staff","📊 Compliance","📋 Reports"],label_visibility="collapsed")
    else: page=st.radio("",["⚠️ Near Miss"],label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("Logout",use_container_width=True): st.session_state.clear();st.rerun()

def sq(sql,p=None):
    try: return db.query(sql,p)
    except: return pd.DataFrame()

# ============================================
# 🏠 COMMAND CENTRE
# ============================================
if page=="🏠 Command":
    st.markdown(f"<h1>Enterprise Command Centre</h1><p style='color:#94a3b8;'>{datetime.now().strftime('%A, %d %B %Y — %H:%M')}</p>",unsafe_allow_html=True);st.markdown("---")
    
    ops=sq("SELECT * FROM ops WHERE company_id=? ORDER BY time DESC",(cid,))
    nm=sq("SELECT * FROM near_misses WHERE company_id=? ORDER BY reported_at DESC",(cid,))
    vc=sq("SELECT COUNT(*) as c FROM vehicles WHERE company_id=?",(cid,)).iloc[0,0]
    sc=sq("SELECT COUNT(*) as c FROM users WHERE company_id=?",(cid,)).iloc[0,0]
    nc=sq("SELECT COUNT(*) as c FROM near_misses WHERE company_id=? AND status='Reported'",(cid,)).iloc[0,0]
    sites=sq("SELECT COUNT(*) as c FROM sites WHERE company_id=?",(cid,)).iloc[0,0]
    
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{Analytics.health(ops)}%</div></div>',unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">Open Near Misses</div><div class="metric-value" style="color:{'#ef4444' if nc>0 else '#10b981'};">{nc}</div></div>',unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-label">Sites</div><div class="metric-value">{sites}</div></div>',unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-label">Team</div><div class="metric-value">{sc}</div></div>',unsafe_allow_html=True)
    
    st.markdown("---")
    col_a,col_b=st.columns(2)
    with col_a:
        st.markdown("### Recent Near Misses")
        if not nm.empty:
            for _,n in nm.head(5).iterrows():
                sev="badge-critical" if 'Critical' in str(n['severity']) else "badge-major" if 'High' in str(n['severity']) else "badge-minor"
                st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{n["title"]}</b> — {n["site_id"]} — <span class="{sev}">{n["severity"][:20]}</span></div>',unsafe_allow_html=True)
        else: st.info("No near misses reported")
    with col_b:
        st.markdown("### Recent Fleet Activity")
        if not ops.empty:
            for _,r in ops.head(5).iterrows():
                b="badge-pass" if r['status']=='PASS' else ("badge-vor" if 'VOR' in str(r['status']) else "badge-major")
                st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{r["reg"]}</b> — {r["driver"]} — <span class="{b}">{r["status"]}</span></div>',unsafe_allow_html=True)

# ============================================
# 🚛 FLEET
# ============================================
elif page=="🚛 Fleet":
    st.markdown("<h1>🚛 Fleet Registry</h1>",unsafe_allow_html=True);st.markdown("---")
    veh=sq("SELECT * FROM vehicles WHERE company_id=? ORDER BY created_at DESC",(cid,))
    cv,ca=st.columns([2,1])
    with cv:
        if not veh.empty:
            for _,v in veh.iterrows():
                with st.expander(f"🚛 {v['reg']} — {v.get('type','N/A')}"):
                    st.write(f"Type: {v.get('type','N/A')} | Make: {v.get('make','N/A')} | Fleet #: {v.get('fleet_number','N/A')}")
    with ca:
        with st.form("add_v"):
            reg=st.text_input("Registration*").upper();t=st.selectbox("Type*",["HGV Artic","HGV Rigid","Van","Car","Trailer","Bus"]);make=st.text_input("Make");model=st.text_input("Model");fn=st.text_input("Fleet Number")
            if st.form_submit_button("Add",type="primary",use_container_width=True):
                if reg:
                    try:
                        c=get_db();c.execute("INSERT INTO vehicles (reg,type,make,model,fleet_number,company_id) VALUES (?,?,?,?,?,?)",(reg,t,make,model,fn,cid));c.commit();c.close()
                        st.success(f"✅ {reg} added!");st.rerun()
                    except: st.error("Already registered")

# ============================================
# 👥 STAFF
# ============================================
elif page=="👥 Staff":
    st.markdown("<h1>👥 Staff Management</h1>",unsafe_allow_html=True);st.markdown("---")
    
    tab_s1,tab_s2,tab_s3,tab_s4=st.tabs(["📋 Staff List","📅 Shifts","🎓 Certifications","➕ Add Staff"])
    
    with tab_s1:
        staff=sq("SELECT * FROM users WHERE company_id=? ORDER BY created_at DESC",(cid,))
        if not staff.empty: st.dataframe(staff[['username','full_name','role','phone','email','created_at']],use_container_width=True,hide_index=True)
        else: st.info("No staff registered")
    
    with tab_s2:
        st.markdown("### Shift Schedule")
        shifts=sq("SELECT shifts.*, users.full_name, sites.name as site_name FROM shifts JOIN users ON shifts.user_id=users.id LEFT JOIN sites ON shifts.site_id=sites.id WHERE shifts.company_id=? ORDER BY shift_date DESC LIMIT 30",(cid,))
        if not shifts.empty: st.dataframe(shifts[['full_name','site_name','shift_date','start_time','end_time','status']],use_container_width=True)
        
        with st.form("add_shift"):
            st.markdown("### Add Shift")
            users=sq("SELECT id,full_name FROM users WHERE company_id=?",(cid,))
            sites=sq("SELECT id,name FROM sites WHERE company_id=?",(cid,))
            uid=st.selectbox("Staff Member",users['id'].tolist(),format_func=lambda x:users[users['id']==x]['full_name'].iloc[0] if not users.empty else "None")
            sid=st.selectbox("Site",sites['id'].tolist(),format_func=lambda x:sites[sites['id']==x]['name'].iloc[0] if not sites.empty else "None") if not sites.empty else st.selectbox("Site",["None"])
            sd=st.date_input("Shift Date");st_time=st.time_input("Start Time",datetime.strptime("08:00","%H:%M").time());et_time=st.time_input("End Time",datetime.strptime("17:00","%H:%M").time())
            if st.form_submit_button("Schedule Shift",type="primary",use_container_width=True):
                db.execute("INSERT INTO shifts (company_id,user_id,site_id,shift_date,start_time,end_time) VALUES (?,?,?,?,?,?)",(cid,uid,sid if not sites.empty else None,sd.strftime('%Y-%m-%d'),st_time.strftime('%H:%M'),et_time.strftime('%H:%M')))
                st.success("✅ Shift scheduled!");st.rerun()
    
    with tab_s3:
        certs=sq("SELECT certifications.*, users.full_name FROM certifications JOIN users ON certifications.user_id=users.id WHERE certifications.company_id=? ORDER BY expiry_date",(cid,))
        if not certs.empty:
            for _,c in certs.iterrows():
                expired=datetime.strptime(c['expiry_date'],'%Y-%m-%d')<datetime.now() if c['expiry_date'] else False
                cl='#ef4444' if expired else '#10b981'
                st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{c["full_name"]}</b> — {c["cert_name"]} — Expires: {c["expiry_date"]} <span style="color:{cl};">{"EXPIRED" if expired else "Valid"}</span></div>',unsafe_allow_html=True)
        
        with st.form("add_cert"):
            users=sq("SELECT id,full_name FROM users WHERE company_id=?",(cid,))
            uid=st.selectbox("Staff Member",users['id'].tolist(),format_func=lambda x:users[users['id']==x]['full_name'].iloc[0] if not users.empty else "None",key="cert_user")
            cn=st.text_input("Certification Name")
            ed=st.date_input("Expiry Date")
            if st.form_submit_button("Add Certification",type="primary",use_container_width=True):
                if cn: db.execute("INSERT INTO certifications (company_id,user_id,cert_name,expiry_date) VALUES (?,?,?,?)",(cid,uid,cn,ed.strftime('%Y-%m-%d')));st.success("✅ Added!");st.rerun()
    
    with tab_s4:
        with st.form("add_staff"):
            c1,c2=st.columns(2)
            with c1: nu=st.text_input("Username*");nf=st.text_input("Full Name")
            with c2: np=st.text_input("Password*",type="password");nr=st.selectbox("Role*",["worker","driver","workshop","manager"])
            ne=st.text_input("Email");nph=st.text_input("Phone")
            if st.form_submit_button("Add Staff Member",type="primary",use_container_width=True):
                if nu and np and len(np)>=8:
                    try:
                        c=get_db();c.execute("INSERT INTO users (username,password,role,full_name,email,phone,company_id) VALUES (?,?,?,?,?,?,?)",(nu,Security.hash(np),nr,nf,ne,nph,cid));c.commit();c.close()
                        st.success(f"✅ {nu} added!");st.rerun()
                    except: st.error("Username exists")

# ============================================
# ⚠️ NEAR MISS
# ============================================
elif page=="⚠️ Near Miss":
    st.markdown("<h1>⚠️ Near Miss Reporting</h1><p style='color:#94a3b8;'>HSE-compliant incident reporting & investigation</p>",unsafe_allow_html=True);st.markdown("---")
    
    tab_n1,tab_n2,tab_n3=st.tabs(["📝 Report","📊 Dashboard","🔍 Investigation"])
    
    with tab_n1:
        with st.form("near_miss"):
            sites=sq("SELECT id,name FROM sites WHERE company_id=?",(cid,))
            sid=st.selectbox("Site/Location*",sites['id'].tolist(),format_func=lambda x:sites[sites['id']==x]['name'].iloc[0]) if not sites.empty else st.selectbox("Site/Location*",["Main Site"])
            title=st.text_input("Incident Title*",placeholder="e.g., Forklift nearly struck pedestrian")
            desc=st.text_area("Description*",placeholder="Describe exactly what happened, who was involved, what prevented injury...")
            cat=st.selectbox("Category*",NEAR_MISS_CATEGORIES)
            sev=st.selectbox("Potential Severity*",SEVERITY_LEVELS)
            loc=st.text_input("Exact Location",placeholder="e.g., Warehouse Bay 3, Loading Dock A")
            photo=st.camera_input("Photo Evidence")
            reporter=st.text_input("Reported By*",value=st.session_state.user)
            
            if st.form_submit_button("🚨 Submit Near Miss Report",type="primary",use_container_width=True):
                if title and desc and reporter:
                    photo_data=None
                    if photo:
                        img=Image.open(photo);buf=BytesIO();img.save(buf,format="PNG");photo_data=base64.b64encode(buf.getvalue()).decode()[:500]
                    db.execute("INSERT INTO near_misses (company_id,site_id,reporter,title,description,severity,category,location,photo_data) VALUES (?,?,?,?,?,?,?,?,?)",(cid,sid if not sites.empty else None,reporter,title,desc,sev,cat,loc,photo_data))
                    st.success("✅ Near miss reported! HSE manager notified.")
                    if 'Critical' in sev:
                        st.error("🚨 CRITICAL — Immediate investigation required!")
                        if OPENAI_API_KEY:
                            with st.spinner("AI analysing..."): st.info(f"🤖 AI Assessment:\n\n{ai_analyze(f'Analyze this near miss: {title}. {desc}. Severity: {sev}')}")
                    st.rerun()
                else: st.error("Title, description, and reporter required")
    
    with tab_n2:
        nm=sq("SELECT * FROM near_misses WHERE company_id=? ORDER BY reported_at DESC",(cid,))
        if not nm.empty:
            total=len(nm);critical=len(nm[nm['severity'].str.contains('Critical',case=False,na=False)])
            high=len(nm[nm['severity'].str.contains('High',case=False,na=False)])
            open_nm=len(nm[nm['status']=='Reported'])
            
            c1,c2,c3,c4=st.columns(4)
            with c1: st.metric("Total Reports",total)
            with c2: st.metric("Critical",critical); 
            with c3: st.metric("High Risk",high)
            with c4: st.metric("Open",open_nm)
            
            st.markdown("---")
            trend=Analytics.near_miss_trend(nm)
            if not trend.empty:
                fig=go.Figure(go.Bar(x=trend['date'],y=trend['count'],marker_color='#f59e0b',name='Near Misses'))
                fig.update_layout(template='plotly_dark',height=300,title="Near Miss Trend")
                st.plotly_chart(fig,use_container_width=True)
            
            st.markdown("### All Reports")
            for _,n in nm.iterrows():
                sev="badge-critical" if 'Critical' in str(n['severity']) else "badge-major" if 'High' in str(n['severity']) else "badge-minor"
                st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><b>{n["title"]}</b> — <span class="{sev}">{n["severity"][:30]}</span><br><span style="color:#94a3b8;">{n["category"]} | {n["location"]} | {n["reporter"]} | {n["reported_at"]}</span></div>',unsafe_allow_html=True)
        else: st.info("No near misses reported — great safety record!")
    
    with tab_n3:
        nm=sq("SELECT * FROM near_misses WHERE company_id=? AND status='Reported' ORDER BY reported_at DESC",(cid,))
        if not nm.empty:
            selected=st.selectbox("Select incident to investigate",nm['id'].tolist(),format_func=lambda x:f"#{x} — {nm[nm['id']==x]['title'].iloc[0][:50]}")
            incident=nm[nm['id']==selected].iloc[0]
            st.markdown(f"### Investigation: #{incident['id']} — {incident['title']}")
            st.write(f"**Description:** {incident['description']}")
            st.write(f"**Severity:** {incident['severity']} | **Category:** {incident['category']}")
            
            with st.form("investigation"):
                why1=st.text_input("1. Why did it happen?")
                why2=st.text_input("2. Why was that?")
                why3=st.text_input("3. Why was that?")
                why4=st.text_input("4. Why was that?")
                why5=st.text_input("5. Root cause?")
                corr=st.text_area("Corrective Action Required")
                if st.form_submit_button("Complete Investigation",type="primary",use_container_width=True):
                    investigation_text=f"5 Whys:\n1. {why1}\n2. {why2}\n3. {why3}\n4. {why4}\n5. {why5}"
                    db.execute("UPDATE near_misses SET investigation=?, corrective_action=?, status='Investigated' WHERE id=?",(investigation_text,corr,selected))
                    st.success("✅ Investigation complete!");st.rerun()

# ============================================
# 📍 SITES
# ============================================
elif page=="📍 Sites":
    st.markdown("<h1>📍 Site Management</h1>",unsafe_allow_html=True);st.markdown("---")
    sites=sq("SELECT * FROM sites WHERE company_id=? ORDER BY created_at DESC",(cid,))
    if not sites.empty:
        for _,s in sites.iterrows():
            nm_count=sq("SELECT COUNT(*) as c FROM near_misses WHERE site_id=?",(s['id'],)).iloc[0,0]
            with st.expander(f"📍 {s['name']} — {s.get('address','N/A')}"):
                st.write(f"Manager: {s.get('manager','N/A')} | Near Misses: {nm_count}")
    with st.form("add_site"):
        sn=st.text_input("Site Name*");sa=st.text_input("Address");sm=st.text_input("Site Manager")
        if st.form_submit_button("Add Site",type="primary",use_container_width=True):
            if sn: db.execute("INSERT INTO sites (company_id,name,address,manager) VALUES (?,?,?,?)",(cid,sn,sa,sm));st.success("✅ Site added!");st.rerun()

# ============================================
# REMAINING PAGES
# ============================================
elif page=="🔧 Workshop":
    st.markdown("<h1>🔧 Workshop</h1>",unsafe_allow_html=True)
    defects=sq("SELECT * FROM ops WHERE company_id=? AND status!='PASS' AND status!='REPAIRED' ORDER BY time DESC",(cid,))
    if not defects.empty:
        for _,d in defects.iterrows():
            sev="badge-vor" if 'VOR' in str(d['status']) else "badge-major"
            st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><b>{d["reg"]}</b> — <span class="{sev}">{d["status"]}</span><br>{str(d["notes"])[:100]}</div>',unsafe_allow_html=True)
    with st.form("repair"):
        vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"]);rn=st.text_area("Repair Notes")
        if st.form_submit_button("Mark Repaired",type="primary",use_container_width=True):
            c=get_db();c.execute("INSERT INTO ops (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,0,'REPAIRED',?,?,?)",(datetime.now(),reg,rn,st.session_state.user,cid));c.commit();c.close();st.success("✅ Repaired!");st.rerun()

elif page=="💰 Jobs":
    st.markdown("<h1>💰 Jobs & Invoices</h1>",unsafe_allow_html=True)
    with st.form("new_job"):
        cn=st.text_input("Customer*");de=st.text_area("Description*");qa=st.number_input("Quote (£)",0.0,100000.0,0.0)
        if st.form_submit_button("Create Job",type="primary",use_container_width=True):
            if cn and de: db.execute("INSERT INTO jobs (company_id,customer_name,description,quoted_amount) VALUES (?,?,?,?)",(cid,cn,de,qa));st.success("✅ Created!");st.rerun()
    jobs=sq("SELECT * FROM jobs WHERE company_id=? ORDER BY created_at DESC",(cid,))
    if not jobs.empty:
        for _,j in jobs.iterrows():
            with st.expander(f"{j['customer_name']} — £{j['quoted_amount']:,.2f}"):
                if j['status']!='Completed':
                    if st.button(f"Complete #{j['id']}",key=f"j{j['id']}"):
                        db.execute("UPDATE jobs SET status='Completed' WHERE id=?",(j['id'],))
                        total=round(j['quoted_amount']*1.2,2)
                        db.execute("INSERT INTO invoices (company_id,job_id,customer_name,total,status,due_date) VALUES (?,?,?,?,'Unpaid',?)",(cid,j['id'],j['customer_name'],total,(datetime.now()+timedelta(days=30)).strftime('%Y-%m-%d')))
                        st.success("✅ Invoice generated!");st.rerun()

elif page=="⛽ Fuel":
    st.markdown("<h1>⛽ Fuel</h1>",unsafe_allow_html=True)
    with st.form("fuel"):
        vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"])
        lit=st.number_input("Litres",0.0,1000.0,0.0);cost=st.number_input("Cost (£)",0.0,10000.0,0.0);mil=st.number_input("Mileage",0,999999,0)
        if st.form_submit_button("Log",type="primary",use_container_width=True):
            db.execute("INSERT INTO fuel_log (company_id,vehicle_reg,date,litres,cost,mileage,driver) VALUES (?,?,?,?,?,?,?)",(cid,reg,datetime.now().strftime('%Y-%m-%d'),lit,cost,mil,st.session_state.user));st.success("✅ Logged!");st.rerun()

elif page=="🔔 Maintenance":
    st.markdown("<h1>🔔 Maintenance</h1>",unsafe_allow_html=True)
    with st.form("maint"):
        vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"])
        stp=st.selectbox("Type",["Oil Change","Brake Service","MOT","Annual Service"]);dd=st.date_input("Due Date")
        if st.form_submit_button("Schedule",type="primary",use_container_width=True): db.execute("INSERT INTO maintenance (company_id,vehicle_reg,service_type,due_date) VALUES (?,?,?,?)",(cid,reg,stp,dd.strftime('%Y-%m-%d')));st.success("✅ Scheduled!");st.rerun()

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
        if not ok:
            fl=[i for i,c in chk.items() if not c];st.error(f"Defects: {', '.join(fl)}")
            nt=st.text_area("Description*",height=100);sv=st.selectbox("Severity*",["Minor","Major - Workshop","Dangerous - VOR"])
        sg=st.text_input("Signature*")
        if st.form_submit_button("Submit",type="primary",use_container_width=True):
            if not ok and not nt: st.error("Description required")
            elif not sg: st.error("Signature required")
            else:
                sts="PASS" if ok else f"DEFECT - {sv}"
                c=get_db();c.execute("INSERT INTO ops (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,?,?,?,?,?)",(datetime.now(),reg,mil,sts,nt or "Passed",st.session_state.user,cid));c.commit();c.close()
                if ok: st.success("PASS!");st.balloons()
                else:
                    if OPENAI_API_KEY and nt:
                        with st.spinner("AI..."): st.info(ai_analyze(f"Vehicle defect: {reg}. {', '.join(fl)}. {nt}"))
                    st.warning("Defect logged")
                time.sleep(2);st.rerun()

elif page=="⏱️ Tacho":
    st.markdown("<h1>⏱️ Tacho</h1>",unsafe_allow_html=True)
    s=tacho.status()
    c1,c2,c3=st.columns(3)
    with c1:
        h=int(s['total'].total_seconds()//3600);m=int((s['total'].total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">DRIVING</div><div class="tacho-time">{h:02d}:{m:02d}</div></div>',unsafe_allow_html=True)
    with c2:
        bh=int(s['until_break'].total_seconds()//3600);bm=int((s['until_break'].total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">BREAK IN</div><div class="tacho-time">{bh:02d}:{bm:02d}</div></div>',unsafe_allow_html=True)
    with c3:
        dh=int(max(timedelta(0),s['day_left']).total_seconds()//3600);dm=int((max(timedelta(0),s['day_left']).total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">DAY LEFT</div><div class="tacho-time">{dh:02d}:{dm:02d}</div></div>',unsafe_allow_html=True)
    if s['warning']: st.error(s['warning'])
    cc1,cc2=st.columns(2)
    with cc1:
        if not s['driving']:
            if st.button("🟢 Start",type="primary",use_container_width=True): tacho.start();st.rerun()
        else:
            if st.button("🔴 Stop",use_container_width=True): tacho.stop();st.rerun()
    with cc2:
        if st.button("🌙 Reset",use_container_width=True): tacho.stop();st.session_state.td=timedelta(0);st.rerun()

elif page=="📸 Photos": st.markdown("<h1>📸 Photos</h1>",unsafe_allow_html=True);st.camera_input("Take photo");st.button("Save")

elif page=="🏆 Safety League":
    st.markdown("<h1>🏆 Safety League</h1>",unsafe_allow_html=True)
    nm=sq("SELECT reporter, COUNT(*) as reports FROM near_misses WHERE company_id=? GROUP BY reporter ORDER BY reports",(cid,))
    if not nm.empty:
        st.markdown("### Staff with FEWEST near misses (safer = higher rank)")
        for i,(_,r) in enumerate(nm.iterrows()):
            icon={0:'🥇',1:'🥈',2:'🥉'}.get(i,f"#{i+1}")
            st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;">{icon} <b>{r["reporter"]}</b> — {r["reports"]} reports</div>',unsafe_allow_html=True)

elif page=="📊 Compliance":
    st.markdown("<h1>📊 Compliance</h1>",unsafe_allow_html=True)
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,))
    nm=sq("SELECT * FROM near_misses WHERE company_id=?",(cid,))
    c1,c2=st.columns(2)
    with c1: st.metric("Fleet Pass Rate",f"{Analytics.health(ops)}%")
    with c2: st.metric("Near Misses (30d)",len(nm[nm['reported_at']>str(datetime.now()-timedelta(days=30))]) if not nm.empty else 0)

elif page=="🤖 AI":
    st.markdown("<h1>🤖 AI Analysis</h1>",unsafe_allow_html=True)
    prompt=st.text_area("Ask AI about any incident or defect","Analyze fleet safety trends")
    if st.button("Run AI",type="primary"): st.info(ai_analyze(prompt))

elif page=="📋 Reports":
    st.markdown("<h1>📋 Reports</h1>",unsafe_allow_html=True)
    nm=sq("SELECT * FROM near_misses WHERE company_id=?",(cid,))
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,))
    if not nm.empty: st.download_button("📊 Near Miss CSV",nm.to_csv(index=False),"near_misses.csv")
    if not ops.empty: st.download_button("📊 Fleet CSV",ops.to_csv(index=False),"fleet_ops.csv")

elif page=="⚙️ Settings":
    st.markdown("<h1>⚙️ Settings</h1>",unsafe_allow_html=True)
    with st.form("pwd"):
        cur=st.text_input("Current",type="password");new=st.text_input("New",type="password")
        if st.form_submit_button("Update",type="primary"):
            if cur and new and len(new)>=8:
                c=get_db();r=c.execute("SELECT password FROM users WHERE username=? AND company_id=?",(st.session_state.user,cid)).fetchone()
                if r and Security.verify(cur,r[0]): c.execute("UPDATE users SET password=? WHERE username=? AND company_id=?",(Security.hash(new),st.session_state.user,cid));c.commit();st.success("✅ Done!")
                else: st.error("Wrong password")
                c.close()

elif page=="👥 My Shifts":
    st.markdown("<h1>👥 My Shifts</h1>",unsafe_allow_html=True)
    uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,))
    if not uid.empty:
        shifts=sq("SELECT * FROM shifts WHERE user_id=? ORDER BY shift_date DESC LIMIT 20",(uid.iloc[0,0],))
        if not shifts.empty:
            for _,s in shifts.iterrows():
                st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{s["shift_date"]}</b> — {s["start_time"]} to {s["end_time"]} — {s["status"]}</div>',unsafe_allow_html=True)
        else: st.info("No shifts scheduled")
    
    st.markdown("---")
    if st.button("🟢 Clock In",type="primary",use_container_width=True):
        db.execute("UPDATE shifts SET clock_in=?, status='Working' WHERE user_id=? AND shift_date=? AND status='Scheduled'",(datetime.now(),uid.iloc[0,0],datetime.now().strftime('%Y-%m-%d')))
        st.success("✅ Clocked in!");st.rerun()
    if st.button("🔴 Clock Out",use_container_width=True):
        db.execute("UPDATE shifts SET clock_out=?, status='Completed' WHERE user_id=? AND status='Working'",(datetime.now(),uid.iloc[0,0]))
        st.success("✅ Clocked out!");st.rerun()

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748b;">🏢 Enterprise Command Centre • Fleet • Staff • Safety • Near Miss • HSE Compliant</div>',unsafe_allow_html=True)
