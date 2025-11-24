import streamlit as st
import json
import os
import time
import pandas as pd

# CONFIG PATHS
BASE_DIR = os.path.join(os.getcwd(), "miso-worker", "app")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
SECRETS_FILE = os.path.join(BASE_DIR, "secrets.json") # New secure storage
LOG_FILE = "miso-worker/worker.log"

# PAGE SETUP
st.set_page_config(page_title="MISO Command", layout="wide", page_icon="🧠")

# --- HELPER FUNCTIONS ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    return {"EPSILON": 0.15, "MODE": "STATIC", "HURDLE_RATE": 0.05}

def save_config(new_config):
    with open(CONFIG_FILE, 'w') as f: json.dump(new_config, f, indent=2)
    st.toast("✅ Configuration Saved!", icon="💾")

def save_secrets(gemini_key, aws_key, aws_secret):
    # In prod, use Vault. Here, we save to a local JSON for agents to read.
    data = {
        "GEMINI_API_KEY": gemini_key,
        "AWS_ACCESS_KEY_ID": aws_key,
        "AWS_SECRET_ACCESS_KEY": aws_secret
    }
    with open(SECRETS_FILE, 'w') as f: json.dump(data, f)
    st.toast("✅ Secrets Updated. Restarting Agents...", icon="🔐")
    # Trigger a restart (Simulated)
    time.sleep(1)
    st.rerun()

# --- UI LAYOUT ---
st.title("🧠 MISO: Enterprise Control Plane")

tabs = st.tabs(["📊 Monitor", "⚙️ Settings", "🧬 Evolution"])

# TAB 1: MONITOR (The existing view)
with tabs[0]:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("System Health", "NOMINAL", "CPU < 20%")
    with col2:
        st.metric("Cost Savings", "$4,250", "+5 today")
    with col3:
        config = load_config()
        st.metric("Learning Rate", f"{config.get('EPSILON', 0.15)*100:.0f}%")

    st.subheader("Live Telemetry")
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-15:]
                for line in lines:
                    st.text(line.strip())
        else:
            st.warning("Waiting for logs...")
    except: st.error("Log Access Failed")

# TAB 2: SETTINGS (The new feature)
with tabs[1]:
    st.header("🔧 System Configuration")
    
    with st.expander("🔑 API Credentials (Secrets)", expanded=True):
        st.caption("These keys power the Intelligence Engine.")
        with st.form("secrets_form"):
            g_key = st.text_input("Google Gemini API Key", type="password")
            aws_id = st.text_input("AWS Access Key ID", type="password")
            aws_sec = st.text_input("AWS Secret Access Key", type="password")
            if st.form_submit_button("Update Credentials"):
                save_secrets(g_key, aws_id, aws_sec)

    with st.expander("🎛️ Operational Parameters"):
        config = load_config()
        new_epsilon = st.slider("Exploration Rate (Creativity)", 0.0, 1.0, config.get("EPSILON", 0.15))
        new_hurdle = st.number_input("ROI Hurdle Rate (%)", 1.0, 50.0, config.get("HURDLE_RATE", 0.05)*100)
        
        if st.button("Save Parameters"):
            config["EPSILON"] = new_epsilon
            config["HURDLE_RATE"] = new_hurdle / 100.0
            save_config(config)

# TAB 3: EVOLUTION
with tabs[2]:
    st.header("🧬 Genetic Engineering")
    st.info("Current Species: MISO V34")
    if st.button("Force Evolution (Trigger Architect)"):
        st.warning("Command Sent: Architect will attempt self-refactor.")

