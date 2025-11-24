import streamlit as st
import json
import os
import pandas as pd
import time

# CONFIG PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TENANT_FILE = os.path.join(BASE_DIR, "tenants.json")
LEDGER_FILE = os.path.join(BASE_DIR, "ledger.json")
# We assume all agents log to the main worker log or their own files. 
# For V36, let's assume we consolidate logs or read specific agent logs if available.
# Previously we just used 'worker.log'. Let's stick to that for simplicity as most agents log there.
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "worker.log") # Point to project root log

st.set_page_config(page_title="MISO Command", layout="wide", page_icon="🧠")

st.markdown("""
<style>
    .metric-card {background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 1px solid #333;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🏢 MISO Enterprise")
page = st.sidebar.radio("Navigation", ["Overview", "Governance (Boardroom)", "Tenant Management", "System Logs"])

# --- PAGE: OVERVIEW ---
if page == "Overview":
    st.title("🚀 Operational Overview")
    # ... (Same as before) ...
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Tenants", "2", "Clients")
    col2.metric("Total Revenue", "2,450", "+00")
    col3.metric("System Health", "NOMINAL", "CPU < 20%")

# --- PAGE: GOVERNANCE (NEW) ---
elif page == "Governance (Boardroom)":
    st.title("🏛️ Corporate Governance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Executive Strategy (CEO)")
        st.info("Current Directive: EXPAND")
        st.write("**Last Decree:** 'Create a new module for azure billing analysis.'")
        
    with col2:
        st.subheader("💰 Financial Control (CFO)")
        st.metric("Hurdle Rate", "5.5%", "+0.5%")
        st.success("Budget Status: APPROVED")
        
    st.markdown("---")
    st.subheader("🧠 CTO Technical Radar")
    st.warning("Alert: Pattern of 'Timeout' errors detected in GCP region us-east4.")
    
    st.markdown("---")
    st.subheader("📜 Board Meeting Minutes")
    # Mock data for visualization - in prod this reads from board.log
    st.code("""
[BOARD] Meeting Started. Runway: .85.
[BOARD] Motion: Increase marketing spend? -> DENIED (Runway < .00)
[BOARD] Motion: Optimize worker latency? -> APPROVED
    """, language="text")

# --- PAGE: TENANT MANAGEMENT ---
elif page == "Tenant Management":
    st.title("👥 Client Administration")
    # ... (Same as before) ...
    st.info("Tenant management module active.")

# --- PAGE: SYSTEM LOGS ---
elif page == "System Logs":
    st.title("📟 Black Box Telemetry")
    if st.button("Refresh"): st.rerun()
    
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-20:]
                for line in lines:
                    if "ERROR" in line: st.error(line.strip())
                    elif "WARNING" in line: st.warning(line.strip())
                    else: st.text(line.strip())
        else:
            st.warning(f"Log file not found at {LOG_FILE}")
    except Exception as e:
        st.error(f"Error reading logs: {e}")
