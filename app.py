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
import json

st.set_page_config(page_title="Enterprise Command Centre",layout="wide",page_icon="🏢",initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{font-family:'Inter',sans-serif}
.stApp{background:linear-gradient(145deg,#0a0e27 0%,#1a1040 100%);background-attachment:fixed}
.glass-card{background:linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01));backdrop-filter:blur(30px);border:1px solid rgba(255,255,255,0.06);border-radius:20px;padding:24px}
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
</style>
""",unsafe_allow_html=True)

DB_PATH=Path(__file__).parent/"enterprise.db"
def get_db():
    conn=sqlite3.connect(str(DB_PATH));conn.row_factory=sqlite3.Row;return conn

conn=get_db()
tables=["companies","users","sites","vehicles","ops","shifts","certifications","training","training_records","near_misses","custom_forms","form_submissions","lone_worker_checkins","channels","messages","calendar_events","documents","tasks","jobs","invoices","maintenance","fuel_log","expenses","inventory","signatures","visitors","ai_conversations"]
for t in tables:conn.execute(f"CREATE TABLE IF NOT EXISTS {t} (id INTEGER PRIMARY KEY AUTOINCREMENT)")
conn.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'worker', full_name TEXT, company_id INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT, type TEXT, company_id INTEGER, UNIQUE(reg, company_id))")
conn.execute("CREATE TABLE IF NOT EXISTS ops (id INTEGER PRIMARY KEY AUTOINCREMENT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reg TEXT, mileage REAL, status TEXT, notes TEXT, driver TEXT, company_id INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS near_misses (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, reporter TEXT, title TEXT, description TEXT, severity TEXT, category TEXT, status TEXT DEFAULT 'Reported', reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, name TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, channel_id INTEGER, sender_id INTEGER, body TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, title TEXT, assigned_to INTEGER, status TEXT DEFAULT 'Pending', due_date DATE)")
conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, customer_name TEXT, description TEXT, quoted_amount REAL, status DEFAULT 'Pending')")
conn.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_id INTEGER, category TEXT, amount REAL, description TEXT, status DEFAULT 'Pending')")
conn.execute("CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, item_name TEXT, quantity INTEGER, min_quantity INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS signatures (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, document_name TEXT, signed_by INTEGER, signature_data TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS visitors (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, visitor_name TEXT, company_name TEXT, sign_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS ai_conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, question TEXT, answer TEXT)")
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

def ai_chat(q):
    if not OPENAI_API_KEY:return"AI offline"
    try:
        r=requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"},json={"model":"gpt-4o-mini","messages":[{"role":"system","content":"Enterprise assistant. Be concise."},{"role":"user","content":q}],"max_tokens":300},timeout=15)
        return r.json()["choices"][0]["message"]["content"]
    except:return"AI unavailable"

class Analytics:
    @staticmethod
    def health(df):
        if df.empty:return 100.0
        t=len(df);vor=len(df[df['status'].str.contains('VOR|Dangerous',case=False,na=False)])
        return round(max(0,100-((vor*35)/max(t,1))),1)
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
        return{'total':t,'until_break':max(timedelta(0),tl),'day_left':max(timedelta(0),dl),'warning':w,'driving':st.session_state.ts is not None}

DVSA={"Structure":["Cab undamaged","Body panels secure","Doors working"],"Visibility":["Windscreen clear","Wipers OK","Mirrors clean"],"Lighting":["Headlights","Indicators","Brake lights"],"Tyres":["Tread legal","No cuts","Wheel nuts present"],"Brakes":["Service brake OK","Parking holds","No leaks"],"Engine":["Oil correct","Coolant correct","No leaks"],"Safety":["Seatbelts","Horn","Extinguisher","First aid"],"Load":["Load distributed","Load secured","Doors locked"]}
NEAR_MISS_CATEGORIES=["Slip/Trip/Fall","Vehicle/Plant","Manual Handling","Working at Height","Electrical","Fire/Explosion","Chemical Spill","Equipment Failure","Structural","Other"]
SEVERITY_LEVELS=["Low","Medium","High","Critical"]

tacho=TachoEngine()

if"logged_in"not in st.session_state:
    st.session_state.logged_in=False;st.session_state.user=None;st.session_state.role=None;st.session_state.cid=None

if not st.session_state.logged_in:
    c1,c2,c3=st.columns([1,2.5,1])
    with c2:
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;margin-bottom:40px;"><div style="font-size:4em;">🏢</div><h1 style="font-size:3em;font-weight:900;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Enterprise Command</h1><p style="color:#94a3b8;">FLEET • STAFF • SAFETY • AI • EXPENSES • INVENTORY</p></div>""",unsafe_allow_html=True)
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
                            c.execute("INSERT INTO users (username,password,role,company_id) VALUES (?,?,'admin',?)",(au,Security.hash(ap),cid));c.commit();c.close()
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
        page=st.radio("",["🏠 Command","🚛 Fleet","👥 Staff","⚠️ Near Miss","💬 Chat","✅ Tasks","💰 Jobs","🏦 Expenses","🛒 Inventory","📝 Signatures","👋 Visitors","🧠 AI","📊 BI","🔍 Inspection","⏱️ Tacho","📊 Compliance","📋 Reports","⚙️ Settings"],label_visibility="collapsed")
    else:page=st.radio("",["🏠 Command","⚠️ Near Miss","💬 Chat","🔍 Inspection","⏱️ Tacho"],label_visibility="collapsed")
    st.markdown("---")
    if st.button("Logout",use_container_width=True):st.session_state.clear();st.rerun()

# ============================================
# 🏠 COMMAND
# ============================================
if page=="🏠 Command":
    st.markdown(f"<h1>Command Centre</h1><p style='color:#94a3b8;'>{datetime.now().strftime('%A, %d %B %Y — %H:%M')}</p>",unsafe_allow_html=True);st.markdown("---")
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,));nm=sq("SELECT * FROM near_misses WHERE company_id=?",(cid,))
    vc=sq("SELECT COUNT(*) as c FROM vehicles WHERE company_id=?",(cid,)).iloc[0,0];sc=sq("SELECT COUNT(*) as c FROM users WHERE company_id=?",(cid,)).iloc[0,0]
    c1,c2,c3,c4=st.columns(4)
    with c1:st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{Analytics.health(ops)}%</div></div>',unsafe_allow_html=True)
    with c2:st.markdown(f'<div class="metric-card"><div class="metric-label">Vehicles</div><div class="metric-value">{vc}</div></div>',unsafe_allow_html=True)
    with c3:st.markdown(f'<div class="metric-card"><div class="metric-label">Team</div><div class="metric-value">{sc}</div></div>',unsafe_allow_html=True)
    with c4:st.markdown(f'<div class="metric-card"><div class="metric-label">Open Near Misses</div><div class="metric-value">{len(nm[nm["status"]=="Reported"]) if not nm.empty else 0}</div></div>',unsafe_allow_html=True)

# ============================================
# 🚛 FLEET
# ============================================
elif page=="🚛 Fleet":
    st.markdown("<h1>🚛 Fleet Registry</h1>",unsafe_allow_html=True)
    veh=sq("SELECT * FROM vehicles WHERE company_id=?",(cid,))
    if not veh.empty:
        for _,v in veh.iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{v["reg"]}</b> — {v.get("type","N/A")}</div>',unsafe_allow_html=True)
    with st.form("add_v"):
        reg=st.text_input("Reg*").upper();t=st.selectbox("Type*",["HGV","Van","Car"])
        if st.form_submit_button("Add",type="primary",use_container_width=True):
            if reg:
                try:c=get_db();c.execute("INSERT INTO vehicles (reg,type,company_id) VALUES (?,?,?)",(reg,t,cid));c.commit();c.close();st.success(f"✅ {reg} added!");st.rerun()
                except:st.error("Exists")

# ============================================
# 👥 STAFF
# ============================================
elif page=="👥 Staff":
    st.markdown("<h1>👥 Staff</h1>",unsafe_allow_html=True)
    staff=sq("SELECT * FROM users WHERE company_id=?",(cid,))
    if not staff.empty:st.dataframe(staff[['username','full_name','role']],use_container_width=True,hide_index=True)
    with st.form("add_staff"):
        nu=st.text_input("Username*");np=st.text_input("Password*",type="password");nr=st.selectbox("Role*",["worker","driver","workshop","manager"])
        if st.form_submit_button("Add",type="primary",use_container_width=True):
            if nu and np and len(np)>=8:
                try:c=get_db();c.execute("INSERT INTO users (username,password,role,company_id) VALUES (?,?,?,?)",(nu,Security.hash(np),nr,cid));c.commit();c.close();st.success(f"✅ {nu} added!");st.rerun()
                except:st.error("Exists")

# ============================================
# ⚠️ NEAR MISS
# ============================================
elif page=="⚠️ Near Miss":
    st.markdown("<h1>⚠️ Near Miss Reporting</h1>",unsafe_allow_html=True)
    with st.form("near_miss"):
        title=st.text_input("Title*");desc=st.text_area("Description*");cat=st.selectbox("Category*",NEAR_MISS_CATEGORIES);sev=st.selectbox("Severity*",SEVERITY_LEVELS);reporter=st.text_input("Reporter*",value=st.session_state.user)
        if st.form_submit_button("Submit",type="primary",use_container_width=True):
            if title and desc:db.execute("INSERT INTO near_misses (company_id,reporter,title,description,severity,category) VALUES (?,?,?,?,?,?)",(cid,reporter,title,desc,sev,cat));st.success("✅ Reported!");st.rerun()
    nm=sq("SELECT * FROM near_misses WHERE company_id=? ORDER BY reported_at DESC",(cid,))
    if not nm.empty:
        for _,n in nm.head(20).iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{n["title"]}</b> — {n["severity"]}</div>',unsafe_allow_html=True)

# ============================================
# 💬 CHAT
# ============================================
elif page=="💬 Chat":
    st.markdown("<h1>💬 Team Chat</h1>",unsafe_allow_html=True)
    uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0]
    msgs=sq("SELECT m.*, u.full_name FROM messages m JOIN users u ON m.sender_id=u.id WHERE m.company_id=? ORDER BY m.sent_at DESC LIMIT 30",(cid,))
    if not msgs.empty:
        for _,m in msgs[::-1].iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{m["full_name"]}</b>: {m["body"][:200]}</div>',unsafe_allow_html=True)
    with st.form("chat"):
        body=st.text_area("Message")
        if st.form_submit_button("Send",type="primary",use_container_width=True):
            if body:db.execute("INSERT INTO messages (company_id,channel_id,sender_id,body) VALUES (?,1,?,?)",(cid,uid,body));st.rerun()

# ============================================
# ✅ TASKS
# ============================================
elif page=="✅ Tasks":
    st.markdown("<h1>✅ Tasks</h1>",unsafe_allow_html=True)
    with st.form("add_task"):
        title=st.text_input("Task*");priority=st.selectbox("Priority",["Low","Normal","High"]);due=st.date_input("Due")
        if st.form_submit_button("Create",type="primary",use_container_width=True):
            if title:db.execute("INSERT INTO tasks (company_id,title,priority,due_date) VALUES (?,?,?,?)",(cid,title,priority,due.strftime('%Y-%m-%d')));st.success("✅ Created!");st.rerun()
    tasks=sq("SELECT * FROM tasks WHERE company_id=? ORDER BY due_date",(cid,))
    if not tasks.empty:
        for _,t in tasks.iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;">{"✅" if t["status"]=="Completed" else "⏳"} {t["title"]} — Due: {t["due_date"]}</div>',unsafe_allow_html=True)

# ============================================
# 💰 JOBS
# ============================================
elif page=="💰 Jobs":
    st.markdown("<h1>💰 Jobs & Invoicing</h1>",unsafe_allow_html=True)
    with st.form("new_job"):
        cn=st.text_input("Customer*");de=st.text_area("Description*");qa=st.number_input("Quote (£)",0.0,100000.0,0.0)
        if st.form_submit_button("Create",type="primary",use_container_width=True):
            if cn and de:db.execute("INSERT INTO jobs (company_id,customer_name,description,quoted_amount) VALUES (?,?,?,?)",(cid,cn,de,qa));st.success("✅ Created!");st.rerun()
    jobs=sq("SELECT * FROM jobs WHERE company_id=?",(cid,))
    if not jobs.empty:
        for _,j in jobs.iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{j["customer_name"]}</b> — £{j["quoted_amount"]:,.2f} — {j["status"]}</div>',unsafe_allow_html=True)

# ============================================
# 🏦 EXPENSES
# ============================================
elif page=="🏦 Expenses":
    st.markdown("<h1>🏦 Expenses</h1>",unsafe_allow_html=True)
    with st.form("expense"):
        cat=st.selectbox("Category",["Travel","Fuel","Equipment","Office","Other"]);amt=st.number_input("Amount (£)",0.0,10000.0,0.0);desc=st.text_area("Description")
        if st.form_submit_button("Submit",type="primary",use_container_width=True):
            if amt>0:uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0];db.execute("INSERT INTO expenses (company_id,user_id,category,amount,description) VALUES (?,?,?,?,?)",(cid,uid,cat,amt,desc));st.success("✅ Submitted!");st.rerun()
    exp=sq("SELECT * FROM expenses WHERE company_id=? ORDER BY rowid DESC LIMIT 20",(cid,))
    if not exp.empty:
        for _,e in exp.iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>£{e["amount"]:,.2f}</b> — {e["category"]} — {e["description"][:50]}</div>',unsafe_allow_html=True)

# ============================================
# 🛒 INVENTORY
# ============================================
elif page=="🛒 Inventory":
    st.markdown("<h1>🛒 Inventory</h1>",unsafe_allow_html=True)
    with st.form("inv"):
        name=st.text_input("Item*");qty=st.number_input("Qty",0,99999,1);minq=st.number_input("Min Stock",0,99999,5)
        if st.form_submit_button("Add",type="primary",use_container_width=True):
            if name:db.execute("INSERT INTO inventory (company_id,item_name,quantity,min_quantity) VALUES (?,?,?,?)",(cid,name,qty,minq));st.success("✅ Added!");st.rerun()
    inv=sq("SELECT * FROM inventory WHERE company_id=?",(cid,))
    if not inv.empty:
        for _,i in inv.iterrows():cl='#ef4444' if i['quantity']<=i['min_quantity'] else '#10b981';st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{i["item_name"]}</b> — <span style="color:{cl};">{i["quantity"]}</span></div>',unsafe_allow_html=True)

# ============================================
# 📝 SIGNATURES
# ============================================
elif page=="📝 Signatures":
    st.markdown("<h1>📝 Digital Signatures</h1>",unsafe_allow_html=True)
    doc=st.text_input("Document Name*");sig=st.text_input("Type Full Name to Sign*")
    if st.button("✍️ Sign",type="primary",use_container_width=True):
        if doc and sig:uid=sq("SELECT id FROM users WHERE username=?",(st.session_state.user,)).iloc[0,0];db.execute("INSERT INTO signatures (company_id,document_name,signed_by,signature_data) VALUES (?,?,?,?)",(cid,doc,uid,sig));st.success("✅ Signed!");st.rerun()

# ============================================
# 👋 VISITORS
# ============================================
elif page=="👋 Visitors":
    st.markdown("<h1>👋 Visitor Management</h1>",unsafe_allow_html=True)
    with st.form("visitor"):
        vn=st.text_input("Name*");vc=st.text_input("Company")
        if st.form_submit_button("Sign In",type="primary",use_container_width=True):
            if vn:db.execute("INSERT INTO visitors (company_id,visitor_name,company_name) VALUES (?,?,?)",(cid,vn,vc));st.success(f"✅ Signed in!");st.rerun()
    vis=sq("SELECT * FROM visitors WHERE company_id=? ORDER BY sign_in_time DESC LIMIT 20",(cid,))
    if not vis.empty:
        for _,v in vis.iterrows():st.markdown(f'<div class="glass-card" style="margin-bottom:4px;padding:10px;"><b>{v["visitor_name"]}</b> — {v["company_name"]} — {v["sign_in_time"]}</div>',unsafe_allow_html=True)

# ============================================
# 🧠 AI
# ============================================
elif page=="🧠 AI":
    st.markdown("<h1>🧠 AI Assistant</h1>",unsafe_allow_html=True)
    q=st.text_area("Ask anything","How can I improve fleet safety?")
    if st.button("🤖 Ask AI",type="primary",use_container_width=True):
        if q:
            with st.spinner("Thinking..."):a=ai_chat(q);st.info(a);db.execute("INSERT INTO ai_conversations (company_id,question,answer) VALUES (?,?,?)",(cid,q,a))

# ============================================
# 📊 BI
# ============================================
elif page=="📊 BI":
    st.markdown("<h1>📊 BI Dashboard</h1>",unsafe_allow_html=True)
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,))
    if not ops.empty:
        ops['date']=pd.to_datetime(ops['time']).dt.date;daily=ops.groupby('date').size().tail(30)
        fig=go.Figure(go.Bar(x=daily.index,y=daily.values,marker_color='#3b82f6'))
        fig.update_layout(template='plotly_dark',height=400);st.plotly_chart(fig,use_container_width=True)

# ============================================
# REMAINING PAGES
# ============================================
elif page=="🔍 Inspection":
    st.markdown("<h1>🔍 DVSA Walkaround</h1>",unsafe_allow_html=True)
    vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,))
    if vehs.empty:st.warning("No vehicles");st.stop()
    with st.form("insp"):
        reg=st.selectbox("Vehicle",vehs['reg'].tolist());mil=st.number_input("Mileage",0,step=1000)
        chk={}
        for cat,items in DVSA.items():
            st.markdown(f"**{cat}**");cs=st.columns(3)
            for i,it in enumerate(items):
                with cs[i%3]:chk[it]=st.checkbox(it,value=True)
        ok=all(chk.values());nt=""
        if not ok:fl=[i for i,c in chk.items() if not c];st.error(f"Defects: {', '.join(fl)}");nt=st.text_area("Description*",height=100);sv=st.selectbox("Severity*",["Minor","Major","VOR"])
        sg=st.text_input("Signature*")
        if st.form_submit_button("Submit",type="primary",use_container_width=True):
            if not ok and not nt:st.error("Description required")
            elif not sg:st.error("Signature required")
            else:
                sts="PASS" if ok else f"DEFECT - {sv}"
                c=get_db();c.execute("INSERT INTO ops (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,?,?,?,?,?)",(datetime.now(),reg,mil,sts,nt or"Passed",st.session_state.user,cid));c.commit();c.close()
                if ok:st.success("PASS!");st.balloons()
                else:st.warning("Defect logged")
                time.sleep(2);st.rerun()

elif page=="⏱️ Tacho":
    st.markdown("<h1>⏱️ Tacho</h1>",unsafe_allow_html=True)
    s=tacho.status()
    c1,c2,c3=st.columns(3)
    with c1:h=int(s['total'].total_seconds()//3600);m=int((s['total'].total_seconds()%3600)//60);st.markdown(f'<div class="tacho-display"><div class="tacho-label">DRIVING</div><div class="tacho-time">{h:02d}:{m:02d}</div></div>',unsafe_allow_html=True)
    with c2:bh=int(s['until_break'].total_seconds()//3600);bm=int((s['until_break'].total_seconds()%3600)//60);st.markdown(f'<div class="tacho-display"><div class="tacho-label">BREAK IN</div><div class="tacho-time">{bh:02d}:{bm:02d}</div></div>',unsafe_allow_html=True)
    with c3:dh=int(max(timedelta(0),s['day_left']).total_seconds()//3600);dm=int((max(timedelta(0),s['day_left']).total_seconds()%3600)//60);st.markdown(f'<div class="tacho-display"><div class="tacho-label">DAY LEFT</div><div class="tacho-time">{dh:02d}:{dm:02d}</div></div>',unsafe_allow_html=True)
    if s['warning']:st.error(s['warning'])
    cc1,cc2=st.columns(2)
    with cc1:
        if not s['driving']:
            if st.button("🟢 Start",type="primary",use_container_width=True):tacho.start();st.rerun()
        else:
            if st.button("🔴 Stop",use_container_width=True):tacho.stop();st.rerun()
    with cc2:
        if st.button("🌙 Reset",use_container_width=True):tacho.stop();st.session_state.td=timedelta(0);st.rerun()

elif page=="📊 Compliance":st.markdown("<h1>📊 Compliance</h1>",unsafe_allow_html=True)
elif page=="📋 Reports":
    st.markdown("<h1>📋 Reports</h1>",unsafe_allow_html=True)
    ops=sq("SELECT * FROM ops WHERE company_id=?",(cid,))
    if not ops.empty:st.download_button("📊 CSV",ops.to_csv(index=False),"report.csv")
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

st.markdown("---")
st.markdown('<div style="text-align:center;color:#64748b;">🏢 Enterprise Command Centre • Fleet • Staff • Safety • AI • Expenses • Inventory</div>',unsafe_allow_html=True)
