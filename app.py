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

st.set_page_config(
    page_title="Enterprise Command Centre",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': 'Enterprise Command Centre — Fleet, Staff, Safety, AI'
    }
)

# PWA Manifest Injection
st.markdown("""
<link rel="manifest" href="data:application/json,{""" + f""""name":"Enterprise Command Centre","short_name":"Enterprise","start_url":"/","display":"standalone","background_color":"#0a0a0f","theme_color":"#4f6ef7","icons":[{{"src":"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏢</text></svg>","sizes":"100x100","type":"image/svg+xml"}}]""" + """}">
<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
    });
}
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
});
</script>
""", unsafe_allow_html=True)

# Install prompt banner
st.markdown("""
<div id="installBanner" style="display:none;background:linear-gradient(135deg,#4f6ef7,#8b5cf6);color:white;padding:12px 20px;border-radius:12px;margin-bottom:16px;text-align:center;cursor:pointer;font-weight:600;">
    📲 Install this app on your device — tap here
</div>
<script>
window.addEventListener('beforeinstallprompt', (e) => {
    document.getElementById('installBanner').style.display = 'block';
    document.getElementById('installBanner').onclick = () => {
        e.prompt();
        e.userChoice.then(() => {
            document.getElementById('installBanner').style.display = 'none';
        });
    };
});
window.addEventListener('appinstalled', () => {
    document.getElementById('installBanner').style.display = 'none';
});
if (window.matchMedia('(display-mode: standalone)').matches) {
    document.getElementById('installBanner').style.display = 'none';
}
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{font-family:'Inter',sans-serif}
.stApp{background:#0a0a0f}
.glass-card{background:#16161f;border:1px solid #222233;border-radius:16px;padding:24px;margin-bottom:12px}
.metric-card{background:#16161f;border:1px solid #222233;border-radius:16px;padding:28px 24px;position:relative;overflow:hidden}
.metric-card::after{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#4f6ef7,#8b5cf6)}
.metric-value{font-size:2.8em;font-weight:800;letter-spacing:-2px;color:#f1f1f3;margin:4px 0}
.metric-label{color:#8888a0;font-size:0.8em;font-weight:500;text-transform:uppercase;letter-spacing:2px}
.badge{display:inline-block;padding:5px 14px;border-radius:20px;font-weight:600;font-size:0.8em}
.badge-pass{background:rgba(34,197,94,0.15);color:#22c55e}
.badge-danger{background:rgba(239,68,68,0.15);color:#ef4444}
.badge-warning{background:rgba(245,158,11,0.15);color:#f59e0b}
.stButton>button{border-radius:12px;font-weight:600;border:none;background:#4f6ef7;color:white;padding:12px 24px;transition:all 0.3s}
.stButton>button:hover{background:#6b84ff;transform:translateY(-2px);box-shadow:0 8px 30px rgba(79,110,247,0.3)}
.stTextInput>div>div>input,.stSelectbox>div>div>select,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{border-radius:10px!important;border:1px solid #222233!important;background:#111118!important;color:#f1f1f3!important;padding:12px 16px!important}
[data-testid="stSidebar"]{background:#111118;border-right:1px solid #222233}
[data-testid="stSidebar"] .stRadio label{padding:10px 16px;border-radius:10px;color:#8888a0;font-weight:500;font-size:0.9em}
[data-testid="stSidebar"] .stRadio label:hover{background:rgba(255,255,255,0.03);color:#f1f1f3}
h1{font-weight:800;letter-spacing:-1.5px;color:#f1f1f3;font-size:2em}
.stTabs [data-baseweb="tab-list"]{border-bottom:1px solid #222233}
.stTabs [aria-selected="true"]{color:#4f6ef7}
.trial-banner{background:linear-gradient(135deg,rgba(245,158,11,0.15),rgba(239,68,68,0.1));border:1px solid rgba(245,158,11,0.3);border-radius:12px;padding:16px 20px;margin-bottom:20px}
.trial-expired{background:rgba(239,68,68,0.1);border:2px solid #ef4444;border-radius:16px;padding:40px;text-align:center}
@media (display-mode: standalone) {
    .stApp { padding-top: env(safe-area-inset-top); }
}
</style>
""", unsafe_allow_html=True)

# ============================================
# DATABASE
# ============================================
DB_PATH = Path(__file__).parent / "demo.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    c = get_db()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, trial_start DATE, trial_end DATE, is_active BOOLEAN DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'admin', full_name TEXT, company_id INTEGER);
        CREATE TABLE IF NOT EXISTS vehicles (id INTEGER PRIMARY KEY AUTOINCREMENT, reg TEXT, type TEXT, company_id INTEGER, UNIQUE(reg, company_id));
        CREATE TABLE IF NOT EXISTS inspections (id INTEGER PRIMARY KEY AUTOINCREMENT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reg TEXT, mileage REAL, status TEXT, notes TEXT, driver TEXT, company_id INTEGER);
        CREATE TABLE IF NOT EXISTS near_misses (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, reporter TEXT, title TEXT, description TEXT, severity TEXT, category TEXT, status TEXT DEFAULT 'Reported', reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, title TEXT, priority TEXT DEFAULT 'Normal', status TEXT DEFAULT 'Pending', due_date DATE);
        CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, user_name TEXT, category TEXT, amount REAL, description TEXT, submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, item_name TEXT, quantity INTEGER DEFAULT 0, min_quantity INTEGER DEFAULT 5);
        CREATE TABLE IF NOT EXISTS visitors (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, visitor_name TEXT, company_name TEXT, sign_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, sender TEXT, body TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, filename TEXT, description TEXT, uploaded_by TEXT, file_data TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)
    c.commit()
    c.close()

init_db()

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

def check_trial(cid):
    c = get_db()
    r = c.execute("SELECT trial_start, trial_end, is_active FROM companies WHERE id=?", (cid,)).fetchone()
    c.close()
    if not r: return True, 90, None
    if r['is_active'] == 0: return False, 0, r['trial_end']
    trial_end = datetime.strptime(r['trial_end'], '%Y-%m-%d') if r['trial_end'] else None
    if not trial_end: return True, 90, None
    days_left = (trial_end - datetime.now()).days
    if days_left <= 0:
        c2 = get_db()
        c2.execute("UPDATE companies SET is_active=0 WHERE id=?", (cid,))
        c2.commit()
        c2.close()
        return False, 0, r['trial_end']
    return True, days_left, r['trial_end']

def start_trial(cid):
    start = datetime.now().strftime('%Y-%m-%d')
    end = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
    db.execute("UPDATE companies SET trial_start=?, trial_end=?, is_active=1 WHERE id=?", (start, end, cid))

OPENAI_API_KEY = 'sk-proj-TC2fgnfimB9wR4k08IXW5g'

def ai_chat(question):
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {OPENAI_API_KEY}","Content-Type":"application/json"},json={"model":"gpt-4o-mini","messages":[{"role":"system","content":"Enterprise assistant. Be concise and helpful."},{"role":"user","content":question}],"max_tokens":300},timeout=20)
        if r.status_code==200:return r.json()["choices"][0]["message"]["content"]
    except:pass
    q=question.lower()
    if "fleet" in q or "vehicle" in q:return"📊 **Fleet Analysis:**\n\n• Daily walkaround checks legally required\n• Common issues: tyres, brakes, lights\n• Preventive maintenance every 6-8 weeks\n• Regular inspections reduce major repairs by 40%"
    elif "safety" in q or "risk" in q:return"⚠️ **Safety Analysis:**\n\n• Report all near misses\n• Refresher training every 12 months\n• Inspect PPE monthly\n• Lone workers: 4-hour check-in policy"
    elif "cost" in q or "save" in q:return"💡 **Cost Reduction:**\n\n• Monitor MPG per vehicle\n• Preventive maintenance 3x cheaper\n• Eco-driving saves 15% fuel\n• Digital records eliminate paper"
    elif "compliance" in q:return"📋 **Compliance:**\n\n• DVSA: Daily checks mandatory for HGVs\n• HSE: Record near misses, investigate within 24hrs\n• Keep records 15 months minimum"
    else:return f"🤖 **Enterprise Assistant**\n\nI can help with fleet, safety, compliance, costs, and more. Try asking a specific question."

class Security:
    @staticmethod
    def hash(p):s=secrets.token_hex(16);return f"{s}${hashlib.sha256(f'{s}{p}'.encode()).hexdigest()}"
    @staticmethod
    def verify(p,h):
        try:s,hv=h.split('$');return hashlib.sha256(f'{s}{p}'.encode()).hexdigest()==hv
        except:return False

def sq(sql,p=None):
    try:return db.query(sql,p)
    except:return pd.DataFrame()

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False;st.session_state.user=None;st.session_state.role=None;st.session_state.cid=None
    st.session_state.dt=0;st.session_state.dr=False;st.session_state.st=None;st.session_state.tmpl="";st.session_state.ai_q=""

if not st.session_state.logged_in:
    col1,col2,col3=st.columns([1,2,1])
    with col2:
        st.markdown("<br><br>",unsafe_allow_html=True)
        st.markdown("""<div style="text-align:center;margin-bottom:50px;"><div style="font-size:3em;">◆</div><h1 style="font-size:2.8em;font-weight:800;letter-spacing:-2px;color:#f1f1f3;margin:0;">Enterprise</h1><p style="color:#8888a0;font-size:1.1em;">Command Centre</p><p style="color:#f59e0b;">3-Month Free Trial — No Card Required</p></div>""",unsafe_allow_html=True)
        tab1,tab2=st.tabs(["Sign In","Start Free Trial"])
        with tab1:
            with st.form("login"):
                u=st.text_input("Username");p=st.text_input("Password",type="password")
                if st.form_submit_button("Sign In",type="primary",use_container_width=True):
                    c=get_db();r=c.execute("SELECT password,role,company_id FROM users WHERE username=?",(u,)).fetchone();c.close()
                    if r and Security.verify(p,r[0]):
                        active,days,end=check_trial(r[2])
                        if not active:st.error("⚠️ Trial expired. Contact us to upgrade.")
                        else:st.session_state.logged_in=True;st.session_state.user=u;st.session_state.role=r[1];st.session_state.cid=r[2];st.rerun()
                    else:st.error("Invalid credentials")
        with tab2:
            with st.form("register"):
                co=st.text_input("Company Name");au=st.text_input("Admin Username");ap=st.text_input("Password",type="password")
                st.markdown("""<div class="trial-banner"><b>🕐 3-Month Free Trial</b><br><small>Full access. No card. Upgrade anytime.</small></div>""",unsafe_allow_html=True)
                if st.form_submit_button("Start Free Trial",type="primary",use_container_width=True):
                    if not co or not au or not ap:st.error("All fields required")
                    elif len(ap)<8:st.error("Password: 8+ chars")
                    else:
                        try:
                            c=get_db();c.execute("INSERT INTO companies (name) VALUES (?)",(co,));cid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
                            c.execute("INSERT INTO users (username,password,role,company_id) VALUES (?,?,'admin',?)",(au,Security.hash(ap),cid));c.commit();c.close()
                            start_trial(cid);st.success("✅ Trial started! 90 days free. Go to Sign In.");st.balloons()
                        except:st.error("Company or username exists")
    st.stop()

cid=st.session_state.cid;role=st.session_state.role
trial_active,days_left,trial_end=check_trial(cid)

if not trial_active:
    st.markdown("""<div class="trial-expired"><h1 style="color:#ef4444;">Trial Expired</h1><p style="color:#8888a0;font-size:1.2em;">Your 3-month free trial has ended.</p><p style="color:#f1f1f3;">Contact davidmlangstead@gmail.com to upgrade.</p></div>""",unsafe_allow_html=True)
    if st.button("Sign Out"):st.session_state.clear();st.rerun()
    st.stop()

with st.sidebar:
    st.markdown('<div style="padding:10px 0;"><div style="font-size:1.3em;font-weight:800;color:#f1f1f3;">◆ Enterprise</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;padding:12px;background:#16161f;border-radius:12px;margin-bottom:16px;"><div style="width:36px;height:36px;background:#4f6ef7;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;">{st.session_state.user[0].upper()}</div><div><div style="font-weight:600;color:#f1f1f3;">{st.session_state.user}</div><div style="font-size:0.8em;color:#8888a0;">{role.upper()}</div></div></div>',unsafe_allow_html=True)
    if days_left<=30:st.markdown(f'<div style="background:rgba({"239,68,68" if days_left<=7 else "245,158,11"},0.1);border:1px solid {"#ef4444" if days_left<=7 else "#f59e0b"};border-radius:10px;padding:10px;margin-bottom:12px;text-align:center;"><b style="color:{"#ef4444" if days_left<=7 else "#f59e0b"};">{days_left} days left</b></div>',unsafe_allow_html=True)
    page=st.radio("",["Dashboard","Fleet","Staff","Near Miss","Jobs","Expenses","Inventory","Visitors","Chat","Tasks","Documents","Inspections","Tacho","AI Assistant","Reports","Settings"],label_visibility="collapsed")
    st.markdown("---")
    if st.button("Sign Out",use_container_width=True):st.session_state.clear();st.rerun()

if page=="Dashboard":
    st.markdown(f'<h1>Dashboard</h1><p style="color:#8888a0;">{datetime.now().strftime("%A, %d %B %Y")}</p>',unsafe_allow_html=True)
    if days_left<=30:st.markdown(f'<div class="trial-banner">⚠️ <b>{days_left} days remaining</b> in free trial.</div>',unsafe_allow_html=True)
    vc=sq("SELECT COUNT(*) as c FROM vehicles WHERE company_id=?",(cid,)).iloc[0,0]
    sc=sq("SELECT COUNT(*) as c FROM users WHERE company_id=?",(cid,)).iloc[0,0]
    ic=sq("SELECT COUNT(*) as c FROM inspections WHERE company_id=?",(cid,)).iloc[0,0]
    nc=sq("SELECT COUNT(*) as c FROM near_misses WHERE company_id=? AND status='Reported'",(cid,)).iloc[0,0]
    c1,c2,c3,c4=st.columns(4)
    with c1:st.markdown(f'<div class="metric-card"><div class="metric-label">Vehicles</div><div class="metric-value">{vc}</div></div>',unsafe_allow_html=True)
    with c2:st.markdown(f'<div class="metric-card"><div class="metric-label">Team</div><div class="metric-value">{sc}</div></div>',unsafe_allow_html=True)
    with c3:st.markdown(f'<div class="metric-card"><div class="metric-label">Inspections</div><div class="metric-value">{ic}</div></div>',unsafe_allow_html=True)
    with c4:st.markdown(f'<div class="metric-card"><div class="metric-label">Near Misses</div><div class="metric-value">{nc}</div></div>',unsafe_allow_html=True)

elif page=="Fleet":
    st.markdown('<h1>Fleet</h1>',unsafe_allow_html=True)
    tab1,tab2=st.tabs(["Vehicles","+ Add"])
    with tab1:
        veh=sq("SELECT * FROM vehicles WHERE company_id=?",(cid,))
        if not veh.empty:
            for _,v in veh.iterrows():
                insp=sq("SELECT * FROM inspections WHERE reg=? AND company_id=? ORDER BY time DESC LIMIT 1",(v['reg'],cid))
                status=insp.iloc[0]['status'] if not insp.empty else"Not inspected"
                badge="badge-pass" if status=="PASS" else"badge-danger"
                st.markdown(f'<div class="glass-card"><div style="display:flex;justify-content:space-between;"><div><b>{v["reg"]}</b><br><span style="color:#8888a0;">{v.get("type","Unknown")}</span></div><span class="badge {badge}">{status}</span></div></div>',unsafe_allow_html=True)
    with tab2:
        with st.form("add_v"):
            reg=st.text_input("Registration").upper();t=st.selectbox("Type",["HGV Artic","HGV Rigid","Van","Car","Trailer"])
            if st.form_submit_button("Register",type="primary",use_container_width=True):
                if reg:
                    try:db.execute("INSERT INTO vehicles (reg,type,company_id) VALUES (?,?,?)",(reg,t,cid));st.success(f"{reg} registered");st.rerun()
                    except:st.error("Already registered")

elif page=="Staff":
    st.markdown('<h1>Staff</h1>',unsafe_allow_html=True)
    staff=sq("SELECT username,role,created_at FROM users WHERE company_id=?",(cid,))
    if not staff.empty:st.dataframe(staff,use_container_width=True,hide_index=True)
    with st.expander("+ Add Staff"):
        with st.form("add_staff"):
            u=st.text_input("Username");p=st.text_input("Password",type="password");r=st.selectbox("Role",["driver","worker","workshop","manager"])
            if st.form_submit_button("Add",type="primary",use_container_width=True):
                if u and p and len(p)>=8:
                    try:db.execute("INSERT INTO users (username,password,role,company_id) VALUES (?,?,?,?)",(u,Security.hash(p),r,cid));st.success(f"{u} added");st.rerun()
                    except:st.error("Username exists")

elif page=="Near Miss":
    st.markdown('<h1>Near Miss</h1>',unsafe_allow_html=True)
    with st.form("nm"):
        title=st.text_input("Title");desc=st.text_area("Description")
        c1,c2=st.columns(2)
        with c1:cat=st.selectbox("Category",["Slip/Trip","Vehicle","Manual Handling","Height","Electrical","Other"])
        with c2:sev=st.selectbox("Severity",["Low","Medium","High","Critical"])
        if st.form_submit_button("Submit",type="primary",use_container_width=True):
            if title and desc:db.execute("INSERT INTO near_misses (company_id,reporter,title,description,severity,category) VALUES (?,?,?,?,?,?)",(cid,st.session_state.user,title,desc,sev,cat));st.success("Reported");st.rerun()
    nm=sq("SELECT * FROM near_misses WHERE company_id=? ORDER BY reported_at DESC LIMIT 20",(cid,))
    if not nm.empty:
        for _,n in nm.iterrows():st.markdown(f'<div class="glass-card"><b>{n["title"]}</b> — {n["severity"]}<br><span style="color:#8888a0;">{n["category"]} • {n["reporter"]}</span></div>',unsafe_allow_html=True)

elif page=="Jobs":
    st.markdown('<h1>Jobs</h1>',unsafe_allow_html=True)
    with st.form("job"):
        cn=st.text_input("Customer");de=st.text_area("Description");q=st.number_input("Quote (£)",0.0,100000.0,0.0)
        if st.form_submit_button("Create",type="primary",use_container_width=True):
            if cn and de:db.execute("INSERT INTO jobs (company_id,customer_name,description,quoted_amount) VALUES (?,?,?,?)",(cid,cn,de,q));st.success("Created");st.rerun()
    jobs=sq("SELECT * FROM jobs WHERE company_id=? ORDER BY rowid DESC",(cid,))
    if not jobs.empty:
        for _,j in jobs.iterrows():st.markdown(f'<div class="glass-card"><b>{j["customer_name"]}</b> — £{j["quoted_amount"]:,.2f}</div>',unsafe_allow_html=True)

elif page=="Expenses":
    st.markdown('<h1>Expenses</h1>',unsafe_allow_html=True)
    with st.form("exp"):
        cat=st.selectbox("Category",["Travel","Fuel","Equipment","Office","Repair","Other"]);amt=st.number_input("Amount (£)",0.0,10000.0,0.0);desc=st.text_area("Description")
        if st.form_submit_button("Submit",type="primary",use_container_width=True):
            if amt>0:db.execute("INSERT INTO expenses (company_id,user_name,category,amount,description) VALUES (?,?,?,?,?)",(cid,st.session_state.user,cat,amt,desc));st.success("Submitted");st.rerun()
    exp=sq("SELECT * FROM expenses WHERE company_id=? ORDER BY submitted_at DESC LIMIT 20",(cid,))
    if not exp.empty:
        for _,e in exp.iterrows():st.markdown(f'<div class="glass-card"><b>£{e["amount"]:,.2f}</b> — {e["category"]}</div>',unsafe_allow_html=True)

elif page=="Inventory":
    st.markdown('<h1>Inventory</h1>',unsafe_allow_html=True)
    with st.form("inv"):
        n=st.text_input("Item");q=st.number_input("Qty",0,99999,1);m=st.number_input("Min Stock",0,99999,5)
        if st.form_submit_button("Add",type="primary",use_container_width=True):
            if n:db.execute("INSERT INTO inventory (company_id,item_name,quantity,min_quantity) VALUES (?,?,?,?)",(cid,n,q,m));st.success("Added");st.rerun()
    inv=sq("SELECT * FROM inventory WHERE company_id=?",(cid,))
    if not inv.empty:
        for _,i in inv.iterrows():c='#ef4444' if i['quantity']<=i['min_quantity'] else'#22c55e';st.markdown(f'<div class="glass-card"><b>{i["item_name"]}</b> — <span style="color:{c};">Qty: {i["quantity"]}</span></div>',unsafe_allow_html=True)

elif page=="Visitors":
    st.markdown('<h1>Visitors</h1>',unsafe_allow_html=True)
    with st.form("vis"):
        n=st.text_input("Name");c=st.text_input("Company")
        if st.form_submit_button("Sign In",type="primary",use_container_width=True):
            if n:db.execute("INSERT INTO visitors (company_id,visitor_name,company_name) VALUES (?,?,?)",(cid,n,c));st.success(f"{n} signed in");st.rerun()
    vis=sq("SELECT * FROM visitors WHERE company_id=? ORDER BY sign_in_time DESC LIMIT 20",(cid,))
    if not vis.empty:
        for _,v in vis.iterrows():st.markdown(f'<div class="glass-card"><b>{v["visitor_name"]}</b> — {v["company_name"]}</div>',unsafe_allow_html=True)

elif page=="Chat":
    st.markdown('<h1>Team Chat</h1>',unsafe_allow_html=True)
    msgs=sq("SELECT * FROM messages WHERE company_id=? ORDER BY sent_at DESC LIMIT 30",(cid,))
    if not msgs.empty:
        for _,m in msgs[::-1].iterrows():st.markdown(f'<div class="glass-card"><b>{m["sender"]}</b>: {m["body"][:200]}</div>',unsafe_allow_html=True)
    with st.form("chat"):
        body=st.text_area("Message")
        if st.form_submit_button("Send",type="primary",use_container_width=True):
            if body:db.execute("INSERT INTO messages (company_id,sender,body) VALUES (?,?,?)",(cid,st.session_state.user,body));st.rerun()

elif page=="Tasks":
    st.markdown('<h1>Tasks</h1>',unsafe_allow_html=True)
    with st.form("task"):
        t=st.text_input("Task");p=st.selectbox("Priority",["Normal","High","Urgent"]);d=st.date_input("Due")
        if st.form_submit_button("Create",type="primary",use_container_width=True):
            if t:db.execute("INSERT INTO tasks (company_id,title,priority,due_date) VALUES (?,?,?,?)",(cid,t,p,d.strftime('%Y-%m-%d')));st.success("Created");st.rerun()
    tasks=sq("SELECT * FROM tasks WHERE company_id=? ORDER BY due_date",(cid,))
    if not tasks.empty:
        for _,t in tasks.iterrows():st.markdown(f'<div class="glass-card">{"✅" if t["status"]=="Completed" else"○"} {t["title"]} — {t["due_date"]}</div>',unsafe_allow_html=True)

elif page=="Documents":
    st.markdown('<h1>Documents</h1>',unsafe_allow_html=True)
    tab1,tab2,tab3=st.tabs(["Editor","Library","Templates"])
    with tab1:
        doc_title=st.text_input("Title",placeholder="Untitled Document")
        c1,c2,c3,c4,c5,c6=st.columns(6)
        with c1:bold=st.checkbox("Bold")
        with c2:italic=st.checkbox("Italic")
        with c3:h1=st.checkbox("Heading 1")
        with c4:h2=st.checkbox("Heading 2")
        with c5:bullet=st.checkbox("Bullets")
        with c6:numbered=st.checkbox("Numbered")
        content=st.text_area("Content",height=400,placeholder="Start writing...",label_visibility="collapsed")
        if content:
            formatted=content
            if bold:formatted=f"**{formatted}**"
            if italic:formatted=f"*{formatted}*"
            if h1:formatted=f"# {formatted}"
            if h2:formatted=f"## {formatted}"
            if bullet:formatted="\n".join([f"- {line}" for line in formatted.split('\n') if line.strip()])
            if numbered:formatted="\n".join([f"{i+1}. {line}" for i,line in enumerate(formatted.split('\n')) if line.strip()])
            with st.expander("Preview"):st.markdown(formatted)
        if st.button("Save Document",type="primary",use_container_width=True):
            if doc_title and content:db.execute("INSERT INTO documents (company_id,filename,description,uploaded_by,file_data) VALUES (?,?,?,?,?)",(cid,doc_title,content[:200],st.session_state.user,content));st.success("Saved");st.rerun()
    with tab2:
        docs=sq("SELECT * FROM documents WHERE company_id=? ORDER BY uploaded_at DESC",(cid,))
        if not docs.empty:
            for _,d in docs.iterrows():
                with st.expander(f"📄 {d['filename']}"):st.markdown(d.get('file_data',''));st.download_button("Download",d.get('file_data',''),f"{d['filename']}.txt")
    with tab3:
        for name,tmpl in{"Meeting Minutes":"# Meeting Minutes\n\n**Date:** \n**Attendees:** \n\n**Agenda:**\n1. \n2.","Safety Report":"# Safety Report\n\n**Date:** \n**Location:** \n\n**Findings:**\n- \n- ","Inspection":"# Vehicle Inspection\n\n**Vehicle:** \n**Mileage:** \n\n- [ ] Tyres\n- [ ] Brakes","Incident":"# Incident Report\n\n**Date:** \n**Location:** \n\n**Description:**\n\n**Signature:** "}.items():
            if st.button(f"📋 {name}",use_container_width=True):st.session_state.tmpl=tmpl;st.rerun()
        if st.session_state.tmpl:st.text_area("Template",st.session_state.tmpl,height=200,key="tmpl_edit")

elif page=="Inspections":
    st.markdown('<h1>Vehicle Inspection</h1>',unsafe_allow_html=True)
    vehs=sq("SELECT reg FROM vehicles WHERE company_id=?",(cid,))
    if vehs.empty:st.warning("No vehicles")
    else:
        with st.form("insp"):
            reg=st.selectbox("Vehicle",vehs['reg'].tolist());mileage=st.number_input("Mileage",0,step=1000)
            items=["Tyres","Brakes","Lights","Steering","Suspension","Exhaust","Seatbelts","Mirrors","Wipers","Fluids","Oil","Coolant"]
            checks={};cols=st.columns(4)
            for i,item in enumerate(items):
                with cols[i%4]:checks[item]=st.checkbox(item,value=True)
            ok=all(checks.values());notes=""
            if not ok:failed=[i for i,c in checks.items() if not c];st.error(f"Defects: {', '.join(failed)}");notes=st.text_area("Description");severity=st.selectbox("Severity",["Minor","Major","Dangerous - VOR"])
            sig=st.text_input("Signature")
            if st.form_submit_button("Submit",type="primary",use_container_width=True):
                if not ok and not notes:st.error("Describe defects")
                elif not sig:st.error("Sign required")
                else:
                    status="PASS" if ok else f"DEFECT - {severity}"
                    db.execute("INSERT INTO inspections (time,reg,mileage,status,notes,driver,company_id) VALUES (?,?,?,?,?,?,?)",(datetime.now(),reg,mileage,status,notes or"Passed",st.session_state.user,cid))
                    if ok:st.success("PASS");st.balloons()
                    else:st.warning("Defect logged")
                    time.sleep(1);st.rerun()

elif page=="Tacho":
    st.markdown('<h1>Tacho Timer</h1>',unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1:h=st.session_state.dt//3600;m=(st.session_state.dt%3600)//60;st.markdown(f'<div style="background:#16161f;border:1px solid #222233;border-radius:16px;padding:30px;text-align:center;"><div style="color:#8888a0;">DRIVING</div><div style="font-size:3em;font-weight:800;color:#22c55e;">{h:02d}:{m:02d}</div></div>',unsafe_allow_html=True)
    with c2:rem=max(0,16200-st.session_state.dt);rh=rem//3600;rm=(rem%3600)//60;st.markdown(f'<div style="background:#16161f;border:1px solid #222233;border-radius:16px;padding:30px;text-align:center;"><div style="color:#8888a0;">REMAINING</div><div style="font-size:3em;font-weight:800;color:#f59e0b;">{rh:02d}:{rm:02d}</div></div>',unsafe_allow_html=True)
    with c3:st.markdown(f'<div style="background:#16161f;border:1px solid #222233;border-radius:16px;padding:30px;text-align:center;"><div style="color:#8888a0;">STATUS</div><div style="font-size:2em;font-weight:700;color:{"#22c55e" if st.session_state.dr else"#8888a0"};">{"DRIVING" if st.session_state.dr else"STOPPED"}</div></div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        if not st.session_state.dr:
            if st.button("Start",type="primary",use_container_width=True):st.session_state.dr=True;st.session_state.st=time.time();st.rerun()
        else:
            if st.button("Stop",use_container_width=True):
                if st.session_state.st:st.session_state.dt+=int(time.time()-st.session_state.st)
                st.session_state.dr=False;st.session_state.st=None;st.rerun()
    with c2:
        if st.button("Reset",use_container_width=True):st.session_state.dt=0;st.session_state.dr=False;st.rerun()

elif page=="AI Assistant":
    st.markdown('<h1>AI Assistant</h1><p style="color:#8888a0;">Always available — smart responses even offline</p>',unsafe_allow_html=True)
    q=st.text_area("Your Question",value=st.session_state.ai_q,height=100,placeholder="Ask anything...")
    if st.button("Ask AI",type="primary",use_container_width=True):
        if q:
            with st.spinner("Thinking..."):answer=ai_chat(q);st.markdown(f'<div class="glass-card" style="line-height:1.8;">{answer}</div>',unsafe_allow_html=True);st.session_state.ai_q=""

elif page=="Reports":
    st.markdown('<h1>Reports</h1>',unsafe_allow_html=True)
    insp=sq("SELECT * FROM inspections WHERE company_id=? ORDER BY time DESC",(cid,))
    nm=sq("SELECT * FROM near_misses WHERE company_id=? ORDER BY reported_at DESC",(cid,))
    if not insp.empty:st.dataframe(insp,use_container_width=True);st.download_button("Download Inspections CSV",insp.to_csv(index=False),"inspections.csv")
    if not nm.empty:st.dataframe(nm,use_container_width=True);st.download_button("Download Near Misses CSV",nm.to_csv(index=False),"near_misses.csv")

elif page=="Settings":
    st.markdown('<h1>Settings</h1>',unsafe_allow_html=True)
    st.markdown(f"""<div class="glass-card"><h3>Trial Status</h3><p><b>Days Remaining:</b> <span style="color:{'#ef4444' if days_left<=7 else'#f59e0b' if days_left<=30 else'#22c55e'};">{days_left} days</span></p><p><b>Trial End:</b> {trial_end}</p><p style="color:#8888a0;">Upgrade: davidmlangstead@gmail.com</p></div>""",unsafe_allow_html=True)
    with st.form("pwd"):
        st.markdown("### Change Password")
        cur=st.text_input("Current",type="password");new=st.text_input("New",type="password")
        if st.form_submit_button("Update",type="primary",use_container_width=True):
            if cur and new and len(new)>=8:
                c=get_db();r=c.execute("SELECT password FROM users WHERE username=? AND company_id=?",(st.session_state.user,cid)).fetchone()
                if r and Security.verify(cur,r[0]):c.execute("UPDATE users SET password=? WHERE username=? AND company_id=?",(Security.hash(new),st.session_state.user,cid));c.commit();st.success("Updated")
                else:st.error("Wrong password")
                c.close()

st.markdown("---")
st.markdown(f'<div style="text-align:center;color:#8888a0;padding:20px;">◆ Enterprise Command Centre • PWA Ready • {days_left} days remaining</div>',unsafe_allow_html=True)
