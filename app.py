import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text as sa_text

st.set_page_config(page_title="FleetPro Test", layout="wide")

st.title("🚛 FleetPro 365 — Connection Test")

# Try pooler first
PGHOST = os.environ.get('PGHOST', 'aws-0-eu-west-2.pooler.supabase.com')
PGPORT = os.environ.get('PGPORT', '6543')
PGDATABASE = os.environ.get('PGDATABASE', 'postgres')
PGUSER = os.environ.get('PGUSER', 'postgres.ykpbbeurorjnzbbggfif')
PGPASSWORD = os.environ.get('PGPASSWORD', 'FleetPro2024!')

st.write(f"Connecting to: {PGHOST}:{PGPORT} as {PGUSER}")

url = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}?sslmode=require"

try:
    engine = create_engine(url, connect_args={'connect_timeout': 10})
    with engine.connect() as conn:
        result = conn.execute(sa_text("SELECT 1"))
        st.success("✅ DATABASE CONNECTED!")
except Exception as e:
    st.error(f"❌ Failed: {str(e)[:200]}")
