import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

# --- CONFIGURATION ---
MISO_API = "http://localhost:8000"
st.set_page_config(
    page_title="MISO V71: Ouroboros",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLES ---
st.markdown("""
<style>
    .stProgress > div > div > div > div { background-color: #00ff00; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SYSTEM VITALS ---
st.sidebar.title("🧬 MISO V71")
st.sidebar.markdown("**Codename:** Ouroboros")
st.sidebar.markdown("---")

# Fetch System Stats
try:
    stats = requests.get(f"{MISO_API}/system/stats", timeout=2).json()
    status = "🟢 ONLINE"
    
    # 1. Routing Weights (The Deep Optimizer's Work)
    st.sidebar.subheader("🧠 Synaptic Weights")
    weights = stats.get("active_weights", {})
    if weights:
        df_weights = pd.DataFrame(list(weights.items()), columns=["Model", "Weight"])
        fig = px.pie(df_weights, values="Weight", names="Model", hole=0.4)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200, showlegend=False)
        st.sidebar.plotly_chart(fig, use_container_width=True)
    
    # 2. Organ Status
    st.sidebar.subheader("🛡️ Immune System")
    st.sidebar.success(stats.get("immune_system", "Unknown"))
    st.sidebar.subheader("🦴 Backbone")
    st.sidebar.info(stats.get("backbone_status", "Unknown"))

except Exception:
    status = "🔴 OFFLINE"
    st.sidebar.error("Connection Lost to Cortex")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**System Status:** {status}")

# --- MAIN INTERFACE: INTERACTION LOOP ---
st.title("Auto-Didactic Enterprise Intelligence")

tab1, tab2 = st.tabs(["💬 Cortex Chat", "🧬 Evolution Trigger"])

# TAB 1: CHAT
with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input("Direct command to Cortex..."):
        # Add User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                payload = {"type": "chat", "payload": prompt}
                # Check if it looks like code execution
                if prompt.startswith("/run"):
                    payload["type"] = "execute_code"
                    payload["payload"] = prompt.replace("/run ", "")
                
                response = requests.post(f"{MISO_API}/process", json=payload).json()
                
                if response["status"] == "success":
                    data = response["data"]
                    if "response" in data:
                        bot_reply = data["response"]
                    elif "output" in data:
                        bot_reply = f"```\n{data['output']}\n```"
                    else:
                        bot_reply = str(data)
                else:
                    bot_reply = f"❌ Error: {response}"
                
                message_placeholder.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
            except Exception as e:
                message_placeholder.error(f"Synapse Failure: {e}")

# TAB 2: EVOLUTION
with tab2:
    st.header("🧬 Direct Genetic Modification")
    st.warning("Warning: Direct manipulation of source code. The Immune System will reject fatal mutations.")
    
    col1, col2 = st.columns(2)
    with col1:
        target_file = st.text_input("Target File Path", "miso_project/utils/new_tool.py")
    with col2:
        test_file = st.text_input("Validation Test Path (Optional)", "tests/test_new_tool.py")
        
    code_content = st.text_area("Python Source Code", height=300)
    
    if st.button("Inject Mutation"):
        if not code_content:
            st.error("Code payload empty.")
        else:
            with st.spinner("Injecting DNA..."):
                # We pack the file and code using our ||| protocol
                payload_str = f"{target_file}|||{code_content}"
                try:
                    res = requests.post(f"{MISO_API}/process", json={
                        "type": "evolve", 
                        "payload": payload_str
                    }).json()
                    
                    if "Mutation Integrated" in str(res):
                        st.success(f"Mutation Successful: {res}")
                    else:
                        st.error(f"Mutation Rejected: {res}")
                except Exception as e:
                    st.error(f"Injection Failed: {e}")

