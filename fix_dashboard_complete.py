import os

# The corrected dashboard code
# - Points to http://miso-core:8000 (Internal Docker Network)
# - Parses nested ['data']['answer'] correctly
# - Parses nested ['data']['audit_ledger'] correctly

code = """import streamlit as st
import requests
import base64
import os
from PIL import Image

# FIX: Hardcoded to internal Docker DNS name
MISO_API = "http://miso-core:8000"

st.set_page_config(page_title="MISO Enterprise", page_icon="🔐", layout="wide")

# CSS
st.markdown(\"\"\"
<style>
    .stChatInput { position: fixed; bottom: 0; padding-bottom: 20px; z-index: 100; }
    .block-container { padding-bottom: 120px; }
</style>
\"\"\", unsafe_allow_html=True)

# --- AUTHENTICATION ---
if "api_key" not in st.session_state: st.session_state.api_key = None

if not st.session_state.api_key:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 MISO Enterprise Login")
        with st.form("login_form"):
            key_input = st.text_input("API Key", type="password")
            if st.form_submit_button("Authenticate"):
                st.session_state.api_key = key_input
                st.rerun()
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.api_key}"}

# --- SIDEBAR (VISUAL INPUT) ---
with st.sidebar:
    st.title("🏢 MISO Hypervisor")

    st.divider()
    st.write("### 📸 Visual Input")
    uploaded_file = st.file_uploader("Analyze Image", type=["png", "jpg", "jpeg"])

    image_b64 = None
    if uploaded_file:
        st.image(uploaded_file, caption="Target Acquired", width=200)
        image_bytes = uploaded_file.getvalue()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    st.divider()
    if st.button("Logout"):
        st.session_state.api_key = None
        st.rerun()

# --- CHAT ---
st.header("Enterprise Intelligence Platform")

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image_data"):
            st.image(base64.b64decode(msg["image_data"]), width=300)
        st.markdown(msg["content"])

if prompt := st.chat_input("Direct command to Hypervisor..."):
    user_msg = {"role": "user", "content": prompt}
    if image_b64:
        user_msg["image_data"] = image_b64
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        if image_b64: st.image(uploaded_file, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ Processing Visual Data..." if image_b64 else "⚡ Thinking...")

        try:
            payload = {"prompt": prompt}
            if image_b64:
                payload["image"] = image_b64

            # Call the API
            res = requests.post(f"{MISO_API}/process", json=payload, headers=headers)

            if res.status_code == 200:
                # FIX: Handle Nested JSON Response
                body = res.json()
                data_block = body.get("data", {})
                
                # Get Answer (Backend sends 'answer', fallback to 'response')
                content = data_block.get("answer", data_block.get("response", "No content received"))

                # Get Ledger (Nested in data_block)
                if "audit_ledger" in data_block:
                    ledger = data_block["audit_ledger"]
                    # Calculate cost string
                    cost_val = ledger.get('cost')
                    if isinstance(cost_val, (float, int)):
                        cost_str = f"${cost_val:.6f}"
                    else:
                        cost_str = str(cost_val)
                        
                    content += f"\\n\\n*Provider: {ledger.get('provider')} | Cost: {cost_str}*"

                placeholder.markdown(content)
                st.session_state.messages.append({"role": "assistant", "content": content})
            else:
                placeholder.error(f"Error {res.status_code}: {res.text}")

        except Exception as e:
            placeholder.error(f"Connection Failure: {e}")
"""

with open("dashboard.py", "w") as f:
    f.write(code)

print("✅ dashboard.py has been completely rewritten.")
