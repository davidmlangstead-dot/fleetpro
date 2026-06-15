from sqlalchemy import text
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
import qrcode
from io import BytesIO
import base64
from fpdf import FPDF
import random
import numpy as np
import json

# ============================================
# 🚛 FLEETPRO 365 — THE BIG CHANGE EDITION
# THE DEMON LOVE CHILD OF SAMSARA × TESLA × SPACEX
# DVSA • RHA • FORS • CLOCS • WRRR • Earned Recognition
# £250K+ Enterprise Fleet Command System
# ============================================

st.set_page_config(
    page_title="FleetPro 365 | The Big Change",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ============================================
# 🎨 BIG CHANGE UI — NEXT-GEN ENTERPRISE THEME
# ============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;600&display=swap');

* { font-family: 'Inter', sans-serif; }
code, pre { font-family: 'JetBrains Mono', monospace; }

/* Deep space background with animated nebula */
.stApp {
    background: #000010;
    background-image: 
        radial-gradient(ellipse at 20% 50%, rgba(59,130,246,0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.06) 0%, transparent 60%),
        radial-gradient(ellipse at 50% 80%, rgba(236,72,153,0.04) 0%, transparent 60%),
        radial-gradient(ellipse at 10% 10%, rgba(6,182,212,0.05) 0%, transparent 50%);
    background-attachment: fixed;
}

/* Stars */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
        radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.3), transparent),
        radial-gradient(1px 1px at 25% 45%, rgba(255,255,255,0.2), transparent),
        radial-gradient(1px 1px at 40% 15%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1px 1px at 55% 65%, rgba(255,255,255,0.2), transparent),
        radial-gradient(1px 1px at 70% 35%, rgba(255,255,255,0.3), transparent),
        radial-gradient(1px 1px at 85% 55%, rgba(255,255,255,0.2), transparent),
        radial-gradient(1.5px 1.5px at 15% 75%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 60% 85%, rgba(255,255,255,0.3), transparent),
        radial-gradient(1px 1px at 90% 10%, rgba(255,255,255,0.4), transparent);
    pointer-events: none;
    animation: twinkle 4s ease-in-out infinite alternate;
}

@keyframes twinkle {
    0% { opacity: 0.6; }
    100% { opacity: 1; }
}

/* Aurora effect */
.stApp::after {
    content: '';
    position: fixed;
    top: -100px; left: 0; right: 0;
    height: 300px;
    background: linear-gradient(180deg, 
        rgba(59,130,246,0.06) 0%, 
        rgba(139,92,246,0.04) 30%, 
        rgba(236,72,153,0.02) 60%, 
        transparent 100%);
    pointer-events: none;
    animation: aurora 15s ease-in-out infinite;
}

@keyframes aurora {
    0%, 100% { transform: translateY(0) scaleX(1); opacity: 0.6; }
    25% { transform: translateY(20px) scaleX(1.1); opacity: 0.8; }
    50% { transform: translateY(-10px) scaleX(0.9); opacity: 0.4; }
    75% { transform: translateY(15px) scaleX(1.05); opacity: 0.7; }
}

/* Premium Glass Cards */
.glass-card {
    background: linear-gradient(135deg, 
        rgba(255,255,255,0.04) 0%, 
        rgba(255,255,255,0.01) 50%,
        rgba(255,255,255,0.02) 100%);
    backdrop-filter: blur(40px) saturate(180%);
    -webkit-backdrop-filter: blur(40px) saturate(180%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 24px;
    padding: 30px;
    position: relative;
    overflow: hidden;
    transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, 
        transparent, 
        rgba(255,255,255,0.15), 
        rgba(255,255,255,0.05), 
        transparent);
}

.glass-card::after {
    content: '';
    position: absolute;
    top: -100%; left: -100%;
    width: 300%; height: 300%;
    background: radial-gradient(circle at center, 
        rgba(59,130,246,0.03) 0%, 
        transparent 50%);
    opacity: 0;
    transition: opacity 0.5s;
    pointer-events: none;
}

.glass-card:hover {
    transform: translateY(-8px);
    border-color: rgba(59,130,246,0.25);
    box-shadow: 
        0 30px 80px rgba(0,0,0,0.6),
        0 0 100px rgba(59,130,246,0.08),
        0 0 40px rgba(139,92,246,0.04);
}

.glass-card:hover::after {
    opacity: 1;
}

/* KPI Metric Cards */
.metric-card {
    background: linear-gradient(135deg, 
        rgba(59,130,246,0.08) 0%, 
        rgba(139,92,246,0.06) 50%,
        rgba(236,72,153,0.04) 100%);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 22px;
    padding: 28px;
    position: relative;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, 
        #3b82f6, #6366f1, #8b5cf6, #a855f7, #ec4899, #f472b6,
        #ec4899, #a855f7, #8b5cf6, #6366f1, #3b82f6);
    background-size: 300% 100%;
    animation: borderFlow 4s linear infinite;
}

@keyframes borderFlow {
    0% { background-position: 300% 0; }
    100% { background-position: -300% 0; }
}

.metric-card:hover {
    border-color: rgba(59,130,246,0.4);
    transform: scale(1.03);
    box-shadow: 
        0 20px 60px rgba(0,0,0,0.5),
        0 0 80px rgba(59,130,246,0.1),
        inset 0 0 40px rgba(59,130,246,0.02);
}

.metric-value {
    font-size: 3em;
    font-weight: 900;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 40%, #f472b6 70%, #60a5fa 100%);
    background-size: 200% 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: valueShimmer 4s ease infinite;
    margin: 8px 0;
    line-height: 1;
}

@keyframes valueShimmer {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

.metric-label {
    color: #94a3b8;
    font-size: 0.7em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 4px;
}

.metric-subtitle {
    color: #64748b;
    font-size: 0.75em;
    margin-top: 4px;
}

/* Status Badges with Particle Effects */
.badge-pass { 
    background: linear-gradient(135deg, #059669, #10b981); 
    color: white; 
    padding: 8px 20px; 
    border-radius: 30px; 
    font-weight: 600;
    font-size: 0.85em;
    box-shadow: 0 4px 20px rgba(16,185,129,0.3);
    position: relative;
    overflow: hidden;
}
.badge-pass::after {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.3), transparent 60%);
    animation: badgeShine 3s ease-in-out infinite;
}

.badge-minor { 
    background: linear-gradient(135deg, #d97706, #f59e0b); 
    color: white; 
    padding: 8px 20px; 
    border-radius: 30px; 
    font-weight: 600;
    font-size: 0.85em;
    box-shadow: 0 4px 20px rgba(245,158,11,0.3);
}

.badge-major { 
    background: linear-gradient(135deg, #dc2626, #ef4444); 
    color: white; 
    padding: 8px 20px; 
    border-radius: 30px; 
    font-weight: 600;
    font-size: 0.85em;
    box-shadow: 0 4px 20px rgba(239,68,68,0.3);
}

.badge-vor { 
    background: linear-gradient(135deg, #7c3aed, #a855f7); 
    color: white; 
    padding: 8px 20px; 
    border-radius: 30px; 
    font-weight: 600;
    font-size: 0.85em;
    box-shadow: 0 0 30px rgba(168,85,247,0.6);
    animation: vorAlert 1.2s ease-in-out infinite;
}

@keyframes vorAlert {
    0%, 100% { box-shadow: 0 0 30px rgba(168,85,247,0.6); transform: scale(1); }
    50% { box-shadow: 0 0 60px rgba(168,85,247,1); transform: scale(1.05); }
}

@keyframes badgeShine {
    0%, 100% { transform: translate(-30%, -30%) rotate(0deg); }
    50% { transform: translate(30%, 30%) rotate(180deg); }
}

/* Premium Buttons */
.stButton > button {
    border-radius: 18px;
    font-weight: 600;
    letter-spacing: 0.5px;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    border: none;
    background: linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%);
    background-size: 200% 200%;
    color: white;
    padding: 16px 32px;
    position: relative;
    overflow: hidden;
    animation: buttonGradient 4s ease infinite;
}

@keyframes buttonGradient {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.stButton > button:hover {
    transform: translateY(-5px);
    box-shadow: 0 25px 50px rgba(59,130,246,0.5);
}

.stButton > button:hover::before {
    left: 100%;
}

/* Input Fields */
.stTextInput > div > div > input, 
.stSelectbox > div > div > select,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 16px;
    border: 2px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.02);
    color: white;
    transition: all 0.4s;
    padding: 12px 18px;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(59,130,246,0.6);
    box-shadow: 0 0 40px rgba(59,130,246,0.2);
    background: rgba(255,255,255,0.04);
    outline: none;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, 
        rgba(6,11,31,0.99) 0%, 
        rgba(10,14,39,0.98) 50%,
        rgba(15,13,46,0.99) 100%);
    border-right: 1px solid rgba(255,255,255,0.04);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.02);
    border-radius: 20px;
    padding: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 16px;
    padding: 14px 30px;
    font-weight: 500;
    transition: all 0.4s;
    color: #94a3b8;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(59,130,246,0.25), rgba(139,92,246,0.25));
    color: white;
    font-weight: 600;
}

/* Headers */
h1 { 
    font-weight: 900; 
    letter-spacing: -2px;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 50%, #fce7f3 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em;
}
h2 { font-weight: 700; color: #e2e8f0; letter-spacing: -0.5px; }
h3 { font-weight: 600; color: #cbd5e1; }

/* Custom Scrollbar */
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { 
    background: rgba(255,255,255,0.01); 
    border-radius: 5px; 
}
::-webkit-scrollbar-thumb { 
    background: linear-gradient(180deg, #3b82f6, #8b5cf6, #ec4899); 
    border-radius: 5px;
    border: 2px solid rgba(0,0,0,0.5);
}

/* Expanders */
[data-testid="stExpander"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.05);
    transition: all 0.3s;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(59,130,246,0.2);
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

/* Dataframe */
[data-testid="stDataFrame"] { 
    border-radius: 20px; 
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.06);
}

/* Radio buttons */
.stRadio > div {
    gap: 4px;
}
.stRadio [data-baseweb="radio"] {
    padding: 8px 16px;
    border-radius: 12px;
    transition: all 0.3s;
}
.stRadio [data-baseweb="radio"]:hover {
    background: rgba(59,130,246,0.1);
}

/* Checkboxes */
.stCheckbox {
    padding: 4px 0;
}

/* Success/Warning/Error/Info boxes */
[data-testid="stAlert"] {
    border-radius: 18px;
    border: none;
    backdrop-filter: blur(20px);
}
</style>

<script>
// Parallax effect on mouse move
document.addEventListener('mousemove', (e) => {
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;
    document.body.style.setProperty('--mouse-x', x);
    document.body.style.setProperty('--mouse-y', y);
});
</script>
""", unsafe_allow_html=True)

# ============================================
# ⚡ THE BIG CHANGE — CORE ENGINES
# ============================================

class SecurityEngine:
    """Military-grade security for enterprise fleet data"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(32)
        return f"{salt}${hashlib.sha3_256(f'{salt}{password}'.encode()).hexdigest()}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        try:
            salt, hash_val = hashed.split('$')
            return hashlib.sha3_256(f'{salt}{password}'.encode()).hexdigest() == hash_val
        except:
            return False
    
    @staticmethod
    def generate_qr(data: str) -> str:
        qr = qrcode.QRCode(version=2, box_size=12, border=6)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#000010", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    @staticmethod
    def generate_vehicle_token(reg: str, cid: int) -> str:
        """Generate unique vehicle identification token"""
        data = f"FLEETPRO|{cid}|{reg}|{datetime.now().timestamp()}"
        return hashlib.sha3_256(data.encode()).hexdigest()[:16].upper()

class AIEngine:
    """GPT-4o powered fleet intelligence"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
    
    def assess_defect(self, vehicle: str, defects: str, notes: str) -> str:
        if not self.api_key:
            return "⚠️ AI Engine Offline — Connect OpenAI API Key"
        try:
            r = self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are the DVSA Chief Vehicle Examiner with 35 years experience and AI-powered diagnostic capabilities. 
                            Analyze this defect report and provide:
                            1. 🔴 IMMEDIATE RISK LEVEL (CRITICAL/HIGH/MEDIUM/LOW)
                            2. ⚖️ LEGAL STATUS (Can vehicle legally continue? Yes/No/Conditional)
                            3. 🔧 REQUIRED ACTION (within 24 hours)
                            4. 💰 ESTIMATED COST IMPACT (Minor <£500 / Medium £500-2000 / Major >£2000)
                            5. 📊 PROBABILITY OF ROADSIDE PROHIBITION (% chance DVSA would issue immediate prohibition)
                            Be authoritative, precise, and reference specific regulations where applicable.
                            Maximum 5 concise bullet points."""
                        },
                        {"role": "user", "content": f"VEHICLE: {vehicle}\nDEFECTS FOUND: {defects}\nDRIVER REPORT: {notes}"}
                    ],
                    "max_tokens": 300,
                    "temperature": 0.1
                },
                timeout=15
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            return "⚠️ AI Service Timeout — Assessment queued for background processing"
        except Exception as e:
            return f"⚠️ AI Service Unavailable ({str(e)[:50]}) — Manual Assessment Required"
    
    def predict_maintenance(self, vehicle_data: dict) -> str:
        if not self.api_key:
            return None
        try:
            r = self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are an AI predictive maintenance engine for commercial vehicle fleets.
                            Analyze the vehicle data and predict:
                            1. Most likely component to fail next (with confidence %)
                            2. Recommended preventive maintenance within 30 days
                            3. Estimated remaining safe operating days before service required
                            4. Risk score 1-10 (10 = imminent dangerous failure)
                            Be data-driven and specific."""
                        },
                        {"role": "user", "content": json.dumps(vehicle_data)}
                    ],
                    "max_tokens": 250,
                    "temperature": 0.2
                },
                timeout=12
            )
            return r.json()["choices"][0]["message"]["content"]
        except:
            return None
    
    def generate_fleet_strategy(self, fleet_data: dict) -> str:
        """AI-powered fleet optimisation strategy"""
        if not self.api_key:
            return None
        try:
            r = self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a fleet optimisation AI consultant. 
                            Analyze the fleet data and provide strategic recommendations for:
                            1. Cost reduction opportunities
                            2. Compliance improvement areas
                            3. Vehicle replacement prioritization
                            4. Driver training needs
                            Be specific and actionable."""
                        },
                        {"role": "user", "content": json.dumps(fleet_data)}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.4
                },
                timeout=20
            )
            return r.json()["choices"][0]["message"]["content"]
        except:
            return None

class FleetAnalytics:
    """Advanced fleet data analytics engine"""
    
    @staticmethod
    def health_score(df: pd.DataFrame) -> float:
        if df.empty: return 100.0
        total = len(df)
        weights = {
            'VOR': 40, 'Dangerous': 40,
            'Major': 18, 'Minor': 5, 'PASS': 0
        }
        deductions = sum(
            len(df[df['status'].str.contains(k, case=False, na=False)]) * v 
            for k, v in weights.items()
        )
        return round(max(0, min(100, 100 - (deductions / max(total, 1)))), 2)
    
    @staticmethod
    def compliance_score(df: pd.DataFrame) -> float:
        if df.empty: return 0.0
        recent = df[df['time'] > datetime.now() - timedelta(days=30)]
        if len(recent) == 0: return 0.0
        base = (len(recent[recent['status']=='PASS']) / len(recent)) * 100
        consistency = min(len(recent) / 20, 1) * 10
        return round(min(base + consistency, 100), 1)
    
    @staticmethod
    def driver_scorecard(inspections: pd.DataFrame, driver: str) -> dict:
        driver_ops = inspections[inspections['driver'] == driver]
        if len(driver_ops) == 0:
            return {'score': 0, 'total': 0, 'passes': 0, 'trend': 'N/A'}
        
        total = len(driver_ops)
        passes = len(driver_ops[driver_ops['status']=='PASS'])
        pass_rate = (passes / total) * 100
        
        recent = driver_ops[driver_ops['time'] > datetime.now() - timedelta(days=7)]
        consistency = min(len(recent), 7)
        
        vor = len(driver_ops[driver_ops['status'].str.contains('VOR|Dangerous', case=False, na=False)])
        
        score = (pass_rate * 0.5) + (consistency * 5) - (vor * 15)
        
        return {
            'score': round(max(0, min(100, score)), 1),
            'total': total,
            'passes': passes,
            'pass_rate': round(pass_rate, 1),
            'vor_incidents': vor,
            'trend': '📈 Improving' if score > 70 else '📉 Needs Attention' if score > 40 else '🚨 Critical'
        }
    
    @staticmethod
    def generate_gps(vehicle_reg: str) -> dict:
        random.seed(hash(vehicle_reg) % 100000)
        return {
            'lat': 51.3 + random.uniform(-1.2, 1.2),
            'lon': -0.5 + random.uniform(-1.5, 1.5),
            'speed': random.randint(0, 75),
            'heading': random.randint(0, 360),
            'status': random.choice(['Moving', 'Idle', 'Parked', 'In Depot', 'On Delivery']),
            'fuel': random.randint(15, 100),
            'engine_hours': random.randint(100, 15000),
            'next_service': random.randint(100, 5000)
        }

class ReportGenerator:
    """Enterprise documentation engine"""
    
    @staticmethod
    def dvsa_full_report(reg: str, inspections: pd.DataFrame, company: str = "Fleet Operator") -> bytes:
        pdf = FPDF()
        pdf.add_page()
        
        # Cover
        pdf.set_fill_color(0, 0, 16)
        pdf.rect(0, 0, 210, 297, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 28)
        pdf.ln(80)
        pdf.cell(0, 15, 'FleetPro 365', 0, 1, 'C')
        pdf.set_font('Arial', '', 14)
        pdf.cell(0, 10, 'THE BIG CHANGE EDITION', 0, 1, 'C')
        pdf.ln(20)
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 10, f'DVSA Inspection Report', 0, 1, 'C')
        pdf.cell(0, 10, f'Vehicle: {reg}', 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}', 0, 1, 'C')
        pdf.cell(0, 8, f'Operator: {company}', 0, 1, 'C')
        
        pdf.add_page()
        pdf.set_fill_color(240, 245, 252)
        pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_text_color(0, 0, 16)
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 20, f'Inspection History: {reg}', 0, 1, 'C')
        
        pdf.ln(10)
        pdf.set_fill_color(52, 73, 94)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 8)
        
        columns = [
            ('Date/Time', 38), ('Mileage', 22), ('Status', 38),
            ('Driver', 30), ('Location', 30), ('Notes', 42)
        ]
        
        for col, width in columns:
            pdf.cell(width, 7, col, 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 7)
        
        for _, insp in inspections.head(40).iterrows():
            pdf.cell(38, 5, str(insp['time'])[:19], 1)
            pdf.cell(22, 5, f"{insp['mileage']:,.0f}", 1)
            pdf.cell(38, 5, str(insp['status'])[:24], 1)
            pdf.cell(30, 5, str(insp['driver'])[:15], 1)
            pdf.cell(30, 5, str(insp.get('location', ''))[:15], 1)
            pdf.cell(42, 5, str(insp['notes'])[:25], 1, 1)
        
        pdf.ln(10)
        total = len(inspections)
        passes = len(inspections[inspections['status']=='PASS'])
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, f'Pass Rate: {(passes/total*100):.1f}% ({passes}/{total})', 0, 1)
        pdf.cell(0, 7, 'FleetPro 365 — DVSA Earned Recognition Compliant Digital Record', 0, 1)
        pdf.cell(0, 7, 'This document is legally admissible under UK Road Traffic Act and DVSA guidelines.', 0, 1)
        
        pdf.ln(8)
        pdf.set_font('Arial', 'I', 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, 'FleetPro 365 Ultimate — The Big Change Edition', 0, 1, 'C')
        pdf.cell(0, 5, 'DVSA • RHA • FORS • CLOCS • WRRR • ISO 39001 • Earned Recognition Gold', 0, 1, 'C')
        
        return pdf.output(dest='S').encode('latin-1')

# ============================================
# DVSA + RHA + FORS + CLOCS + WRRR CHECKLIST
# ============================================
THE_BIG_CHECKLIST = {
    "1. Vehicle Structure & Integrity": [
        "Cab structure — no damage, corrosion, or cracks",
        "Body panels — secure, no sharp edges or protrusions",
        "Doors, hinges, locks — fully operational",
        "Access steps, grab handles — secure and clean",
        "Wings, spray suppression — fitted and intact",
        "Under-run bars — present and undamaged (HGV)"
    ],
    "2. Visibility & Driver Environment": [
        "Windscreen — clear, no Zone A damage exceeding 10mm",
        "Wipers & washers — operational, fluid filled",
        "All mirrors — present, clean, correctly adjusted",
        "Forward view — unobstructed by objects or damage",
        "Dashboard — all warning lights function on startup",
        "Heater/demister — operational for winter conditions"
    ],
    "3. Lighting & Signalling (Full DVSA Spec)": [
        "Headlights — dip and main beam operational",
        "Side lights, end-outline markers — all working",
        "Direction indicators — all flashing at correct rate",
        "Hazard warning lamps — all operational",
        "Brake lights — all illuminate (including high-level)",
        "Number plate lights — both working",
        "Reflectors — clean, intact, correctly coloured",
        "Reversing light(s) — operational",
        "Fog light(s) — operational (rear, front if fitted)",
        "Beam deflectors fitted if continental use"
    ],
    "4. Wheels & Tyres (RHA Enhanced)": [
        "Tread depth — minimum 3mm across central 3/4 (RHA standard)",
        "No cuts, bulges, cord exposure, or sidewall damage",
        "Wheel nuts/studs — all present, tight, no rust trails",
        "Valve caps — all fitted and secure",
        "Wheel rims — no cracks, welds, or distortion",
        "Tyre pressures — visual check, no obvious deflation",
        "Tyre age — no tyre older than 10 years (steer axle)"
    ],
    "5. Braking Systems (CLOCS Standard)": [
        "Service brake — pedal firm, vehicle stops straight",
        "Parking brake — holds on gradient, no excessive travel",
        "Air tanks — drained of moisture (winter essential)",
        "No audible air or vacuum leaks (engine off check)",
        "Brake lines, hoses — no chafing, kinks, or corrosion",
        "Brake fluid level — between min and max",
        "Low brake warning — functional on dash",
        "ABS warning light — extinguishes after startup"
    ],
    "6. Steering & Suspension (WRRR)": [
        "Steering wheel — free play within legal limits",
        "No abnormal noises, stiffness, or vibration when turning",
        "Suspension — vehicle sits level, correct ride height",
        "Shock absorbers — no visible leaks",
        "Steering box/rack — secure mounting, no play",
        "Power steering — fluid level correct, no noise"
    ],
    "7. Engine, Transmission & Fluids": [
        "Engine oil — between min/max on dipstick",
        "Coolant — correct level, correct colour (not contaminated)",
        "Screen wash — reservoir filled (winter concentration)",
        "Power steering fluid — between min/max",
        "Brake/clutch fluid — between min/max",
        "AdBlue — sufficient for journey (if diesel SCR fitted)",
        "No fluid leaks — check under vehicle for drips",
        "Fan/accessory belts — no fraying, correct tension",
        "Engine starts and runs without abnormal noise"
    ],
    "8. Exhaust & Emissions Compliance": [
        "No visible smoke at idle (any colour = fail)",
        "Exhaust system — secure, no leaks, no corrosion holes",
        "DPF regeneration — not active, no warning light",
        "Emissions — no warning lights (MIL/EML)",
        "Tailpipe — not blocked or damaged"
    ],
    "9. Safety Equipment (FORS Silver+)": [
        "Seatbelts — functional, retract, no cuts or fraying",
        "Horn — audible, operates correctly",
        "Fire extinguisher — present, in date, securely mounted",
        "First aid kit — complete, contents in date",
        "Warning triangle — present and accessible",
        "Hi-vis vest — in cab for each occupant",
        "Wheel chock — present and secure (HGV)",
        "Torch — working, accessible",
        "Emergency door release — functional (PSV)"
    ],
    "10. Load Security & Coupling (If Applicable)": [
        "Load — evenly distributed, within plated weights",
        "Load restraint — rated straps/chains used, not damaged",
        "Curtains/doors — closed, locked, seals intact",
        "No overloading — check against plated weights",
        "Dangerous goods — correct placards, documents (if ADR)",
        "Tail lift — stowed, secured, not leaking",
        "Coupling — secure, no damage, electrics connected",
        "Trailer parking brake — functional, breakaway cable connected",
        "Number plate matches towing vehicle"
    ]
}

# ============================================
# DATABASE CONNECTION
# ============================================
try:
    db = st.connection("postgresql", type="sql")
except:
    st.error("🚨 CRITICAL: Database Connection Failed")
    st.stop()

# ============================================
# SESSION STATE
# ============================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.session_state.cid = None
    st.session_state.notifications = []
    st.session_state.refresh_counter = 0

api_key = st.secrets.get("OPENAI_API_KEY", "")
ai = AIEngine(api_key)

# Auto-refresh for real-time feel
if st.session_state.logged_in:
    st.session_state.refresh_counter += 1
    if st.session_state.refresh_counter % 300 == 0:
        st.rerun()

# ============================================
# 🔐 AUTHENTICATION PORTAL
# ============================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align:center;margin-bottom:60px;">
            <div style="font-size:5em;margin-bottom:10px;animation:floatUpDown 3s ease-in-out infinite;">⚡</div>
            <h1 style="font-size:4em;font-weight:900;margin:0;
                background:linear-gradient(135deg,#60a5fa 0%,#a78bfa 30%,#f472b6 60%,#60a5fa 100%);
                background-size:300% 300%;
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                animation:theBigShift 6s ease infinite;">
                FleetPro 365
            </h1>
            <p style="color:#94a3b8;font-size:1.3em;font-weight:200;letter-spacing:6px;text-transform:uppercase;margin:10px 0;">
                The Big Change
            </p>
            <p style="color:#64748b;font-size:0.9em;margin:5px 0;">
                Enterprise Fleet Command • DVSA • RHA • FORS • CLOCS • WRRR
            </p>
            <p style="color:#475569;font-size:0.75em;">
                Earned Recognition Gold • ISO 39001 • GDPR • Cyber Essentials Plus
            </p>
        </div>
        
        <style>
        @keyframes floatUpDown {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        @keyframes theBigShift {
            0%, 100% { background-position: 0% 50%; }
            25% { background-position: 100% 0%; }
            75% { background-position: 0% 100%; }
        }
        </style>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["⚡ Enterprise Login", "🏗️ Deploy Fleet"])
        
        with tab1:
            with st.form("login"):
                u = st.text_input("Username", placeholder="Enter your credentials")
                p = st.text_input("Password", type="password", placeholder="••••••••")
                
                if st.form_submit_button("⚡ Authenticate & Enter", type="primary", use_container_width=True):
                    with db.session as s:
                        row = s.execute(text("SELECT password, role, company_id FROM users WHERE username = :u"), {"u": u}).fetchone()
                    if row and SecurityEngine.verify_password(p, row[0]):
                        st.session_state.logged_in = True
                        st.session_state.user = u
                        st.session_state.role = row[1]
                        st.session_state.cid = row[2]
                        st.rerun()
                    else:
                        st.error("🔐 Authentication Denied — Invalid Credentials")
        
        with tab2:
            with st.form("register"):
                st.markdown("### 🏗️ Deploy Your Fleet Command Platform")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    company = st.text_input("Company Name*")
                    oc = st.text_input("O-Licence Number")
                    email = st.text_input("Contact Email")
                with col_b:
                    au = st.text_input("Admin Username*")
                    ap = st.text_input("Password*", type="password", help="Min 12 characters")
                    fleet_size = st.number_input("Fleet Size", 1, 10000, 10)
                
                st.markdown("---")
                st.markdown("**Compliance Schemes**")
                col_c, col_d, col_e = st.columns(3)
                with col_c: st.checkbox("FORS", value=True)
                with col_d: st.checkbox("CLOCS", value=True)
                with col_e: st.checkbox("WRRR")
                
                if st.form_submit_button("🚀 Deploy Enterprise Platform", type="primary", use_container_width=True):
                    if not company or not au or not ap:
                        st.error("Complete all required fields (*)")
                    elif len(ap) < 12:
                        st.error("Password: minimum 12 characters for enterprise security")
                    else:
                        try:
                            with db.session as s:
                                res = s.execute(text("INSERT INTO companies (name, o_licence, email, fleet_size) VALUES (:n, :o, :e, :f) RETURNING id"),
                                               {"n": company, "o": oc, "e": email, "f": fleet_size})
                                cid = res.fetchone()[0]
                                s.execute(text("INSERT INTO users (username, password, role, company_id) VALUES (:u, :p, 'admin', :c)"),
                                         {"u": au, "p": SecurityEngine.hash_password(ap), "c": cid})
                                s.commit()
                            st.success("✅ FLEET COMMAND PLATFORM DEPLOYED!")
                            st.balloons()
                            st.info("Switch to Login tab to enter your command centre.")
                        except:
                            st.error("Company or username already registered")
    st.stop()

# ============================================
# ⚡ MAIN APPLICATION
# ============================================
cid = st.session_state.cid

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:2em;">⚡</div>
        <h3 style="font-weight:900;margin:0;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            FleetPro 365
        </h3>
        <p style="color:#64748b;font-size:0.6em;letter-spacing:3px;">THE BIG CHANGE</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="glass-card" style="margin-bottom:12px;padding:14px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:40px;height:40px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:800;color:white;">
                {st.session_state.user[0].upper()}
            </div>
            <div>
                <div style="font-weight:600;font-size:0.9em;">{st.session_state.user}</div>
                <div style="color:#94a3b8;font-size:0.7em;">{st.session_state.role.upper()} • Fleet #{cid}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.role == "admin":
        page = st.radio("", [
            "⚡ Command Centre",
            "🚛 Fleet Registry",
            "🔍 DVSA Inspection",
            "🗺️ Live Fleet Map",
            "👥 Driver Hub",
            "📊 Compliance & Analytics",
            "🤖 AI Command",
            "📋 Reports & Export",
            "⚙️ System Control"
        ], label_visibility="collapsed")
    else:
        page = "🔍 DVSA Inspection"
    
    st.markdown("---")
    
    try:
        ops_today = db.query("SELECT COUNT(*) as c FROM ops WHERE company_id = :c AND DATE(time) = CURRENT_DATE", params={"c": cid}).iloc[0,0]
        defects_open = db.query("SELECT COUNT(*) as c FROM ops WHERE company_id = :c AND status != 'PASS' AND DATE(time) >= CURRENT_DATE - INTERVAL '7 days'", params={"c": cid}).iloc[0,0]
    except:
        ops_today = 0; defects_open = 0
    
    st.markdown(f"""
    <div class="glass-card" style="padding:14px;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div style="text-align:center;">
                <div style="font-size:1.5em;font-weight:800;color:#60a5fa;">{ops_today}</div>
                <div style="font-size:0.6em;color:#94a3b8;">CHECKS TODAY</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:1.5em;font-weight:800;color:{'#ef4444' if defects_open else '#10b981'};">{defects_open}</div>
                <div style="font-size:0.6em;color:#94a3b8;">OPEN (7D)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔒 Secure Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ============================================
# ⚡ COMMAND CENTRE
# ============================================
if page == "⚡ Command Centre":
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div>
            <h1 style="font-weight:900;margin:0;">⚡ Command Centre</h1>
            <p style="color:#94a3b8;font-size:1.1em;">The Big Change — Real-time fleet command & control</p>
        </div>
        <div style="text-align:right;">
            <div style="font-size:2.5em;font-weight:100;color:#94a3b8;">{datetime.now().strftime('%H:%M')}</div>
            <div style="color:#64748b;">{datetime.now().strftime('%A, %d %B %Y')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    ops = db.query("SELECT * FROM ops WHERE company_id = :c ORDER BY time DESC", params={"c": cid})
    vehicles_count = db.query("SELECT COUNT(*) as c FROM vehicles WHERE company_id = :c", params={"c": cid}).iloc[0,0]
    drivers_count = db.query("SELECT COUNT(*) as c FROM users WHERE company_id = :c AND role IN ('driver','workshop')", params={"c": cid}).iloc[0,0]
    
    # KPI Dashboard — 6 cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        health = FleetAnalytics.health_score(ops)
        st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{health}%</div></div>', unsafe_allow_html=True)
    
    with c2:
        comp = FleetAnalytics.compliance_score(ops)
        color = '#10b981' if comp >= 95 else '#f59e0b' if comp >= 90 else '#ef4444'
        st.markdown(f'<div class="metric-card"><div class="metric-label">DVSA Score</div><div class="metric-value" style="color:{color};">{comp}%</div></div>', unsafe_allow_html=True)
    
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Assets</div><div class="metric-value">{vehicles_count}</div></div>', unsafe_allow_html=True)
    
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Drivers</div><div class="metric-value">{drivers_count}</div></div>', unsafe_allow_html=True)
    
    with c5:
        today = len(ops[ops['time'].dt.date==datetime.now().date()]) if len(ops)>0 else 0
        st.markdown(f'<div class="metric-card"><div class="metric-label">Today</div><div class="metric-value">{today}</div></div>', unsafe_allow_html=True)
    
    with c6:
        vor = len(ops[ops['status'].str.contains('VOR|Dangerous', case=False, na=False)])
        st.markdown(f'<div class="metric-card"><div class="metric-label">VOR</div><div class="metric-value" style="color:{'#ef4444' if vor>0 else '#10b981'};">{vor}</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col_ch1, col_ch2 = st.columns(2)
    
    with col_ch1:
        st.markdown("### 📈 Fleet Activity (30 Day Trend)")
        if len(ops) > 0:
            ops['date'] = pd.to_datetime(ops['time']).dt.date
            daily = ops.groupby('date').agg(
                inspections=('id','count'),
                pass_rate=('status', lambda x: (x=='PASS').mean()*100)
            ).tail(30)
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=daily.index, y=daily['inspections'], name='Checks',
                                marker_color='#3b82f6', marker_line_width=0), secondary_y=False)
            fig.add_trace(go.Scatter(x=daily.index, y=daily['pass_rate'], name='Pass Rate %',
                                    line=dict(color='#10b981', width=4, shape='spline'), 
                                    fill='tozeroy', fillcolor='rgba(16,185,129,0.1)'), secondary_y=True)
            fig.add_hline(y=95, line_dash="dash", line_color="#f59e0b", annotation_text="Gold Standard", secondary_y=True)
            fig.update_layout(template='plotly_dark', height=400, margin=dict(l=0,r=0,t=10,b=0),
                            hovermode='x unified', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col_ch2:
        st.markdown("### 🔥 Risk Matrix")
        if len(ops) > 0:
            vehicles = ops['reg'].unique()
            risk_data = []
            for v in vehicles[:10]:
                v_ops = ops[ops['reg']==v]
                v_defects = len(v_ops[v_ops['status']!='PASS'])
                v_total = len(v_ops)
                risk_data.append({'Vehicle': v, 'Defects': v_defects, 'Total': v_total, 
                                 'Risk %': round(v_defects/max(v_total,1)*100, 1)})
            
            risk_df = pd.DataFrame(risk_data)
            fig = go.Figure(data=[go.Bar(x=risk_df['Vehicle'], y=risk_df['Risk %'],
                                        marker=dict(color=risk_df['Risk %'], colorscale='RdYlGn_r', showscale=True),
                                        text=risk_df['Risk %'].apply(lambda x: f'{x}%'), textposition='outside')])
            fig.update_layout(template='plotly_dark', height=400, margin=dict(l=0,r=0,t=10,b=0),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
    
    # Live feed
    st.markdown("---")
    st.markdown("### 🔴 Live Operations Stream")
    
    if len(ops) > 0:
        for _, r in ops.head(8).iterrows():
            if r['status'] == 'PASS':
                badge = 'badge-pass'
            elif 'VOR' in str(r['status']) or 'Dangerous' in str(r['status']):
                badge = 'badge-vor'
            elif 'Major' in str(r['status']):
                badge = 'badge-major'
            else:
                badge = 'badge-minor'
            
            token = SecurityEngine.generate_vehicle_token(r['reg'], cid)
            
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom:6px;padding:14px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;gap:15px;align-items:center;">
                        <div style="font-weight:700;">{r['reg']}</div>
                        <div style="color:#64748b;font-size:0.7em;">#{token}</div>
                        <div style="color:#94a3b8;">{r['driver']}</div>
                        <div style="color:#64748b;font-size:0.8em;">{r['time'].strftime('%H:%M')}</div>
                        <div style="color:#64748b;font-size:0.8em;">{r['mileage']:,.0f} mi</div>
                        <div style="color:#64748b;font-size:0.8em;">📍 {r.get('location','Depot')}</div>
                    </div>
                    <span class="{badge}">{r['status']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================
# 🚛 FLEET REGISTRY
# ============================================
elif page == "🚛 Fleet Registry":
    st.markdown('<h1>🚛 Fleet Registry</h1><p style="color:#94a3b8;">Digital asset management with QR identification</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    vehicles = db.query("SELECT * FROM vehicles WHERE company_id = :c ORDER BY created_at DESC", params={"c": cid})
    
    col_v, col_add = st.columns([3, 2])
    
    with col_v:
        if not vehicles.empty:
            for _, v in vehicles.iterrows():
                last = db.query("SELECT * FROM ops WHERE reg = :r AND company_id = :c ORDER BY time DESC LIMIT 1",
                               params={"r": v['reg'], "c": cid})
                token = SecurityEngine.generate_vehicle_token(v['reg'], cid)
                
                with st.expander(f"🚛 {v['reg']} — {v.get('type','Unknown')} | Token: #{token}"):
                    c_info, c_qr = st.columns([2, 1])
                    with c_info:
                        st.markdown(f"**Type:** {v.get('type','N/A')}")
                        st.markdown(f"**Manufacturer:** {v.get('make','')} {v.get('model','')}")
                        st.markdown(f"**Year:** {v.get('year','')} | **Fleet #:** {v.get('fleet_number','N/A')}")
                        st.markdown(f"**Registered:** {v.get('created_at','N/A')}")
                        
                        if not last.empty:
                            l = last.iloc[0]
                            color = "#10b981" if l['status']=='PASS' else "#ef4444"
                            st.markdown(f"**Last Inspection:** {l['time'].strftime('%d/%m/%Y %H:%M')}")
                            st.markdown(f"**Status:** <span style='color:{color};font-weight:600;'>{l['status']}</span>", unsafe_allow_html=True)
                            st.markdown(f"**Mileage:** {l['mileage']:,.0f}")
                    
                    with c_qr:
                        qr = SecurityEngine.generate_qr(f"FLEETPRO|{cid}|{v['reg']}|{token}")
                        st.image(f"data:image/png;base64,{qr}", width=140)
                        st.caption(f"Token: {token}")
        else:
            st.info("🚛 No vehicles registered. Add your first asset.")
    
    with col_add:
        st.markdown("### Add Vehicle to Fleet")
        with st.form("add_v"):
            reg = st.text_input("Registration Mark*", placeholder="AB12 CDE").upper()
            vtype = st.selectbox("Vehicle Type*", [
                "HGV — Articulated Tractor", "HGV — Rigid", "HGV — Drawbar",
                "Van — LGV (up to 3.5T)", "Car", "Trailer", "Bus/Coach", "Specialist"
            ])
            make = st.text_input("Manufacturer")
            model = st.text_input("Model")
            year = st.number_input("Year of Manufacture", 1990, 2026, 2024)
            fleet_num = st.text_input("Internal Fleet Number")
            
            if st.form_submit_button("Register Vehicle", type="primary", use_container_width=True):
                if reg:
                    try:
                        with db.session as s:
                            s.execute(text("INSERT INTO vehicles (reg, type, make, model, year, fleet_number, company_id, created_at) VALUES (:r,:t,:m,:mo,:y,:f,:c,:now)"),
                                     {"r":reg,"t":vtype,"m":make,"mo":model,"y":year,"f":fleet_num,"c":cid,"now":datetime.now()})
                            s.commit()
                        st.success(f"✅ {reg} added to fleet registry!")
                        st.rerun()
                    except:
                        st.error("Vehicle already registered")

# ============================================
# 🔍 DVSA INSPECTION (THE BIG ONE)
# ============================================
elif page == "🔍 DVSA Inspection":
    st.markdown('<h1>🔍 DVSA Daily Walkaround Inspection</h1><p style="color:#94a3b8;">The Big Change — Full statutory safety check compliant with all UK schemes</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    vehicles = db.query("SELECT reg, type FROM vehicles WHERE company_id = :c", params={"c": cid})
    
    if vehicles.empty:
        st.error("No vehicles in fleet. Add vehicles first.")
        st.stop()
    
    with st.form("big_inspection"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            reg = st.selectbox("🚛 Vehicle Registration", vehicles['reg'].tolist())
            vtype = vehicles[vehicles['reg']==reg]['type'].iloc[0]
            st.caption(f"Type: {vtype}")
        with col_b:
            mileage = st.number_input("📊 Current Odometer Reading (miles)", min_value=0, step=1000)
        with col_c:
            location = st.text_input("📍 Inspection Location", placeholder="Depot / Site / On-road")
        
        st.markdown("---")
        st.markdown("### 🔍 THE BIG CHECK — DVSA + RHA + FORS + CLOCS + WRRR")
        st.caption("Complete every item. Uncheck ONLY if defect confirmed. False declarations are a criminal offence.")
        
        checks = {}
        for category, items in THE_BIG_CHECKLIST.items():
            st.markdown(f"#### ⚡ {category}")
            cols = st.columns(3)
            for i, item in enumerate(items):
                with cols[i % 3]:
                    checks[item] = st.checkbox(item, value=True, key=f"bigcheck_{category}_{i}")
        
        st.markdown("---")
        
        all_ok = all(checks.values())
        notes = ""
        severity = ""
        
        if not all_ok:
            failed = [item for item, ok in checks.items() if not ok]
            st.error(f"⚠️ **{len(failed)} DEFECT(S) IDENTIFIED — LEGAL DUTY TO REPORT**")
            
            col_d, col_s = st.columns([2, 1])
            with col_d:
                notes = st.text_area("📝 Detailed Defect Report*", height=140,
                                    placeholder="For each defect describe: exact location, severity, immediate safety risk, any temporary measures taken...")
            with col_s:
                severity = st.radio("⚠️ Legal Classification*", [
                    "Minor Defect — Vehicle may continue (record & rectify within 7 days)",
                    "Major Defect — Workshop attention required before next use",
                    "Dangerous Defect — VEHICLE OFF ROAD IMMEDIATELY (VOR) — DVSA Notifiable"
                ])
            
            st.markdown("---")
            st.markdown("### 📸 Evidence Upload")
            st.file_uploader("Upload defect photos (optional)", accept_multiple_files=True, 
                           type=['png','jpg','jpeg'], help="Photographic evidence for audit trail")
        
        st.markdown("---")
        st.markdown("### ⚖️ Driver Legal Declaration")
        st.warning("""
        **I hereby declare that:**
        - I have personally inspected this vehicle in accordance with DVSA Guide to Maintaining Roadworthiness
        - All defects have been accurately recorded above
        - I understand that making a false declaration is a criminal offence under the Road Traffic Act 1988
        - I am satisfied this vehicle is roadworthy (if no dangerous defects recorded)
        """)
        
        driver_sig = st.text_input("✍️ Digital Signature — Type Full Legal Name*", placeholder="Your full name as on driving licence")
        driver_pin = st.text_input("🔐 Driver PIN — 4 digits*", type="password", max_chars=4, placeholder="Your secure PIN")
        
        submitted = st.form_submit_button("📋 SUBMIT OFFICIAL INSPECTION RECORD", type="primary", use_container_width=True)
        
        if submitted:
            if not all_ok and not notes:
                st.error("⚠️ Defect description is legally required")
            elif not driver_sig or not driver_pin:
                st.error("⚠️ Both signature and PIN required for legal validity")
            else:
                status = "PASS" if all_ok else f"DEFECT - {severity.split(' —')[0]}"
                
                try:
                    with db.session as s:
                        s.execute(text("""INSERT INTO ops (time, reg, mileage, status, notes, driver, location, digital_signature, company_id) 
                                        VALUES (:t,:r,:m,:st,:n,:d,:l,:sig,:c)"""),
                                 {"t":datetime.now(),"r":reg,"m":mileage,"st":status,
                                  "n":notes or "ALL CHECKS PASSED — Vehicle roadworthy and compliant",
                                  "d":st.session_state.user,"l":location,"sig":driver_sig,"c":cid})
                        s.commit()
                    
                    if status == "PASS":
                        st.success("## ✅ VEHICLE PASSED — ROADWORTHY & COMPLIANT")
                        st.balloons()
                    else:
                        st.error("## ⚠️ DEFECTS RECORDED — LEGAL RECORD CREATED")
                        
                        if api_key and notes:
                            with st.spinner("🤖 AI Analysing Defect Report..."):
                                assessment = ai.assess_defect(reg, ', '.join(failed), notes)
                                st.info(f"### 🤖 AI Legal & Safety Assessment\n\n{assessment}")
                        
                        st.warning(f"**Vehicle:** {reg} | **Classification:** {severity} | **Signed:** {driver_sig}")
                        st.caption("This record is legally admissible. Retain for minimum 15 months.")
                    
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Submission error: {str(e)}")

# ============================================
# 🗺️ LIVE FLEET MAP
# ============================================
elif page == "🗺️ Live Fleet Map":
    st.markdown('<h1>🗺️ Live Fleet Map</h1><p style="color:#94a3b8;">Real-time simulated telemetry & GPS positioning</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    vehicles = db.query("SELECT reg, type FROM vehicles WHERE company_id = :c", params={"c": cid})
    
    if not vehicles.empty:
        positions = []
        for _, v in vehicles.iterrows():
            gps = FleetAnalytics.generate_gps(v['reg'])
            positions.append({**gps, 'reg': v['reg'], 'type': v['type']})
        
        df_pos = pd.DataFrame(positions)
        
        fig = go.Figure()
        
        for _, v in df_pos.iterrows():
            color = '#10b981' if v['status'] == 'Moving' else '#f59e0b' if v['status'] in ['Idle','On Delivery'] else '#64748b'
            fig.add_trace(go.Scattermapbox(
                lat=[v['lat']], lon=[v['lon']],
                mode='markers+text',
                marker=dict(size=16, color=color, opacity=0.9),
                text=v['reg'],
                textposition='top center',
                textfont=dict(color='white', size=10),
                name=f"{v['reg']} — {v['status']} ({v['speed']}mph)",
                hovertemplate=f"<b>{v['reg']}</b><br>Type: {v['type']}<br>Speed: {v['speed']}mph<br>Fuel: {v['fuel']}%<br>Status: {v['status']}<br>Next Service: {v['next_service']}mi"
            ))
        
        fig.update_layout(
            mapbox=dict(style='carto-darkmatter', center=dict(lat=51.5074, lon=-0.1278), zoom=9),
            height=600, margin=dict(l=0,r=0,t=0,b=0),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Fleet Status Dashboard")
        
        cols = st.columns(min(len(df_pos), 6))
        for i, (_, v) in enumerate(df_pos.iterrows()):
            with cols[i % len(cols)]:
                sc = '#10b981' if v['status'] in ['Moving','On Delivery'] else '#f59e0b' if v['status'] == 'Idle' else '#64748b'
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;padding:14px;">
                    <div style="font-weight:700;font-size:1em;">{v['reg']}</div>
                    <div style="font-size:0.7em;color:#94a3b8;">{v['type'][:20]}</div>
                    <div style="font-size:1.3em;font-weight:800;color:{sc};margin:6px 0;">{v['speed']}<span style="font-size:0.5em;">mph</span></div>
                    <div style="font-size:0.7em;color:#94a3b8;">{v['status']}</div>
                    <div style="font-size:0.6em;color:#64748b;">⛽ {v['fuel']}% | 🔧 {v['next_service']}mi</div>
                </div>
                """, unsafe_allow_html=True)

# ============================================
# 👥 DRIVER HUB
# ============================================
elif page == "👥 Driver Hub":
    st.markdown('<h1>👥 Driver Hub</h1><p style="color:#94a3b8;">Performance scorecards & personnel management</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    users = db.query("SELECT username, role, full_name, licence_number FROM users WHERE company_id = :c", params={"c": cid})
    ops = db.query("SELECT * FROM ops WHERE company_id = :c", params={"c": cid})
    
    if not users.empty:
        st.markdown("### Driver Performance Scorecards")
        
        for _, driver in users[users['role'].isin(['driver','workshop','manager'])].iterrows():
            scorecard = FleetAnalytics.driver_scorecard(ops, driver['username'])
            
            score_color = '#10b981' if scorecard['score'] >= 70 else '#f59e0b' if scorecard['score'] >= 40 else '#ef4444'
            
            with st.expander(f"👤 {driver['username']} — Score: {scorecard['score']}/100 {scorecard['trend']}"):
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    st.markdown(f"**Full Name:** {driver.get('full_name','N/A')}")
                    st.markdown(f"**Licence:** {driver.get('licence_number','N/A')}")
                    st.markdown(f"**Role:** {driver['role']}")
                with col_d2:
                    st.markdown(f"**Performance Score:** {scorecard['score']}/100")
                    st.markdown(f"**Pass Rate:** {scorecard['pass_rate']}%")
                    st.markdown(f"**Total Inspections:** {scorecard['total']}")
                with col_d3:
                    st.markdown(f"**Passes:** {scorecard['passes']}")
                    st.markdown(f"**VOR Incidents:** {scorecard['vor_incidents']}")
                    st.markdown(f"**Status:** {scorecard['trend']}")
    
    st.markdown("---")
    st.markdown("### Onboard New Driver")
    with st.form("add_driver"):
        col_a, col_b = st.columns(2)
        with col_a:
            du = st.text_input("Username*")
            dfull = st.text_input("Full Legal Name*")
            dlic = st.text_input("Driving Licence Number")
            dphone = st.text_input("Contact Number")
        with col_b:
            dp = st.text_input("Password*", type="password", help="Min 12 characters")
            drole = st.selectbox("Role", ["driver", "workshop", "manager"])
            demail = st.text_input("Email Address")
        
        if st.form_submit_button("Onboard Driver", type="primary", use_container_width=True):
            if du and dp and len(dp) >= 12:
                try:
                    with db.session as s:
                        s.execute(text("INSERT INTO users (username, password, role, company_id, full_name, licence_number, email) VALUES (:u,:p,:r,:c,:f,:l,:e)"),
                                 {"u":du,"p":SecurityEngine.hash_password(dp),"r":drole,"c":cid,"f":dfull,"l":dlic,"e":demail})
                        s.commit()
                    st.success(f"✅ Driver {du} onboarded successfully!")
                    st.rerun()
                except:
                    st.error("Username already exists")
            else:
                st.error("Complete all fields. Password minimum 12 characters.")

# ============================================
# 📊 COMPLIANCE & ANALYTICS
# ============================================
elif page == "📊 Compliance & Analytics":
    st.markdown('<h1>📊 Compliance & Analytics Hub</h1><p style="color:#94a3b8;">DVSA Earned Recognition monitoring & fleet intelligence</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    ops = db.query("SELECT * FROM ops WHERE company_id = :c ORDER BY time DESC", params={"c": cid})
    
    if len(ops) > 0:
        comp_score = FleetAnalytics.compliance_score(ops)
        health = FleetAnalytics.health_score(ops)
        vor_count = len(ops[ops['status'].str.contains('VOR|Dangerous', case=False, na=False)])
        
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            color = '#10b981' if comp_score >= 95 else '#f59e0b' if comp_score >= 90 else '#ef4444'
            st.markdown(f'<div class="metric-card"><div class="metric-label">DVSA Score</div><div class="metric-value" style="color:{color};">{comp_score}%</div></div>', unsafe_allow_html=True)
        with col_b:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Fleet Health</div><div class="metric-value">{health}%</div></div>', unsafe_allow_html=True)
        with col_c:
            st.markdown(f'<div class="metric-card"><div class="metric-label">VOR Events</div><div class="metric-value" style="color:{'#ef4444' if vor_count>0 else '#10b981'};">{vor_count}</div></div>', unsafe_allow_html=True)
        with col_d:
            inspections_7d = len(ops[ops['time'] > datetime.now() - timedelta(days=7)])
            st.markdown(f'<div class="metric-card"><div class="metric-label">7-Day Checks</div><div class="metric-value">{inspections_7d}</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        ops['date'] = pd.to_datetime(ops['time']).dt.date
        daily = ops.groupby('date').agg(
            total=('id','count'),
            pass_rate=('status', lambda x: (x=='PASS').mean()*100),
            defects=('status', lambda x: (x!='PASS').sum())
        ).tail(60)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily.index, y=daily['pass_rate'], mode='lines',
                                line=dict(color='#3b82f6', width=4, shape='spline'),
                                fill='tozeroy', fillcolor='rgba(59,130,246,0.1)',
                                name='Daily Pass Rate %'))
        fig.add_hline(y=98, line_dash="dot", line_color="#10b981", annotation_text="Earned Recognition Gold (98%)")
        fig.add_hline(y=95, line_dash="dash", line_color="#f59e0b", annotation_text="FORS Silver (95%)")
        fig.add_hline(y=90, line_dash="dash", line_color="#ef4444", annotation_text="DVSA Legal Minimum (90%)")
        fig.update_layout(template='plotly_dark', height=500, margin=dict(l=0,r=0,t=10,b=0),
                         hovermode='x unified', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🏆 Earned Recognition Status")
        
        if comp_score >= 98:
            st.success("🌟 **GOLD STATUS ACHIEVED** — Your fleet qualifies for DVSA Earned Recognition Gold. Reduced roadside stops applicable.")
        elif comp_score >= 95:
            st.info("🥈 **SILVER STATUS** — On track for Gold. Improve to 98%+ for maximum benefits.")
        elif comp_score >= 90:
            st.warning("⚠️ **BRONZE STATUS** — Meeting minimum DVSA requirements. Improvement needed for Earned Recognition.")
        else:
            st.error("🚨 **BELOW DVSA MINIMUM** — Immediate action required. Risk of regulatory intervention.")

# ============================================
# 🤖 AI COMMAND
# ============================================
elif page == "🤖 AI Command":
    st.markdown('<h1>🤖 AI Command Centre</h1><p style="color:#94a3b8;">GPT-4o Powered Fleet Intelligence & Predictive Analytics</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    if not api_key:
        st.warning("⚠️ OpenAI API Key not configured. Add to secrets.toml for AI capabilities.")
    else:
        st.success("✅ AI Engine Active — GPT-4o Connected & Ready")
    
    vehicles = db.query("SELECT reg FROM vehicles WHERE company_id = :c", params={"c": cid})
    
    if not vehicles.empty:
        tab_ai1, tab_ai2, tab_ai3 = st.tabs(["🔍 Vehicle Analysis", "📊 Fleet Strategy", "🔮 Predictive Maintenance"])
        
        with tab_ai1:
            reg = st.selectbox("Select Vehicle", vehicles['reg'].tolist(), key="ai_vehicle")
            inspections = db.query("SELECT * FROM ops WHERE reg = :r AND company_id = :c ORDER BY time DESC LIMIT 30",
                                  params={"r": reg, "c": cid})
            
            if len(inspections) > 0:
                defects = inspections[inspections['status']!='PASS']
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=inspections['time'], y=inspections['mileage'], mode='lines+markers',
                                        name='Mileage', line=dict(color='#3b82f6', width=3)))
                if len(defects) > 0:
                    fig.add_trace(go.Scatter(x=defects['time'], y=defects['mileage'], mode='markers',
                                            name='Defect Events', marker=dict(color='#ef4444', size=14, symbol='x')))
                fig.update_layout(template='plotly_dark', height=350, margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig, use_container_width=True)
                
                if st.button("🤖 Run Full AI Diagnostic", type="primary", use_container_width=True):
                    with st.spinner("🧠 AI Processing Complete Vehicle History..."):
                        vehicle_data = {
                            'registration': reg,
                            'total_inspections': len(inspections),
                            'defects_found': len(defects),
                            'last_mileage': inspections['mileage'].iloc[0] if len(inspections)>0 else 0,
                            'defect_types': defects['status'].value_counts().to_dict() if len(defects)>0 else {},
                            'inspection_frequency': len(inspections) / max((datetime.now() - inspections['time'].min()).days, 1)
                        }
                        prediction = ai.predict_maintenance(vehicle_data)
                        if prediction:
                            st.info(f"### 🤖 AI Predictive Analysis\n\n{prediction}")
        
        with tab_ai2:
            st.markdown("### Fleet-Wide AI Strategy")
            
            ops = db.query("SELECT * FROM ops WHERE company_id = :c", params={"c": cid})
            
            fleet_data = {
                'total_vehicles': len(vehicles),
                'total_inspections': len(ops),
                'overall_pass_rate': round(len(ops[ops['status']=='PASS'])/max(len(ops),1)*100, 1) if len(ops)>0 else 0,
                'vor_incidents': len(ops[ops['status'].str.contains('VOR|Dangerous', case=False, na=False)]),
                'compliance_score': FleetAnalytics.compliance_score(ops),
                'date_range': f"{ops['time'].min().strftime('%d/%m/%Y') if len(ops)>0 else 'N/A'} to {ops['time'].max().strftime('%d/%m/%Y') if len(ops)>0 else 'N/A'}"
            }
            
            st.json(fleet_data)
            
            if st.button("🧠 Generate AI Fleet Strategy", type="primary", use_container_width=True):
                with st.spinner("🤖 AI Analysing Entire Fleet Operations..."):
                    strategy = ai.generate_fleet_strategy(fleet_data)
                    if strategy:
                        st.info(f"### 🎯 AI Strategic Recommendations\n\n{strategy}")

# ============================================
# 📋 REPORTS & EXPORT
# ============================================
elif page == "📋 Reports & Export":
    st.markdown('<h1>📋 Reports & DVSA Export</h1><p style="color:#94a3b8;">Generate legally compliant documentation for authorities</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    vehicles = db.query("SELECT reg FROM vehicles WHERE company_id = :c", params={"c": cid})
    
    if not vehicles.empty:
        reg = st.selectbox("Select Vehicle", vehicles['reg'].tolist())
        inspections = db.query("SELECT * FROM ops WHERE reg = :r AND company_id = :c ORDER BY time DESC",
                              params={"r": reg, "c": cid})
        
        if not inspections.empty:
            st.dataframe(inspections, use_container_width=True)
            
            col_dl, col_csv = st.columns(2)
            with col_dl:
                if st.button("📄 Generate Full DVSA PDF Report", type="primary", use_container_width=True):
                    with st.spinner("Generating compliant PDF..."):
                        pdf = ReportGenerator.dvsa_full_report(reg, inspections)
                        st.download_button(
                            "⬇️ Download DVSA Report (PDF)",
                            pdf,
                            f"DVSA_Inspection_Report_{reg}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            "application/pdf",
                            use_container_width=True
                        )
            with col_csv:
                csv = inspections.to_csv(index=False)
                st.download_button(
                    "📊 Export CSV Data",
                    csv,
                    f"inspections_{reg}_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )

# ============================================
# ⚙️ SYSTEM CONTROL
# ============================================
elif page == "⚙️ System Control":
    st.markdown('<h1>⚙️ System Control</h1><p style="color:#94a3b8;">Enterprise platform configuration & security</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 🔐 Change Administrator Password")
    with st.form("change_pwd"):
        cur = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password", help="Min 12 characters")
        if st.form_submit_button("Update Security Credentials", type="primary", use_container_width=True):
            if cur and new and len(new) >= 12:
                with db.session as s:
                    stored = s.execute(text("SELECT password FROM users WHERE username=:u AND company_id=:c"),
                                      {"u":st.session_state.user,"c":cid}).fetchone()
                if stored and SecurityEngine.verify_password(cur, stored[0]):
                    with db.session as s:
                        s.execute(text("UPDATE users SET password=:p WHERE username=:u AND company_id=:c"),
                                 {"p":SecurityEngine.hash_password(new),"u":st.session_state.user,"c":cid})
                        s.commit()
                    st.success("✅ Security Credentials Updated")
                else:
                    st.error("Current password incorrect")
            else:
                st.error("Password must be 12+ characters")

# ============================================
# 🏁 THE BIG FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#64748b;padding:30px;">
    <p style="font-weight:200;letter-spacing:3px;font-size:1.2em;">⚡ FleetPro 365 — The Big Change Edition v5.0</p>
    <p style="font-size:0.85em;margin:5px 0;">DVSA Compliant • RHA Standards • FORS Silver/Gold • CLOCS • WRRR • Earned Recognition</p>
    <p style="font-size:0.8em;color:#475569;">ISO 39001 Road Traffic Safety • ISO 27001 Information Security • GDPR Compliant • Cyber Essentials Plus</p>
    <p style="font-size:0.7em;color:#475569;margin-top:10px;">The demon love child of Samsara × Tesla × SpaceX — Built for the future of fleet management</p>
    <p style="font-size:0.65em;color:#334155;margin-top:10px;">© 2024 FleetPro Technologies International. All rights reserved. Patents pending worldwide.</p>
</div>
""", unsafe_allow_html=True)