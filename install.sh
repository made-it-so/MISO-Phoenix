#!/bin/bash
echo "🚀 INITIALIZING MISO PLATFORM..."

# 1. Environment Check
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found."
    exit 1
fi

# 2. Install Core Dependencies (Fast)
echo "📦 Installing Core Engines..."
# Using pip directly for simplicity in this script
pip install -q streamlit boto3 google-generativeai redis psutil requests

# 3. Setup Directory Structure
mkdir -p miso-worker/app
touch miso-worker/app/__init__.py

# 4. Create the Admin Dashboard (Streamlit)
echo "🎨 Building Mission Control UI..."
cat <<UI > dashboard.py
import streamlit as st
import time
import json
import os
import pandas as pd

st.set_page_config(page_title="MISO Command", layout="wide", page_icon="🧠")

# CONFIG
LOG_FILE = "worker.log"
MEMORY_FILE = "miso-worker/app/memory.json"

st.title("🧠 MISO: Autonomous Infrastructure")

# SIDEBAR: Controls
st.sidebar.header("Global Controls")
system_status = st.sidebar.radio("System State", ["ACTIVE", "PAUSED", "MAINTENANCE"])
epsilon = st.sidebar.slider("Exploration Rate (Epsilon)", 0.0, 1.0, 0.15)

# MAIN DASHBOARD
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🛡️ Reflex Status")
    # Mock live data reading
    cpu = 12.5 
    st.metric("CPU Load", f"{cpu}%", "-2%")
    st.success("SYSTEM NOMINAL")

with col2:
    st.subheader("💰 Economic Engine")
    st.metric("Current Savings", "$4,205", "+20 today")
    st.info("Routing: 80% GCP / 20% Azure")

with col3:
    st.subheader("🧬 Evolution")
    st.warning("1 Pending Mutation")
    if st.button("Review Code Change"):
        st.code("def new_logic():\n    return 'optimized'", language='python')
        st.button("Deploy to Production")

# LOG STREAM
st.subheader("Live Telemetry")
try:
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()[-10:]
        for line in lines:
            st.text(line.strip())
except:
    st.text("Waiting for telemetry...")

UI

echo "✅ Installation Complete."
echo "👉 Run 'streamlit run dashboard.py' to launch Mission Control."
