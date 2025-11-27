import streamlit as st
import redis
import json
import time
import os
from datetime import datetime

# --- CONFIG ---
st.set_page_config(
    page_title="MISO V43: THE SOVEREIGN",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONNECTIONS ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

@st.cache_resource
def get_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

try:
    r = get_redis()
except Exception as e:
    st.error(f"FATAL: Cannot connect to Synaptic Mesh (Redis). {e}")
    st.stop()

# --- CUSTOM CSS (CYBERPUNK UI) ---
st.markdown("""
    <style>
    /* Force metrics to be visible if theme fails */
    [data-testid="stMetricLabel"] { color: #a0a0a0 !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-family: 'Courier New', monospace; }
    
    /* Custom Cards */
    .plasticity-card {
        background-color: #0d1b2a;
        border-left: 4px solid #00f2ff;
        padding: 15px;
        border-radius: 4px;
        color: #00f2ff;
        font-family: 'Courier New', monospace;
        margin-bottom: 10px;
    }
    .dream-log {
        font-family: 'Courier New', monospace;
        color: #888;
        font-size: 12px;
        border-bottom: 1px solid #222;
        padding: 2px 0;
    }
    .alert-log {
        font-family: 'Courier New', monospace;
        color: #ff4b4b;
        font-weight: bold;
        border-bottom: 1px solid #400;
        padding: 2px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CORTEX CONTROLS ---
st.sidebar.title("🎮 CORTEX CONTROL")
monitoring_active = st.sidebar.toggle("Activate fMRI Monitor", value=True)
refresh_rate = st.sidebar.slider("Synaptic Refresh (s)", 0.5, 5.0, 1.0)

st.sidebar.divider()
if st.sidebar.button("💉 Inject Dopamine (Reset Wallet)"):
    genesis_state = {"address": "ADMIN_INJECT", "balance": 100.00, "status": "SOLVENT"}
    r.set("miso:sovereign:wallet", json.dumps(genesis_state))
    st.sidebar.success("Energy injected.")

if st.sidebar.button("⚡ Trigger Sensory Input (Mock Task)"):
    task = {"id": f"task_{int(time.time())}", "type": "USER_REQUEST", "payload": "Analyze architectural entropy."}
    r.rpush("miso:tasks", json.dumps(task))
    st.sidebar.warning("Stimulus applied.")

# --- MAIN DASHBOARD ---
st.title("🧠 MISO PHOENIX: V43 SOVEREIGN STATE")

col1, col2, col3 = st.columns(3)
backbone_container = col1.empty()
sovereign_container = col2.empty()
scientist_container = col3.empty()

st.divider()

col_log_L, col_log_R = st.columns([2, 1])
with col_log_L:
    st.subheader("🌊 Stream of Consciousness")
    log_container = st.empty()

with col_log_R:
    st.subheader("🧬 State Manifold")
    state_container = st.empty()

# --- LIVE MONITOR LOOP ---
def render_frame():
    # 1. TEMPORAL CORTEX
    try:
        backbone_raw = r.get("miso:backbone:state")
        backbone_data = json.loads(backbone_raw) if backbone_raw else {}
        mode = backbone_data.get("mode", "OFFLINE")
        
        with backbone_container.container():
            st.markdown("### TEMPORAL CORTEX")
            status_color = "🟢" if mode == "DREAM" else "🔴" if mode == "ALERT" else "⚪"
            # Use delta to show entropy change or load
            st.metric("System Mode", f"{status_color} {mode}", delta=f"Entropy: {backbone_data.get('entropy', 0):.4f}")
    except:
        backbone_container.error("Backbone Offline")

    # 2. METABOLIC STATE
    try:
        wallet_raw = r.get("miso:sovereign:wallet")
        wallet_data = json.loads(wallet_raw) if wallet_raw else {}
        balance = wallet_data.get("balance", 0.0)
        status = wallet_data.get("status", "UNKNOWN")
        
        with sovereign_container.container():
            st.markdown("### METABOLIC STATE")
            st.metric("Energy Balance (MISO)", f"{balance:.4f}", delta=status)
    except:
        sovereign_container.error("Sovereign Offline")

    # 3. PLASTICITY (Scientist)
    try:
        experiments = r.lrange("miso:scientist:experiments", -1, -1)
        last_exp = experiments[0] if experiments else "No active mutation."
        
        with scientist_container.container():
            st.markdown("### PLASTICITY (Scientist)")
            # Custom Cyberpunk Card for better readability
            st.markdown(f"""
            <div class="plasticity-card">
                {last_exp}
            </div>
            """, unsafe_allow_html=True)
    except:
        scientist_container.info("Scientist Sleeping")

    # 4. LOGS
    logs = r.lrange("miso:backbone:logs", -10, -1)
    with log_container.container():
        for log in reversed(logs):
            style = "alert-log" if "[ALERT]" in log else "dream-log"
            st.markdown(f"<div class='{style}'>{log}</div>", unsafe_allow_html=True)

    # 5. STATE MANIFOLD (Pretty Print)
    with state_container.container():
        # Using st.code implies dark mode automatically in recent Streamlit versions
        st.code(json.dumps(backbone_data, indent=2), language="json")

if monitoring_active:
    while True:
        render_frame()
        time.sleep(refresh_rate)
else:
    render_frame()
    st.info("Monitoring Paused.")
