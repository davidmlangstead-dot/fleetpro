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

st.set_page_config(page_title="FleetPro 365 | Enterprise Fleet Management", layout="wide", page_icon="🚛", initial_sidebar_state="expanded")

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
@media (max-width: 768px) { .metric-value { font-size: 1.8em; } }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATABASE
# ============================================
DB_PATH = Path(__file__).parent / "fleetpro.db"
def get_db():
    conn = sqlite3.connect(str(DB_PATH)); conn.row_factory = sqlite3.Row; return conn

conn = get_db()
conn.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, branding_color DEFAULT '#3b82f6', email_alerts TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'driver', full_name TEXT, phone TEXT, email TEXT, company_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT, type TEXT, make TEXT, model TEXT, year INTEGER, fleet_number TEXT, fuel_type TEXT, company_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(reg, company_id))")
conn.execute("CREATE TABLE IF NOT EXISTS ops (id INTEGER PRIMARY KEY AUTOINCREMENT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reg TEXT, mileage REAL, fuel_added REAL, fuel_cost REAL, status TEXT, notes TEXT, driver TEXT, location TEXT, company_id INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, customer_name TEXT, vehicle_reg TEXT, description TEXT, status DEFAULT 'Pending', priority DEFAULT 'Normal', quoted_amount REAL, invoiced_amount REAL, paid BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, job_id INTEGER, customer_name TEXT, amount REAL, vat REAL, total REAL, status DEFAULT 'Unpaid', due_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, vehicle_reg TEXT, service_type TEXT, due_mileage REAL, due_date DATE, status DEFAULT 'Scheduled', notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS fuel_log (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, vehicle_reg TEXT, date DATE, litres REAL, cost REAL, mileage REAL, mpg REAL, driver TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit(); conn.close()

class SQLiteDB:
    def query(self, sql, params=None):
        c = get_db()
        try: return pd.read_sql_query(sql, c, params=params or ())
        finally: c.close()
    def execute(self, sql, params=None):
        c = get_db()
        try: c.execute(sql, params or ()); c.commit()
        finally: c.close()

db = SQLiteDB()
OPENAI_API_KEY = 'sk-proj-TC2fgnfimB9wR4k08IXW5g'

class AlertEngine:
    @staticmethod
    def send_vor_alert(company_id, reg, defect, driver):
        try:
            company = db.query("SELECT email_alerts FROM companies WHERE id = ?", (company_id,))
            if not company.empty and company.iloc[0]['email_alerts']:
                st.toast(f"📧 VOR Alert sent for {reg}!", icon="🚨")
        except: pass

class SecurityEngine:
    @staticmethod
    def hash_password(p):
        s = secrets.token_hex(16); return f"{s}${hashlib.sha256(f'{s}{p}'.encode()).hexdigest()}"
    @staticmethod
    def verify_password(p, h):
        try: s, hv = h.split('$'); return hashlib.sha256(f'{s}{p}'.encode()).hexdigest() == hv
        except: return False

def ai_assess(v, d, n):
    if not OPENAI_API_KEY: return "AI offline"
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"},
            json={"model":"gpt-4o-mini","messages":[{"role":"system","content":"DVSA examiner. 1)Risk 2)Continue? 3)Action."},{"role":"user","content":f"Vehicle:{v}\nDefects:{d}\nNotes:{n}"}],"max_tokens":200},timeout=10)
        return r.json()["choices"][0]["message"]["content"]
    except: return "AI unavailable"

class FleetAnalytics:
    @staticmethod
    def health_score(df):
        if df.empty: return 100.0
        t=len(df);vor=len(df[df['status'].str.contains('VOR|Dangerous',case=False,na=False)]);maj=len(df[df['status'].str.contains('Major',case=False,na=False)])
        return round(max(0,100-((vor*35+maj*15)/max(t,1))),1)
    @staticmethod
    def compliance_score(df):
        if df.empty: return 0.0
        r=df[df['time']>datetime.now()-timedelta(days=30)]
        if len(r)==0: return 0.0
        return round((len(r[r['status']=='PASS'])/len(r))*100,1)
    @staticmethod
    def driver_scorecard(insp, drv):
        d=insp[insp['driver']==drv]
        if len(d)==0: return {'score':0,'total':0,'passes':0,'pass_rate':0,'vor':0,'trend':'N/A','rank':99}
        t=len(d);p=len(d[d['status']=='PASS']);v=len(d[d['status'].str.contains('VOR|Dangerous',case=False,na=False)])
        s=round(max(0,min(100,((p/t)*60)+(min(len(d[d['time']>datetime.now()-timedelta(days=7)])*5,20))-(v*20)+(10 if t>5 else 0))),1)
        return {'score':s,'total':t,'passes':p,'pass_rate':round((p/t)*100,1),'vor':v,'trend':'Elite' if s>90 else 'Excellent' if s>75 else 'Good' if s>50 else 'Needs Work','rank':0}
    @staticmethod
    def get_leaderboard(insp, udf):
        sc=[]
        for _,u in udf.iterrows():
            s=FleetAnalytics.driver_scorecard(insp,u['username']);s['driver']=u['username'];s['name']=u.get('full_name',u['username']);sc.append(s)
        sc.sort(key=lambda x:x['score'],reverse=True)
        for i,s in enumerate(sc): s['rank']=i+1
        return sc
    @staticmethod
    def calc_mpg(m,l):
        if l<=0: return 0
        return round(m/(l/4.54609),1)
    @staticmethod
    def gen_gps(reg):
        random.seed(hash(reg)%100000)
        return {'lat':51.3+random.uniform(-1,1),'lon':-0.5+random.uniform(-1.2,1.2),'speed':random.randint(0,70),'status':random.choice(['Moving','Idle','Parked'])}

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
        elif dl<timedelta(hours=1): w=f"{int(dl.total_seconds()//60)}min left today"
        elif tl<timedelta(minutes=15): w=f"BREAK in {int(tl.total_seconds()//60)}min"
        return {'total':t,'until_break':max(timedelta(0),tl),'day_left':max(timedelta(0),dl),'warning':w,'driving':st.session_state.ts is not None,'break_needed':tl<=timedelta(minutes=30)}

class ReportGenerator:
    @staticmethod
    def invoice_pdf(inv_id, customer, amount, status):
        pdf=FPDF();pdf.add_page()
        pdf.set_fill_color(10,14,39);pdf.rect(0,0,210,40,'F')
        pdf.set_text_color(255,255,255);pdf.set_font('Arial','B',22)
        pdf.cell(0,25,f'INVOICE #{inv_id}',0,1,'C')
        pdf.set_text_color(0,0,0);pdf.ln(10)
        pdf.set_font('Arial','',12)
        pdf.cell(0,8,f"Customer: {customer}",0,1)
        pdf.cell(0,8,f"Amount: £{amount:,.2f}",0,1)
        pdf.cell(0,8,f"Status: {status}",0,1)
        return pdf.output(dest='S').encode('latin-1')
    @staticmethod
    def dvsa_report(reg, inspections):
        pdf=FPDF();pdf.add_page()
        pdf.set_fill_color(10,14,39);pdf.rect(0,0,210,35,'F')
        pdf.set_text_color(255,255,255);pdf.set_font('Arial','B',18)
        pdf.cell(0,20,'FleetPro 365 - Inspection Report',0,1,'C')
        pdf.ln(10);pdf.set_text_color(0,0,0)
        for _,insp in inspections.head(25).iterrows():
            pdf.cell(0,6,f"{insp['time']} | {insp['mileage']} | {insp['status']} | {insp['driver']}",0,1)
        return pdf.output(dest='S').encode('latin-1')

DVSA = {
    "Vehicle Structure":["Cab undamaged","Body panels secure","Doors & hinges working","Access steps secure"],
    "Visibility":["Windscreen clear","Wipers & washers OK","Mirrors present & clean"],
    "Lighting":["Headlights","Side lights","Indicators","Brake lights","Reflectors"],
    "Wheels & Tyres":["Tread depth legal","No cuts/bulges","Wheel nuts present"],
    "Brakes":["Service brake OK","Parking brake holds","No air leaks"],
    "Engine & Fluids":["Oil correct","Coolant correct","Washer fluid","No leaks"],
    "Safety Equipment":["Seatbelts","Horn","Fire extinguisher","First aid kit","Hi-vis vest"],
    "Load Security":["Load distributed","Load secured","Doors locked"]
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False;st.session_state.user=None;st.session_state.role=None;st.session_state.cid=None

tacho=TachoEngine()

# ============================================
# AUTH
# ============================================
if not st.session_state.logged_in:
    c1,c2,c3=st.columns([1,2.5,1])
    with c2:
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;margin-bottom:40px;"><div style="font-size:4em;">🚛</div><h1 style="font-size:3em;font-weight:900;margin:0;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">FleetPro 365</h1><p style="color:#94a3b8;font-size:1.1em;">ENTERPRISE PLATFORM</p><p style="color:#64748b;">DVSA • Jobs • Invoices • Fuel • Maintenance • Alerts • White-Label</p></div>""",unsafe_allow_html=True)
        t1,t2=st.tabs(["Login","Register"])
        with t1:
            with st.form("login"):
                u=st.text_input("Username");p=st.text_input("Password",type="password")
                if st.form_submit_button("Login",type="primary",use_container_width=True):
                    c=get_db();r=c.execute("SELECT password,role,company_id FROM users WHERE username=?",(u,)).fetchone();c.close()
                    if r and SecurityEngine.verify_password(p,r[0]): st.session_state.logged_in=True;st.session_state.user=u;st.session_state.role=r[1];st.session_state.cid=r[2];st.rerun()
                    else: st.error("Invalid credentials")
        with t2:
            with st.form("register"):
                co=st.text_input("Company*");au=st.text_input("Username*");ap=st.text_input("Password*",type="password")
                if st.form_submit_button("Register",type="primary",use_container_width=True):
                    if not co or not au or not ap: st.error("Fill all fields")
                    elif len(ap)<8: st.error("Password: 8+ chars")
                    else:
                        try:
                            c=get_db();c.execute("INSERT INTO companies (name) VALUES (?)",(co,));cid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
                            c.execute("INSERT INTO users (username,password,role,company_id) VALUES (?,?,'admin',?)",(au,SecurityEngine.hash_password(ap),cid));c.commit();c.close()
                            st.success("Registered! Go to Login.")
                        except: st.error("Company/username exists")
    st.stop()

cid=st.session_state.cid;role=st.session_state.role

with st.sidebar:
    st.markdown('<div style="text-align:center;"><h3 style="font-weight:900;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🚛 FleetPro 365</h3></div>',unsafe_allow_html=True)
    st.markdown(f"**{st.session_state.user}** ({role.upper()})")
    if role=="admin":
        page=st.radio("",["🏠 Command","🚛 Fleet","👥 Drivers","🔧 Workshop","📋 Manager","💰 Jobs","⛽ Fuel","🔔 Maintenance","🔍 Inspection","⏱️ Tacho","📸 Photos","🏆 League","🗺️ Map","📊 Compliance","🤖 AI","📋 Reports","🎨 Brand","⚙️ Settings"],label_visibility="collapsed")
    elif role=="driver": page=st.radio("",["🔍 Inspection","⏱️ Tacho","📸 Photos","⛽ Fuel"],label_visibility="collapsed")
    elif role=="workshop": page=st.radio("",["🔧 Workshop","🔔 Maintenance","🔍 Inspection"],label_visibility="collapsed")
    elif role=="manager": page=st.radio("",["📋 Manager","💰 Jobs","📊 Compliance","📋 Reports"],label_visibility="collapsed")
    else: page=st.radio("",["🔍 Inspection","⏱️ Tacho"],label_visibility="collapsed")
    st.markdown("---")
    try: today=db.query("SELECT COUNT(*) as c FROM ops WHERE company_id=? AND DATE(time)=DATE('now')",(cid,)).iloc[0,0]
    except: today=0
    st.metric("Checks Today",today)
    if st.button("Logout",use_container_width=True): st.session_state.clear();st.rerun()

def sq(sql,p=None):
    try: return db.query(sql,p)
    except: return pd.DataFrame()

# ============================================
# 🏠 COMMAND
# ============================================
if page=="🏠 Command":
    st.markdown(f"<h1>Command Centre</h1><p style='color:#94a3b8;'>{datetime.now().strftime('%A, %d %B %Y — %H:%M')}</p>",unsafe_allow_html=True);st.markdown("---")
    ops=sq("SELECT * FROM ops WHERE company_id=? ORDER BY time DESC",(cid,));vc=sq("SELECT COUNT(*) as c FROM vehicles WHERE company_id=?",(cid,)).iloc[0,0]
    jc=sq("SELECT COUNT(*) as c FROM jobs WHERE company_id=? AND status!='Completed'",(cid,)).iloc[0,0]
    rev=sq("SELECT COALESCE(SUM(total),0) as r FROM invoices WHERE company_id=? AND status='Paid'",(cid,)).iloc[0,0]
    dc=sq("SELECT COUNT(*) as c FROM users WHERE company_id=? AND role='driver'",(cid,)).iloc[0,0]
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{FleetAnalytics.health_score(ops)}%</div></div>',unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">Revenue</div><div class="metric-value">£{rev:,.0f}</div></div>',unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-label">Vehicles</div><div class="metric-value">{vc}</div></div>',unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-label">Open Jobs</div><div class="metric-value">{jc}</div></div>',unsafe_allow_html=True)
    if len(ops)>0:
        st.markdown("---");st.markdown("### Recent Activity")
        for _,r in ops.head(8).iterrows():
            b="badge-pass" if r['status']=='PASS' else ("badge-vor" if 'VOR' in str(r['status']) else "badge-major" if 'Major' in str(r['status']) else "badge-minor")
            st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><span style="font-weight:600;">{r["reg"]}</span> • {r["driver"]} • {r["mileage"]:,.0f}mi <span class="{b}" style="float:right;">{r["status"]}</span></div>',unsafe_allow_html=True)

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
                    last=sq("SELECT * FROM ops WHERE reg=? AND company_id=? ORDER BY time DESC LIMIT 1",(v['reg'],cid))
                    if not last.empty: st.write(f"Last: {last.iloc[0]['time']} | {last.iloc[0]['status']} | {last.iloc[0]['mileage']:,.0f}mi")
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
# 👥 DRIVERS
# ============================================
elif page=="👥 Drivers":
    st.markdown("<h1>👥 Driver Management</h1>",unsafe_allow_html=True);st.markdown("---")
    drv=sq("SELECT * FROM users WHERE company_id=? AND role='driver' ORDER BY created_at DESC",(cid,))
    if not drv.empty:
        st.dataframe(drv[['username','full_name','phone','created_at']],use_container_width=True,hide_index=True)
        ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,))
        if len(ops)>0:
            st.markdown("### Driver Performance")
            for _,d in drv.iterrows():
                try:
                    sc=FleetAnalytics.driver_scorecard(ops,d['username']);cl='#10b981' if sc['score']>75 else '#f59e0b' if sc['score']>50 else '#ef4444'
                    st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><b>{d["username"]}</b> — <span style="color:{cl};font-weight:700;">{sc["score"]}/100</span> | {sc["pass_rate"]}% | {sc["total"]} checks | {sc["trend"]}</div>',unsafe_allow_html=True)
                except: pass
    else: st.info("No drivers yet")
    st.markdown("---")
    with st.form("add_d"):
        c1,c2=st.columns(2)
        with c1: du=st.text_input("Username*");df=st.text_input("Full Name")
        with c2: dp=st.text_input("Password*",type="password");dph=st.text_input("Phone")
        if st.form_submit_button("Add Driver",type="primary",use_container_width=True):
            if du and dp and len(dp)>=8:
                try:
                    c=get_db();c.execute("INSERT INTO users (username,password,role,full_name,phone,company_id) VALUES (?,?,'driver',?,?,?)",(du,SecurityEngine.hash_password(dp),df,dph,cid));c.commit();c.close()
                    st.success(f"✅ {du} added!");st.rerun()
                except: st.error("Username exists")

# ============================================
# 🔧 WORKSHOP
# ============================================
elif page=="🔧 Workshop":
    st.markdown("<h1>🔧 Workshop Dashboard</h1>",unsafe_allow_html=True);st.markdown("---")
    defects=sq("SELECT * FROM ops WHERE company_id=? AND status!='PASS' AND status!='REPAIRED' ORDER BY time DESC",(cid,))
    if not defects.empty:
        st.markdown(f"### 🔴 Open Defects ({len(defects)})")
        for _,d in defects.iterrows():
            sev="badge-vor" if 'VOR' in str(d['status']) else "badge-major" if 'Major' in str(d['status']) else "badge-minor"
            st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:12px;"><b>{d["reg"]}</b> — {d["driver"]} — <span class="{sev}">{d["status"]}</span><br><span style="color:#94a3b8;">{str(d["notes"])[:100]}</span></div>',unsafe_allow_html=True)
    else: st.success("✅ No open defects")
    st.markdown("---")
    with st.form("repair"):
        vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"]);rn=st.text_area("Repair Notes")
        if st.form_submit_button("Mark Repaired",type="primary",use_container_width=True):
            c=get_db();c.execute("INSERT INTO ops (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,0,'REPAIRED',?,?,?)",(datetime.now(),reg,rn,st.session_state.user,cid));c.commit();c.close()
            st.success("✅ Repaired!");st.rerun()

# ============================================
# 📋 MANAGER
# ============================================
elif page=="📋 Manager":
    st.markdown("<h1>📋 Transport Manager</h1>",unsafe_allow_html=True);st.markdown("---")
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,));veh=sq("SELECT * FROM vehicles WHERE company_id=?",(cid,));drv=sq("SELECT * FROM users WHERE company_id=? AND role='driver'",(cid,))
    c1,c2,c3,c4=st.columns(4)
    with c1: st.metric("Vehicles",len(veh))
    with c2: st.metric("Drivers",len(drv))
    with c3: st.metric("Inspections",len(ops))
    with c4: st.metric("Compliance",f"{FleetAnalytics.compliance_score(ops)}%")
    if len(ops)>0:
        st.markdown("---")
        comp=FleetAnalytics.compliance_score(ops);health=FleetAnalytics.health_score(ops)
        ca,cb=st.columns(2)
        with ca: st.markdown(f'<div class="metric-card"><div class="metric-label">DVSA Score</div><div class="metric-value">{comp}%</div></div>',unsafe_allow_html=True)
        with cb: st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{health}%</div></div>',unsafe_allow_html=True)
    if not veh.empty:
        st.markdown("---");st.markdown("### Vehicle Status")
        for _,v in veh.iterrows():
            last=sq("SELECT * FROM ops WHERE reg=? AND company_id=? ORDER BY time DESC LIMIT 1",(v['reg'],cid))
            sts=last.iloc[0]['status'] if not last.empty else "Not inspected";cl='#10b981' if sts=='PASS' else '#ef4444'
            st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{v["reg"]}</b> — <span style="color:{cl};">{sts}</span></div>',unsafe_allow_html=True)

# ============================================
# 💰 JOBS
# ============================================
elif page=="💰 Jobs":
    st.markdown("<h1>💰 Jobs & Invoicing</h1>",unsafe_allow_html=True);st.markdown("---")
    tj1,tj2,tj3=st.tabs(["📋 New Job","📊 Job List","🧾 Invoices"])
    with tj1:
        with st.form("new_job"):
            cn=st.text_input("Customer Name*");vr=st.text_input("Vehicle Reg");de=st.text_area("Description*");qa=st.number_input("Quote (£)",0.0,100000.0,0.0);pr=st.selectbox("Priority",["Normal","Urgent","VOR Related"])
            if st.form_submit_button("Create Job",type="primary",use_container_width=True):
                if cn and de: db.execute("INSERT INTO jobs (company_id,customer_name,vehicle_reg,description,quoted_amount,priority) VALUES (?,?,?,?,?,?)",(cid,cn,vr,de,qa,pr));st.success("✅ Job created!");st.rerun()
                else: st.error("Customer and description required")
    with tj2:
        jobs=sq("SELECT * FROM jobs WHERE company_id=? ORDER BY created_at DESC",(cid,))
        if not jobs.empty:
            for _,j in jobs.iterrows():
                sts='🟢' if j['status']=='Completed' else '🟡' if j['status']=='In Progress' else '🔴'
                with st.expander(f"{sts} {j['customer_name']} — {j['description'][:40]} — £{j['quoted_amount']:,.2f}"):
                    st.write(f"**Status:** {j['status']} | **Priority:** {j['priority']} | **Created:** {j['created_at']}")
                    if j['status']!='Completed':
                        if st.button(f"✅ Mark Complete #{j['id']}",key=f"comp_{j['id']}"):
                            db.execute("UPDATE jobs SET status='Completed',completed_at=? WHERE id=?",(datetime.now(),j['id']))
                            inv_total=round(j['quoted_amount']*1.2,2);inv_vat=round(j['quoted_amount']*0.2,2)
                            db.execute("INSERT INTO invoices (company_id,job_id,customer_name,amount,vat,total,status,due_date) VALUES (?,?,?,?,?,?,'Unpaid',?)",(cid,j['id'],j['customer_name'],j['quoted_amount'],inv_vat,inv_total,(datetime.now()+timedelta(days=30)).strftime('%Y-%m-%d')))
                            st.success("✅ Complete — Invoice generated!");st.rerun()
        else: st.info("No jobs yet")
    with tj3:
        inv=sq("SELECT * FROM invoices WHERE company_id=? ORDER BY created_at DESC",(cid,))
        if not inv.empty:
            total_unpaid=inv[inv['status']=='Unpaid']['total'].sum()
            st.metric("Outstanding",f"£{total_unpaid:,.2f}")
            for _,i in inv.iterrows():
                cl='#ef4444' if i['status']=='Unpaid' else '#10b981'
                with st.expander(f"🧾 #{i['id']} — {i['customer_name']} — £{i['total']:,.2f} — {i['status']}"):
                    st.write(f"**Amount:** £{i['amount']:,.2f} | **VAT:** £{i['vat']:,.2f} | **Total:** £{i['total']:,.2f}")
                    st.write(f"**Due:** {i['due_date']} | **Created:** {i['created_at']}")
                    if i['status']=='Unpaid':
                        if st.button(f"💰 Mark Paid #{i['id']}",key=f"pay_{i['id']}"):
                            db.execute("UPDATE invoices SET status='Paid' WHERE id=?",(i['id'],))
                            if i['job_id']: db.execute("UPDATE jobs SET paid=1 WHERE id=?",(i['job_id'],))
                            st.success("✅ Marked as paid!");st.rerun()
                    if st.button(f"📄 PDF #{i['id']}",key=f"pdf_{i['id']}"):
                        pdf=ReportGenerator.invoice_pdf(i['id'],i['customer_name'],i['total'],i['status'])
                        st.download_button("Download Invoice PDF",pdf,f"invoice_{i['id']}.pdf","application/pdf")
        else: st.info("No invoices yet")

# ============================================
# ⛽ FUEL
# ============================================
elif page=="⛽ Fuel":
    st.markdown("<h1>⛽ Fuel Tracking</h1>",unsafe_allow_html=True);st.markdown("---")
    with st.form("fuel"):
        vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"])
        lit=st.number_input("Litres Added",0.0,1000.0,0.0);cost=st.number_input("Total Cost (£)",0.0,10000.0,0.0);mil=st.number_input("Current Mileage",0,999999,0)
        if st.form_submit_button("Log Fuel",type="primary",use_container_width=True):
            last=sq("SELECT mileage FROM fuel_log WHERE vehicle_reg=? AND company_id=? ORDER BY date DESC LIMIT 1",(reg,cid))
            pm=last.iloc[0,0] if not last.empty else mil;mpg=FleetAnalytics.calc_mpg(mil-pm,lit) if pm!=mil else 0
            db.execute("INSERT INTO fuel_log (company_id,vehicle_reg,date,litres,cost,mileage,mpg,driver) VALUES (?,?,?,?,?,?,?,?)",(cid,reg,datetime.now().strftime('%Y-%m-%d'),lit,cost,mil,mpg,st.session_state.user))
            st.success(f"✅ Fuel logged! MPG: {mpg}");st.rerun()
    fd=sq("SELECT * FROM fuel_log WHERE company_id=? ORDER BY date DESC LIMIT 30",(cid,))
    if not fd.empty:
        st.markdown("### Recent Fuel Logs")
        st.dataframe(fd[['date','vehicle_reg','litres','cost','mileage','mpg','driver']],use_container_width=True)
        st.markdown("### MPG Trends")
        fig=px.line(fd,x='date',y='mpg',color='vehicle_reg',title='MPG by Vehicle')
        fig.update_layout(template='plotly_dark',height=350)
        st.plotly_chart(fig,use_container_width=True)

# ============================================
# 🔔 MAINTENANCE
# ============================================
elif page=="🔔 Maintenance":
    st.markdown("<h1>🔔 Maintenance Scheduler</h1>",unsafe_allow_html=True);st.markdown("---")
    with st.form("maint"):
        vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,));reg=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"])
        stp=st.selectbox("Service Type",["Oil Change","Brake Service","MOT","Annual Service","Tyre Replacement","Safety Inspection","Other"])
        dm=st.number_input("Due at Mileage",0,999999,0);dd=st.date_input("Due Date");nt=st.text_area("Notes")
        if st.form_submit_button("Schedule Maintenance",type="primary",use_container_width=True):
            db.execute("INSERT INTO maintenance (company_id,vehicle_reg,service_type,due_mileage,due_date,notes) VALUES (?,?,?,?,?,?)",(cid,reg,stp,dm,dd.strftime('%Y-%m-%d'),nt))
            st.success("✅ Scheduled!");st.rerun()
    mt=sq("SELECT * FROM maintenance WHERE company_id=? ORDER BY due_date ASC",(cid,))
    if not mt.empty:
        st.markdown("### Maintenance Schedule")
        for _,m in mt.iterrows():
            od=datetime.strptime(m['due_date'],'%Y-%m-%d')<datetime.now()
            days_left=(datetime.strptime(m['due_date'],'%Y-%m-%d')-datetime.now()).days
            cl='#ef4444' if od else '#f59e0b' if days_left<7 else '#10b981'
            st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{m["vehicle_reg"]}</b> — {m["service_type"]} — {m["due_date"]} <span style="color:{cl};">({"OVERDUE" if od else f"{days_left}d left"})</span></div>',unsafe_allow_html=True)

# ============================================
# 🔍 INSPECTION
# ============================================
elif page=="🔍 Inspection":
    st.markdown("<h1>🔍 DVSA Daily Walkaround</h1><p style='color:#94a3b8;'>Statutory safety inspection — legally required</p>",unsafe_allow_html=True);st.markdown("---")
    vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,))
    if vehs.empty: st.warning("No vehicles registered");st.stop()
    with st.form("insp"):
        c1,c2=st.columns(2)
        with c1: reg=st.selectbox("Vehicle",vehs['reg'].tolist())
        with c2: mil=st.number_input("Mileage",0,step=1000)
        st.markdown("### DVSA Checklist")
        chk={}
        for cat,items in DVSA.items():
            st.markdown(f"**{cat}**");cs=st.columns(3)
            for i,it in enumerate(items):
                with cs[i%3]: chk[it]=st.checkbox(it,value=True)
        ok=all(chk.values());nt=""
        if not ok:
            fl=[i for i,c in chk.items() if not c];st.error(f"⚠️ {len(fl)} Defects: {', '.join(fl)}")
            nt=st.text_area("Description*",height=100);sv=st.selectbox("Severity*",["Minor","Major - Workshop","Dangerous - VOR"])
        sg=st.text_input("Digital Signature*")
        if st.form_submit_button("Submit Inspection",type="primary",use_container_width=True):
            if not ok and not nt: st.error("Description required")
            elif not sg: st.error("Signature required")
            else:
                sts="PASS" if ok else f"DEFECT - {sv}"
                c=get_db();c.execute("INSERT INTO ops (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,?,?,?,?,?)",(datetime.now(),reg,mil,sts,nt or "All checks passed",st.session_state.user,cid));c.commit();c.close()
                if 'VOR' in sts: AlertEngine.send_vor_alert(cid,reg,nt,st.session_state.user)
                if ok: st.success("✅ PASS — Vehicle roadworthy!");st.balloons()
                else:
                    if OPENAI_API_KEY and nt:
                        with st.spinner("🤖 AI analysing defect..."): st.info(f"🤖 AI Assessment:\n\n{ai_assess(reg,', '.join(fl),nt)}")
                    st.warning("⚠️ Defect logged — Workshop notified")
                time.sleep(2);st.rerun()

# ============================================
# ⏱️ TACHO
# ============================================
elif page=="⏱️ Tacho":
    st.markdown("<h1>⏱️ Digital Tachograph Timer</h1>",unsafe_allow_html=True);st.markdown("---")
    s=tacho.status()
    c1,c2,c3=st.columns(3)
    with c1:
        h=int(s['total'].total_seconds()//3600);m=int((s['total'].total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">DRIVING TODAY</div><div class="tacho-time">{h:02d}:{m:02d}</div><div class="tacho-label">Max: 9h00m</div></div>',unsafe_allow_html=True)
    with c2:
        bh=int(s['until_break'].total_seconds()//3600);bm=int((s['until_break'].total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">UNTIL BREAK</div><div class="{"tacho-warning" if s["break_needed"] else "tacho-time"}">{bh:02d}:{bm:02d}</div><div class="tacho-label">45min after 4.5h</div></div>',unsafe_allow_html=True)
    with c3:
        dh=int(max(timedelta(0),s['day_left']).total_seconds()//3600);dm=int((max(timedelta(0),s['day_left']).total_seconds()%3600)//60)
        st.markdown(f'<div class="tacho-display"><div class="tacho-label">DAY REMAINING</div><div class="tacho-time">{dh:02d}:{dm:02d}</div><div class="tacho-label">Max Daily: 9h</div></div>',unsafe_allow_html=True)
    if s['warning']: st.error(s['warning'])
    st.markdown("---")
    cc1,cc2,cc3=st.columns(3)
    with cc1:
        if not s['driving']:
            if st.button("🟢 Start Driving",type="primary",use_container_width=True): tacho.start();st.rerun()
        else:
            if st.button("🔴 Stop Driving",use_container_width=True): tacho.stop();st.rerun()
    with cc2:
        if st.button("☕ Take Break (45min)",use_container_width=True): tacho.stop();st.info("Break started");st.rerun()
    with cc3:
        if st.button("🌙 End Daily Rest",use_container_width=True): tacho.stop();st.session_state.td=timedelta(0);st.success("Rest period started");st.rerun()
    st.caption("EU/AETR Rules: 9h max daily | 45min break after 4.5h | 11h daily rest")

# ============================================
# 📸 PHOTOS
# ============================================
elif page=="📸 Photos":
    st.markdown("<h1>📸 Photo Evidence</h1>",unsafe_allow_html=True);st.markdown("---")
    vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,))
    vehicle=st.selectbox("Vehicle",vehs['reg'].tolist() if not vehs.empty else ["None"])
    photo=st.camera_input("Take defect photo");desc=st.text_area("Description")
    if photo and desc and st.button("💾 Save Photo Evidence",type="primary"):
        img=Image.open(photo);buf=BytesIO();img.save(buf,format="PNG")
        c=get_db();c.execute("INSERT INTO ops (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,0,'PHOTO EVIDENCE',?,?,?)",(datetime.now(),vehicle,desc,st.session_state.user,cid));c.commit();c.close()
        st.success("✅ Photo saved!")

# ============================================
# 🏆 LEAGUE
# ============================================
elif page=="🏆 League":
    st.markdown("<h1>🏆 Driver Performance League</h1>",unsafe_allow_html=True);st.markdown("---")
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,));usr=sq("SELECT username,full_name FROM users WHERE company_id=? AND role='driver'",(cid,))
    if not usr.empty and len(ops)>0:
        lb=FleetAnalytics.get_leaderboard(ops,usr)
        if len(lb)>0:
            for d in lb:
                icon={1:'🥇',2:'🥈',3:'🥉'}.get(d['rank'],f"#{d['rank']}")
                sc='#10b981' if d['score']>75 else '#f59e0b' if d['score']>50 else '#ef4444'
                st.markdown(f'<div class="glass-card" style="margin-bottom:6px;padding:14px;"><span style="font-size:1.3em;">{icon}</span> <b>{d["name"]}</b> — <span style="color:{sc};font-weight:700;">{d["score"]}/100</span> | {d["pass_rate"]}% pass | {d["trend"]}</div>',unsafe_allow_html=True)
    else: st.info("Add drivers and complete inspections to see rankings")

# ============================================
# 🗺️ MAP
# ============================================
elif page=="🗺️ Map":
    st.markdown("<h1>🗺️ Live Fleet Map</h1>",unsafe_allow_html=True);st.markdown("---")
    vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,))
    if not vehs.empty:
        pos=[FleetAnalytics.gen_gps(v['reg']) for _,v in vehs.iterrows()]
        df=pd.DataFrame(pos)
        df['reg']=vehs['reg'].tolist()
        fig=go.Figure()
        for _,v in df.iterrows():
            c='#10b981' if v['status']=='Moving' else '#f59e0b'
            fig.add_trace(go.Scattermapbox(lat=[v['lat']],lon=[v['lon']],mode='markers+text',marker=dict(size=14,color=c),text=v['reg'],textposition='top center'))
        fig.update_layout(mapbox=dict(style='carto-darkmatter',center=dict(lat=51.5,lon=-0.1),zoom=9),height=500,margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig,use_container_width=True)

# ============================================
# 📊 COMPLIANCE
# ============================================
elif page=="📊 Compliance":
    st.markdown("<h1>📊 Compliance Hub</h1>",unsafe_allow_html=True);st.markdown("---")
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,))
    if len(ops)>0:
        comp=FleetAnalytics.compliance_score(ops);health=FleetAnalytics.health_score(ops)
        c1,c2=st.columns(2)
        with c1: st.markdown(f'<div class="metric-card"><div class="metric-label">30-Day DVSA Score</div><div class="metric-value">{comp}%</div></div>',unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{health}%</div></div>',unsafe_allow_html=True)
        ops['date']=pd.to_datetime(ops['time']).dt.date
        daily=ops.groupby('date').agg(pr=('status',lambda x:(x=='PASS').mean()*100)).tail(30)
        fig=go.Figure(go.Scatter(x=daily.index,y=daily['pr'],mode='lines',fill='tozeroy',line=dict(color='#3b82f6',width=3),name='Pass Rate'))
        fig.add_hline(y=90,line_dash="dash",line_color="#ef4444",annotation_text="DVSA Minimum 90%")
        fig.update_layout(template='plotly_dark',height=400)
        st.plotly_chart(fig,use_container_width=True)

# ============================================
# 🤖 AI
# ============================================
elif page=="🤖 AI":
    st.markdown("<h1>🤖 AI Defect Analysis</h1>",unsafe_allow_html=True);st.markdown("---")
    vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,))
    if not vehs.empty:
        reg=st.selectbox("Select Vehicle",vehs['reg'].tolist())
        insp=sq("SELECT * FROM ops WHERE reg=? AND company_id=? ORDER BY time DESC LIMIT 20",(reg,cid))
        if len(insp)>0:
            defects=insp[insp['status']!='PASS']
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=insp['time'],y=insp['mileage'],mode='lines+markers',line=dict(color='#3b82f6',width=3),name='Mileage'))
            if len(defects)>0:
                fig.add_trace(go.Scatter(x=defects['time'],y=defects['mileage'],mode='markers',marker=dict(color='#ef4444',size=12,symbol='x'),name='Defects'))
            fig.update_layout(template='plotly_dark',height=350)
            st.plotly_chart(fig,use_container_width=True)
            if st.button("🤖 Run AI Predictive Analysis",type="primary"):
                with st.spinner("AI analysing fleet data..."): st.info(ai_assess(reg,f"{len(defects)} defects found","Full vehicle analysis"))

# ============================================
# 📋 REPORTS
# ============================================
elif page=="📋 Reports":
    st.markdown("<h1>📋 Reports & Export</h1>",unsafe_allow_html=True);st.markdown("---")
    ops=sq("SELECT * FROM ops WHERE company_id=? ORDER BY time DESC",(cid,))
    if not ops.empty:
        st.dataframe(ops,use_container_width=True)
        csv=ops.to_csv(index=False);st.download_button("📊 Download Full CSV Report",csv,f"fleet_report_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")
        st.markdown("---")
        vehs=sq("SELECT DISTINCT reg FROM ops WHERE company_id=?",(cid,))
        if not vehs.empty:
            reg=st.selectbox("Filter by Vehicle",vehs['reg'].tolist())
            filtered=ops[ops['reg']==reg]
            if not filtered.empty:
                st.dataframe(filtered,use_container_width=True)
                pdf=ReportGenerator.dvsa_report(reg,filtered)
                st.download_button("📄 Download DVSA PDF Report",pdf,f"DVSA_{reg}.pdf","application/pdf")

# ============================================
# 🎨 BRAND
# ============================================
elif page=="🎨 Brand":
    st.markdown("<h1>🎨 White-Label Settings</h1>",unsafe_allow_html=True);st.markdown("---")
    co=sq("SELECT * FROM companies WHERE id=?",(cid,))
    if not co.empty:
        c=co.iloc[0]
        with st.form("wl"):
            bc=st.color_picker("Brand Color",c.get('branding_color','#3b82f6'));ea=st.text_input("Alert Email Address",c.get('email_alerts',''),placeholder="alerts@yourcompany.com")
            if st.form_submit_button("Save Branding",type="primary",use_container_width=True):
                db.execute("UPDATE companies SET branding_color=?,email_alerts=? WHERE id=?",(bc,ea,cid));st.success("✅ Branding updated!");st.rerun()
        st.markdown(f'<div style="background:{c.get("branding_color","#3b82f6")};padding:40px;border-radius:20px;text-align:center;color:white;"><h1>{c["name"]}</h1><p>Powered by FleetPro 365</p></div>',unsafe_allow_html=True)

# ============================================
# ⚙️ SETTINGS
# ============================================
elif page=="⚙️ Settings":
    st.markdown("<h1>⚙️ Settings</h1>",unsafe_allow_html=True);st.markdown("---")
    st.markdown("### Change Password")
    with st.form("pwd"):
        cur=st.text_input("Current Password",type="password");new=st.text_input("New Password",type="password")
        if st.form_submit_button("Update Password",type="primary",use_container_width=True):
            if cur and new and len(new)>=8:
                c=get_db();r=c.execute("SELECT password FROM users WHERE username=? AND company_id=?",(st.session_state.user,cid)).fetchone()
                if r and SecurityEngine.verify_password(cur,r[0]): c.execute("UPDATE users SET password=? WHERE username=? AND company_id=?",(SecurityEngine.hash_password(new),st.session_state.user,cid));c.commit();st.success("✅ Password updated!")
                else: st.error("Current password incorrect")
                c.close()
    st.markdown("---")
    st.markdown("### Add Team Members")
    with st.form("add_team"):
        c1,c2=st.columns(2)
        with c1: nu=st.text_input("Username*");nf=st.text_input("Full Name")
        with c2: np=st.text_input("Password*",type="password");nr=st.selectbox("Role*",["driver","workshop","manager"])
        if st.form_submit_button("Add Team Member",type="primary",use_container_width=True):
            if nu and np and len(np)>=8:
                try:
                    c=get_db();c.execute("INSERT INTO users (username,password,role,full_name,company_id) VALUES (?,?,?,?,?)",(nu,SecurityEngine.hash_password(np),nr,nf,cid));c.commit();c.close()
                    st.success(f"✅ {nr.upper()} {nu} added!");st.rerun()
                except: st.error("Username already exists")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748b;">🚛 FleetPro 365 Enterprise • DVSA Compliant • Jobs • Invoices • Fuel • Maintenance • Alerts • White-Label</div>',unsafe_allow_html=True)
