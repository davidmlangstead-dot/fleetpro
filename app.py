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
from PIL import Image, ImageDraw, ImageFont
import sqlite3
from pathlib import Path
import os
import json

st.set_page_config(page_title="Enterprise Command Centre",layout="wide",page_icon="🏢",initial_sidebar_state="expanded")

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
.instruction-step{background:linear-gradient(135deg,rgba(59,130,246,0.1),rgba(139,92,246,0.05));border-left:4px solid #3b82f6;padding:16px 20px;border-radius:0 12px 12px 0;margin-bottom:12px}
.message-bubble{background:rgba(59,130,246,0.15);padding:12px 16px;border-radius:16px;margin-bottom:8px;max-width:80%}
.message-mine{background:rgba(16,185,129,0.15);margin-left:auto}
.task-pending{border-left:4px solid #f59e0b}
.task-done{border-left:4px solid #10b981;opacity:0.7}
.tacho-display{background:#000;border:3px solid #3b82f6;border-radius:20px;padding:20px;text-align:center}
.tacho-time{font-size:3em;font-weight:900;color:#10b981;font-family:'Courier New',monospace}
.tacho-label{color:#94a3b8;font-size:0.8em;text-transform:uppercase;letter-spacing:2px}
.channel-active{background:rgba(59,130,246,0.2);border-left:3px solid #3b82f6;padding:8px 12px;border-radius:8px;margin-bottom:4px}
.pinned-msg{background:rgba(245,158,11,0.1);border-left:3px solid #f59e0b;padding:10px 14px;border-radius:8px;margin-bottom:8px}
</style>
<script>
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js')}
Notification.requestPermission();
function notifyMe(title,body){if(Notification.permission==='granted'){new Notification(title,{body:body,icon:'🚛'})}}
</script>
""",unsafe_allow_html=True)

DB_PATH=Path(__file__).parent/"enterprise.db"
def get_db():
    conn=sqlite3.connect(str(DB_PATH));conn.row_factory=sqlite3.Row;return conn

conn=get_db()
conn.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, branding_color DEFAULT '#3b82f6', email_alerts TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'worker', full_name TEXT, phone TEXT, email TEXT, emergency_contact TEXT, company_id INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS sites (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, name TEXT, address TEXT, lat REAL, lon REAL, manager TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT, type TEXT, make TEXT, model TEXT, fleet_number TEXT, site_id INTEGER, company_id INTEGER, UNIQUE(reg, company_id))")
conn.execute("CREATE TABLE IF NOT EXISTS ops (id INTEGER PRIMARY KEY AUTOINCREMENT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reg TEXT, mileage REAL, status TEXT, notes TEXT, driver TEXT, company_id INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS shifts (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, site_id INTEGER, shift_date DATE, start_time TEXT, end_time TEXT, clock_in TIMESTAMP, clock_out TIMESTAMP, status TEXT DEFAULT 'Scheduled')")
conn.execute("CREATE TABLE IF NOT EXISTS certifications (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, cert_name TEXT, expiry_date DATE, status TEXT DEFAULT 'Valid')")
conn.execute("CREATE TABLE IF NOT EXISTS training (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, title TEXT, description TEXT, video_url TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS training_records (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, training_id INTEGER, completed_at TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS near_misses (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, site_id INTEGER, reporter TEXT, title TEXT, description TEXT, severity TEXT, category TEXT, location TEXT, photo_data TEXT, investigation TEXT, corrective_action TEXT, status TEXT DEFAULT 'Reported', reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS custom_forms (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, form_name TEXT, form_fields TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS form_submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, form_id INTEGER, submission_data TEXT, submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS lone_worker_checkins (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, site_id INTEGER, checkin_time TIMESTAMP, location TEXT, status TEXT DEFAULT 'Safe')")
conn.execute("CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, name TEXT, description TEXT, created_by INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, channel_id INTEGER, sender_id INTEGER, recipient_id INTEGER, subject TEXT, body TEXT, is_rich BOOLEAN DEFAULT 0, attachment_name TEXT, attachment_data TEXT, is_pinned BOOLEAN DEFAULT 0, read_by TEXT DEFAULT '[]', sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS calendar_events (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, title TEXT, description TEXT, event_date DATE, start_time TEXT, end_time TEXT, created_by INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, filename TEXT, description TEXT, uploaded_by INTEGER, file_data TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, title TEXT, description TEXT, assigned_to INTEGER, assigned_by INTEGER, priority TEXT DEFAULT 'Normal', status TEXT DEFAULT 'Pending', due_date DATE, completed_at TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, customer_name TEXT, description TEXT, status DEFAULT 'Pending', quoted_amount REAL)")
conn.execute("CREATE TABLE IF NOT EXISTS invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, job_id INTEGER, customer_name TEXT, total REAL, status DEFAULT 'Unpaid', due_date DATE)")
conn.execute("CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, vehicle_reg TEXT, service_type TEXT, due_date DATE, status DEFAULT 'Scheduled')")
conn.execute("CREATE TABLE IF NOT EXISTS fuel_log (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, vehicle_reg TEXT, date DATE, litres REAL, cost REAL, mileage REAL, mpg REAL, driver TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, category TEXT, amount REAL, description TEXT, receipt_data TEXT, status TEXT DEFAULT 'Pending', submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, item_name TEXT, category TEXT, quantity INTEGER, min_quantity INTEGER, location TEXT, unit_cost REAL, supplier TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS signatures (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, document_name TEXT, signed_by INTEGER, signature_data TEXT, signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS visitors (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, visitor_name TEXT, company_name TEXT, host_name TEXT, purpose TEXT, sign_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, sign_out_time TIMESTAMP, badge_number TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS ai_conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, question TEXT, answer TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit();conn.close()

class DB:
    def query(self,sql,params=None):
        c=get_db()
        try:return pd.read_sql_query(sql,c,params=params or())
        finally:c.close()
    def execute(self,sql,params=None):
        c=get_db()
        try:c.execute(sql,params or());c.commit()
        finally:c.close()

db=DB()
OPENAI_API_KEY='sk-proj-TC2fgnfimB9wR4k08IXW5g'

class Security:
    @staticmethod
    def hash(p):s=secrets.token_hex(16);return f"{s}${hashlib.sha256(f'{s}{p}'.encode()).hexdigest()}"
    @staticmethod
    def verify(p,h):
        try:s,hv=h.split('$');return hashlib.sha256(f'{s}{p}'.encode()).hexdigest()==hv
        except:return False

def ai_chat(question):
    if not OPENAI_API_KEY:return"AI offline"
    try:
        r=requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"},json={"model":"gpt-4o-mini","messages":[{"role":"system","content":"You are an enterprise assistant. Answer concisely. You can help with fleet, safety, HR, compliance, and business questions."},{"role":"user","content":question}],"max_tokens":300},timeout=15)
        return r.json()["choices"][0]["message"]["content"]
    except:return"AI unavailable"

class Analytics:
    @staticmethod
    def health(df):
        if df.empty:return 100.0
        t=len(df);vor=len(df[df['status'].str.contains('VOR|Dangerous',case=False,na=False)]);maj=len(df[df['status'].str.contains('Major',case=False,na=False)])
        return round(max(0,100-((vor*35+maj*15)/max(t,1))),1)
    @staticmethod
    def gen_gps(reg):
        random.seed(hash(reg)%100000)
        return{'lat':51.3+random.uniform(-1,1),'lon':-0.5+random.uniform(-1.2,1.2),'speed':random.randint(0,70)}

class TachoEngine:
    def __init__(self):
        if'ts'not in st.session_state:st.session_state.ts=None
        if'td'not in st.session_state:st.session_state.td=timedelta(0)
    def start(self):st.session_state.ts=datetime.now();st.session_state.td=timedelta(0)
    def stop(self):
        if st.session_state.ts:st.session_state.td+=datetime.now()-st.session_state.ts
        st.session_state.ts=None
    def status(self):
        md=timedelta(hours=4,minutes=30);mx=timedelta(hours=9)
        t=st.session_state.td
        if st.session_state.ts:t+=datetime.now()-st.session_state.ts
        tl=md-(t%md)if t>timedelta(0)else md;dl=mx-t
        w=""
        if dl<=timedelta(0):w="DAILY LIMIT EXCEEDED"
        elif dl<timedelta(hours=1):w=f"{int(dl.total_seconds()//60)}min left"
        elif tl<timedelta(minutes=15):w=f"BREAK in {int(tl.total_seconds()//60)}min"
        return{'total':t,'until_break':max(timedelta(0),tl),'day_left':max(timedelta(0),dl),'warning':w,'driving':st.session_state.ts is not None}

DVSA={"Structure":["Cab undamaged","Body panels secure","Doors working"],"Visibility":["Windscreen clear","Wipers OK","Mirrors clean"],"Lighting":["Headlights","Indicators","Brake lights"],"Tyres":["Tread legal","No cuts","Wheel nuts present"],"Brakes":["Service brake OK","Parking holds","No leaks"],"Engine":["Oil correct","Coolant correct","No leaks"],"Safety":["Seatbelts","Horn","Extinguisher","First aid"],"Load":["Load distributed","Load secured","Doors locked"]}
NEAR_MISS_CATEGORIES=["Slip/Trip/Fall","Vehicle/Plant","Manual Handling","Working at Height","Electrical","Fire/Explosion","Chemical Spill","Equipment Failure","Structural","Other"]
SEVERITY_LEVELS=["Low","Medium","High","Critical"]
EXPENSE_CATEGORIES=["Travel","Fuel","Accommodation","Equipment","Training","Office Supplies","Vehicle Repair","Other"]
INVENTORY_CATEGORIES=["Vehicle Parts","Tools","PPE","Office Supplies","Cleaning","Safety Equipment","Other"]

tacho=TachoEngine()

if"logged_in"not in st.session_state:
    st.session_state.logged_in=False;st.session_state.user=None;st.session_state.role=None;st.session_state.cid=None;st.session_state.current_channel=None

if not st.session_state.logged_in:
    c1,c2,c3=st.columns([1,2.5,1])
    with c2:
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;margin-bottom:40px;"><div style="font-size:4em;">🏢</div><h1 style="font-size:3em;font-weight:900;margin:0;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Enterprise Command</h1><p style="color:#94a3b8;font-size:1.1em;">FLEET • STAFF • SAFETY • WORKSPACE • AI • EXPENSES • INVENTORY</p></div>""",unsafe_allow_html=True)
        t1,t2=st.tabs(["Login","Register"])
        with t1:
            with st.form("login"):
                u=st.text_input("Username");p=st.text_input("Password",type="password")
                if st.form_submit_button("Login",type="primary",use_container_width=True):
                    c=get_db();r=c.execute("SELECT password,role,company_id FROM users WHERE username=?",(u,)).fetchone();c.close()
                    if r and Security.verify(p,r[0]):st.session_state.logged_in=True;st.session_state.user=u;st.session_state.role=r[1];st.session_state.cid=r[2];st.rerun()
                    else:st.error("Invalid credentials")
        with t2:
            with st.form("register"):
                co=st.text_input("Company*");au=st.text_input("Admin Username*");ap=st.text_input("Password*",type="password")
                if st.form_submit_button("Deploy",type="primary",use_container_width=True):
                    if not co or not au or not ap:st.error("Fill all fields")
                    elif len(ap)<8:st.error("Password: 8+ chars")
                    else:
                        try:
                            c=get_db();c.execute("INSERT INTO companies (name) VALUES (?)",(co,));cid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
                            c.execute("INSERT INTO users (username,password,role,company_id) VALUES (?,?,'admin',?)",(au,Security.hash(ap),cid))
                            c.execute("INSERT INTO channels (company_id,name,description,created_by) VALUES (?,'General','Company-wide',?)",(cid,cid))
                            c.commit();c.close()
                            st.success("✅ Deployed!");st.balloons()
                        except:st.error("Exists")
    st.stop()

cid=st.session_state.cid;role=st.session_state.role
def sq(sql,p=None):
    try:return db.query(sql,p)
    except:return pd.DataFrame()

with st.sidebar:
    st.markdown('<div style="text-align:center;"><h3 style="font-weight:900;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🏢 Enterprise</h3></div>',unsafe_allow_html=True)
    st.markdown(f"**{st.session_state.user}** ({role.upper()})")
    if role=="admin":
        page=st.radio("",["📖 Help","🏠 Command","🚛 Fleet","👥 Staff","⚠️ Near Miss","📍 Sites","🗺️ Map","💬 Chat","📅 Calendar","📁 Docs","✅ Tasks","🔧 Workshop","💰 Jobs","⛽ Fuel","🔔 Maintenance","🔍 Inspection","⏱️ Tacho","📸 Photos","🏆 Safety League","🎓 Training","📋 Forms","🆘 Lone Worker","🧠 AI Assistant","📊 BI Dashboard","🏦 Expenses","📝 Signatures","🛒 Inventory","👋 Visitors","📊 Compliance","📋 Reports","⚙️ Settings"],label_visibility="collapsed")
    elif role=="driver":page=st.radio("",["📖 Help","🔍 Inspection","⏱️ Tacho","📸 Photos","💬 Chat","🏦 Expenses"],label_visibility="collapsed")
    elif role=="worker":page=st.radio("",["📖 Help","⚠️ Near Miss","📸 Photos","👥 My Shifts","🆘 Lone Worker","💬 Chat","✅ Tasks","🏦 Expenses"],label_visibility="collapsed")
    elif role=="manager":page=st.radio("",["📖 Help","🏠 Command","⚠️ Near Miss","👥 Staff","📊 Compliance","🎓 Training","📋 Reports","💬 Chat","📅 Calendar","✅ Tasks","📊 BI Dashboard","🏦 Expenses","🛒 Inventory"],label_visibility="collapsed")
    else:page=st.radio("",["📖 Help","⚠️ Near Miss","💬 Chat"],label_visibility="collapsed")
    st.markdown("---")
    if st.button("Logout",use_container_width=True):st.session_state.clear();st.rerun()

# ============================================
if page=="🧠 AI Assistant":
    st.markdown("<h1>🧠 AI Assistant</h1><p style='color:#94a3b8;'>Ask me anything about your fleet, safety, compliance, or business</p>",unsafe_allow_html=True);st.markdown("---")
    
    # Quick prompts
    st.markdown("### Quick Actions")
    qp1,qp2,qp3,qp4=st.columns(4)
    with qp1:
        if st.button("📊 Fleet Health Report",use_container_width=True):st.session_state.ai_prompt="Give me a fleet health summary based on recent inspections"
    with qp2:
        if st.button("⚠️ Safety Analysis",use_container_width=True):st.session_state.ai_prompt="Analyze our near miss data and suggest top 3 safety improvements"
    with qp3:
        if st.button("📋 Generate Report",use_container_width=True):st.session_state.ai_prompt="Generate a monthly compliance summary report template"
    with qp4:
        if st.button("💡 Optimisation Tips",use_container_width=True):st.session_state.ai_prompt="How can we reduce fleet operating costs?"
    
    if 'ai_prompt' not in st.session_state:st.session_state.ai_prompt=""
    
    question=st.text_area("Ask AI Assistant",value=st.session_state.ai_prompt,placeholder="e.g., What's the most common defect in our fleet? How can I improve driver safety scores?",height=100)
    
    if st.button("🤖 Ask AI",type="primary",use_container_width=True):
        if question:
            with st.spinner("🧠 Thinking..."):
                answer=ai_chat(question)
                uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0]
                db.execute("INSERT INTO ai_conversations (company_id,user_id,question,answer) VALUES (?,?,?,?)",(cid,uid,question,answer))
                st.markdown(f'<div class="glass-card" style="padding:20px;"><b>🤖 AI Response:</b><br><br>{answer}</div>',unsafe_allow_html=True)
                st.session_state.ai_prompt=""
    
    st.markdown("---")
    st.markdown("### Recent Conversations")
    convos=sq("SELECT * FROM ai_conversations WHERE company_id=? ORDER BY created_at DESC LIMIT 10",(cid,))
    if not convos.empty:
        for _,c in convos.iterrows():
            with st.expander(f"Q: {c['question'][:80]}... — {c['created_at']}"):st.write(c['answer'])

elif page=="📊 BI Dashboard":
    st.markdown("<h1>📊 BI Dashboard Builder</h1>",unsafe_allow_html=True);st.markdown("---")
    
    chart_type=st.selectbox("Chart Type",["Bar Chart","Line Chart","Pie Chart","Scatter Plot","Metric Card"])
    
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,))
    nm=sq("SELECT * FROM near_misses WHERE company_id=?",(cid,))
    
    if chart_type=="Metric Card":
        metric=st.selectbox("Metric",["Fleet Health","Total Inspections","Open Near Misses","Open Tasks","Vehicles","Staff Count"])
        val=Analytics.health(ops) if metric=="Fleet Health" else len(ops) if metric=="Total Inspections" else len(nm[nm['status']=='Reported']) if metric=="Open Near Misses" else len(sq("SELECT * FROM tasks WHERE company_id=? AND status!='Completed'",(cid,))) if metric=="Open Tasks" else sq("SELECT COUNT(*) as c FROM vehicles WHERE company_id=?",(cid,)).iloc[0,0] if metric=="Vehicles" else sq("SELECT COUNT(*) as c FROM users WHERE company_id=?",(cid,)).iloc[0,0]
        st.markdown(f'<div class="metric-card"><div class="metric-label">{metric}</div><div class="metric-value">{val}{"%" if metric=="Fleet Health" else ""}</div></div>',unsafe_allow_html=True)
    
    elif chart_type=="Bar Chart":
        if not ops.empty:
            ops['date']=pd.to_datetime(ops['time']).dt.date
            daily=ops.groupby('date').size().tail(30)
            fig=go.Figure(go.Bar(x=daily.index,y=daily.values,marker_color='#3b82f6'))
            fig.update_layout(template='plotly_dark',height=400,title="Daily Inspections")
            st.plotly_chart(fig,use_container_width=True)
    
    elif chart_type=="Pie Chart":
        if not nm.empty:
            cats=nm['category'].value_counts()
            fig=go.Figure(go.Pie(labels=cats.index,values=cats.values,hole=0.4))
            fig.update_layout(template='plotly_dark',height=400,title="Near Miss Categories")
            st.plotly_chart(fig,use_container_width=True)
    
    st.markdown("---")
    st.caption("💡 More chart types coming soon. Data updates in real-time from your database.")

elif page=="🏦 Expenses":
    st.markdown("<h1>🏦 Expense Management</h1>",unsafe_allow_html=True);st.markdown("---")
    tab_e1,tab_e2=st.tabs(["📝 Submit Expense","📊 Expense Log"])
    with tab_e1:
        with st.form("expense"):
            cat=st.selectbox("Category*",EXPENSE_CATEGORIES);amt=st.number_input("Amount (£)*",0.0,100000.0,0.0);desc=st.text_area("Description*");receipt=st.camera_input("Receipt Photo")
            if st.form_submit_button("Submit Expense",type="primary",use_container_width=True):
                if amt>0 and desc:
                    uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0]
                    rec_data=None
                    if receipt:img=Image.open(receipt);buf=BytesIO();img.save(buf,format="PNG");rec_data=base64.b64encode(buf.getvalue()).decode()[:2000]
                    db.execute("INSERT INTO expenses (company_id,user_id,category,amount,description,receipt_data) VALUES (?,?,?,?,?,?)",(cid,uid,cat,amt,desc,rec_data))
                    st.success("✅ Expense submitted!");st.rerun()
    with tab_e2:
        expenses=sq("SELECT e.*, u.full_name FROM expenses e JOIN users u ON e.user_id=u.id WHERE e.company_id=? ORDER BY e.submitted_at DESC LIMIT 30",(cid,))
        if not expenses.empty:
            total=expenses[expenses['status']=='Approved']['amount'].sum()
            st.metric("Total Approved",f"£{total:,.2f}")
            for _,e in expenses.iterrows():
                sts='🟢' if e['status']=='Approved' else '🟡' if e['status']=='Pending' else '🔴'
                st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;">{sts} <b>£{e["amount"]:,.2f}</b> — {e["category"]} — {e["full_name"]}<br><span style="color:#94a3b8;">{e["description"][:80]}</span></div>',unsafe_allow_html=True)

elif page=="📝 Signatures":
    st.markdown("<h1>📝 Digital Signatures</h1>",unsafe_allow_html=True);st.markdown("---")
    tab_s1,tab_s2=st.tabs(["✍️ Sign Document","📋 Signed Documents"])
    with tab_s1:
        doc_name=st.text_input("Document Name*","e.g., Employment Contract, Safety Acknowledgment")
        st.markdown("### Draw Your Signature")
        from streamlit_drawable_canvas import st_canvas
        try:
            canvas_result=st_canvas(fill_color="rgba(255,255,255,0)",stroke_width=3,stroke_color="#ffffff",background_color="#000000",height=200,width=500,drawing_mode="freedraw",key="signature")
            if st.button("💾 Save Signature",type="primary",use_container_width=True):
                if canvas_result.image_data is not None and doc_name:
                    img=Image.fromarray(canvas_result.image_data.astype('uint8'),'RGBA');buf=BytesIO();img.save(buf,format="PNG");sig_data=base64.b64encode(buf.getvalue()).decode()
                    uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0]
                    db.execute("INSERT INTO signatures (company_id,document_name,signed_by,signature_data) VALUES (?,?,?,?)",(cid,doc_name,uid,sig_data))
                    st.success("✅ Document signed!");st.rerun()
        except:st.info("📝 Signature pad — draw your signature above")
    with tab_s2:
        sigs=sq("SELECT s.*, u.full_name FROM signatures s JOIN users u ON s.signed_by=u.id WHERE s.company_id=? ORDER BY s.signed_at DESC",(cid,))
        if not sigs.empty:
            for _,s in sigs.iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>📝 {s["document_name"]}</b> — Signed by {s["full_name"]} — {s["signed_at"]}</div>',unsafe_allow_html=True)

elif page=="🛒 Inventory":
    st.markdown("<h1>🛒 Inventory & Asset Tracking</h1>",unsafe_allow_html=True);st.markdown("---")
    tab_i1,tab_i2=st.tabs(["➕ Add Item","📊 Inventory List"])
    with tab_i1:
        with st.form("inv"):
            name=st.text_input("Item Name*");cat=st.selectbox("Category",INVENTORY_CATEGORIES);qty=st.number_input("Quantity",0,99999,1);min_q=st.number_input("Min Stock Alert",0,99999,5);loc=st.text_input("Location");cost=st.number_input("Unit Cost (£)",0.0,100000.0,0.0);supplier=st.text_input("Supplier")
            if st.form_submit_button("Add Item",type="primary",use_container_width=True):
                if name:db.execute("INSERT INTO inventory (company_id,item_name,category,quantity,min_quantity,location,unit_cost,supplier) VALUES (?,?,?,?,?,?,?,?)",(cid,name,cat,qty,min_q,loc,cost,supplier));st.success("✅ Added!");st.rerun()
    with tab_i2:
        inv=sq("SELECT * FROM inventory WHERE company_id=? ORDER BY category,item_name",(cid,))
        if not inv.empty:
            low=inv[inv['quantity']<=inv['min_quantity']]
            if not low.empty:st.error(f"⚠️ {len(low)} items below minimum stock!")
            total_value=(inv['quantity']*inv['unit_cost']).sum()
            st.metric("Total Inventory Value",f"£{total_value:,.2f}")
            for _,i in inv.iterrows():
                cl='#ef4444' if i['quantity']<=i['min_quantity'] else '#10b981'
                st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{i["item_name"]}</b> — Qty: <span style="color:{cl};">{i["quantity"]}</span> — {i["location"]} — £{i["unit_cost"]:,.2f} each</div>',unsafe_allow_html=True)

elif page=="👋 Visitors":
    st.markdown("<h1>👋 Visitor Management</h1>",unsafe_allow_html=True);st.markdown("---")
    tab_v1,tab_v2=st.tabs(["📝 Sign In","📊 Visitor Log"])
    with tab_v1:
        with st.form("visitor"):
            vn=st.text_input("Visitor Name*");vc=st.text_input("Company");host=st.text_input("Host Name");purpose=st.text_input("Purpose")
            if st.form_submit_button("Sign In",type="primary",use_container_width=True):
                if vn:badge=f"VIS-{random.randint(1000,9999)}";db.execute("INSERT INTO visitors (company_id,visitor_name,company_name,host_name,purpose,badge_number) VALUES (?,?,?,?,?,?)",(cid,vn,vc,host,purpose,badge));st.success(f"✅ Signed in! Badge: {badge}");st.rerun()
    with tab_v2:
        visitors=sq("SELECT * FROM visitors WHERE company_id=? AND sign_out_time IS NULL ORDER BY sign_in_time DESC",(cid,))
        if not visitors.empty:
            st.markdown(f"### Currently On Site ({len(visitors)})")
            for _,v in visitors.iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{v["visitor_name"]}</b> — {v["company_name"]} — Host: {v["host_name"]} — Badge: {v["badge_number"]} — {v["sign_in_time"]}</div>',unsafe_allow_html=True)
            if st.button("🚪 Sign Out All",use_container_width=True):db.execute("UPDATE visitors SET sign_out_time=? WHERE company_id=? AND sign_out_time IS NULL",(datetime.now(),cid));st.success("✅ Signed out!");st.rerun()

elif page=="📖 Help":st.markdown("<h1>📖 Help Guide</h1>",unsafe_allow_html=True)
elif page=="🏠 Command":st.markdown("<h1>🏠 Command Centre</h1>",unsafe_allow_html=True)
elif page=="🚛 Fleet":st.markdown("<h1>🚛 Fleet</h1>",unsafe_allow_html=True)
elif page=="👥 Staff":st.markdown("<h1>👥 Staff</h1>",unsafe_allow_html=True)
elif page=="⚠️ Near Miss":st.markdown("<h1>⚠️ Near Miss</h1>",unsafe_allow_html=True)
elif page=="📍 Sites":st.markdown("<h1>📍 Sites</h1>",unsafe_allow_html=True)
elif page=="🗺️ Map":st.markdown("<h1>🗺️ Map</h1>",unsafe_allow_html=True)
elif page=="💬 Chat":st.markdown("<h1>💬 Chat</h1>",unsafe_allow_html=True)
elif page=="📅 Calendar":st.markdown("<h1>📅 Calendar</h1>",unsafe_allow_html=True)
elif page=="📁 Docs":st.markdown("<h1>📁 Docs</h1>",unsafe_allow_html=True)
elif page=="✅ Tasks":st.markdown("<h1>✅ Tasks</h1>",unsafe_allow_html=True)
elif page=="🔧 Workshop":st.markdown("<h1>🔧 Workshop</h1>",unsafe_allow_html=True)
elif page=="💰 Jobs":st.markdown("<h1>💰 Jobs</h1>",unsafe_allow_html=True)
elif page=="⛽ Fuel":st.markdown("<h1>⛽ Fuel</h1>",unsafe_allow_html=True)
elif page=="🔔 Maintenance":st.markdown("<h1>🔔 Maintenance</h1>",unsafe_allow_html=True)
elif page=="🔍 Inspection":st.markdown("<h1>🔍 Inspection</h1>",unsafe_allow_html=True)
elif page=="⏱️ Tacho":st.markdown("<h1>⏱️ Tacho</h1>",unsafe_allow_html=True)
elif page=="📸 Photos":st.markdown("<h1>📸 Photos</h1>",unsafe_allow_html=True)
elif page=="🏆 Safety League":st.markdown("<h1>🏆 Safety League</h1>",unsafe_allow_html=True)
elif page=="🎓 Training":st.markdown("<h1>🎓 Training</h1>",unsafe_allow_html=True)
elif page=="📋 Forms":st.markdown("<h1>📋 Forms</h1>",unsafe_allow_html=True)
elif page=="🆘 Lone Worker":st.markdown("<h1>🆘 Lone Worker</h1>",unsafe_allow_html=True)
elif page=="📊 Compliance":st.markdown("<h1>📊 Compliance</h1>",unsafe_allow_html=True)
elif page=="📋 Reports":st.markdown("<h1>📋 Reports</h1>",unsafe_allow_html=True)

elif page=="⚙️ Settings":
    st.markdown("<h1>⚙️ Settings</h1>",unsafe_allow_html=True)
    with st.form("pwd"):
        cur=st.text_input("Current",type="password");new=st.text_input("New",type="password")
        if st.form_submit_button("Update",type="primary"):
            if cur and new and len(new)>=8:
                c=get_db();r=c.execute("SELECT password FROM users WHERE username=? AND company_id=?",(st.session_state.user,cid)).fetchone()
                if r and Security.verify(cur,r[0]):c.execute("UPDATE users SET password=? WHERE username=? AND company_id=?",(Security.hash(new),st.session_state.user,cid));c.commit();st.success("✅ Done!")
                else:st.error("Wrong password")
                c.close()

elif page=="👥 My Shifts":st.markdown("<h1>👥 My Shifts</h1>",unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748b;">🏢 Enterprise Command Centre • Fleet • Staff • Safety • Workspace • AI • Expenses • Inventory • Visitors • Signatures</div>',unsafe_allow_html=True)
