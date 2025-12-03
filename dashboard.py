import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import base64
import json
import time

MISO_API = "http://localhost:8000"
st.set_page_config(page_title="MISO Enterprise", page_icon="🔐", layout="wide")

# CSS
st.markdown("""
<style>
    .stChatInput { position: fixed; bottom: 0; padding-bottom: 20px; z-index: 100; }
    .block-container { padding-bottom: 120px; }
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION STATE ---
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# --- LOGIN SCREEN ---
if not st.session_state.api_key:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 MISO Enterprise Login")
        st.markdown("Please enter your access credential.")
        
        with st.form("login_form"):
            key_input = st.text_input("API Key", type="password")
            submitted = st.form_submit_button("Authenticate")
            
            if submitted and key_input:
                st.session_state.api_key = key_input
                st.rerun()
    st.stop() # Stop rendering the rest of the app

# --- MAIN APP (AUTHENTICATED) ---
headers = {"Authorization": f"Bearer {st.session_state.api_key}"}

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏢 MISO Hypervisor")
    
    # System Status & Balance Check
    try:
        # We can hit the stats endpoint, but strictly we should check valid key.
        # Let's try a lightweight check or just rely on the main flow.
        stats = requests.get(f"{MISO_API}/system/stats", headers=headers, timeout=1).json()
        st.success("🟢 System Online")
        
        # We need a way to get user balance. 
        # For now, we'll track it from the last response or show generic status.
        # (In V90 we'd add a /user/me endpoint)
        if st.session_state.user_info:
            bal = st.session_state.user_info.get('balance', 0)
            st.metric("Credit Balance", f"${bal:.4f}")
        
    except Exception as e:
        st.error("🔴 Auth Failure / Offline")
        st.caption(str(e))
        if st.button("Logout"):
            st.session_state.api_key = None
            st.rerun()

    st.divider()
    st.write("### 📸 Visual Input")
    uploaded_file = st.file_uploader("Analyze Image", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    image_b64 = None
    if uploaded_file:
        image_bytes = uploaded_file.getvalue()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        st.image(uploaded_file, caption="Target Acquired", width=200)
    
    if st.button("🔒 Logout"):
        st.session_state.api_key = None
        st.rerun()

# --- CHAT INTERFACE ---
st.header("Enterprise Intelligence Platform")

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"): st.image(base64.b64decode(msg["image"]), width=300)
        content = msg["content"]
        if "Action Result" in str(content): st.markdown(content)
        else: st.write(content)

if prompt := st.chat_input("Direct command to Hypervisor..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ Authenticating & Optimizing...")
        
        try:
            payload = {"type": "chat", "payload": prompt}
            if image_b64: payload["image_data"] = image_b64
            
            if prompt.startswith("/run "):
                payload = {"type": "execute_code", "payload": prompt.replace("/run ", "")}
            elif prompt.startswith("/research "):
                payload = {"type": "research", "payload": prompt.replace("/research ", "")}

            # SEND WITH HEADERS
            res = requests.post(f"{MISO_API}/process", json=payload, headers=headers)
            
            if res.status_code == 403 or res.status_code == 401:
                placeholder.error("⛔ Access Denied. Invalid Key or Insufficient Funds.")
                st.stop()
            
            response_json = res.json()
            data = response_json.get("data", {})
            
            # Update Balance in Session
            if "user_balance" in response_json:
                if not st.session_state.user_info: st.session_state.user_info = {}
                st.session_state.user_info["balance"] = response_json["user_balance"]

            # Render
            if "response" in data:
                content = data["response"]
                if "cost" in data: content += f"\n\n*Transaction Cost: {data['cost']}*"
            elif "output" in data:
                content = f"**⚙️ Backbone Execution:**\n```\n{data['output']}\n```"
            elif "insight" in data:
                content = f"**📚 Research Insight:**\n\n{data['insight']}\n\n**Sources:**"
                for p in data.get("papers", []): content += f"\n- [{p['title']}]({p['url']})"
            else:
                content = str(data)

            placeholder.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})

        except Exception as e:
            placeholder.error(f"Hypervisor Failure: {e}")
