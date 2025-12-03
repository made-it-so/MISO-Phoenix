import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import json
import base64

MISO_API = "http://localhost:8000"
st.set_page_config(page_title="MISO V87", page_icon="👁️", layout="wide")

st.sidebar.title("👁️ MISO V87")
try:
    stats = requests.get(f"{MISO_API}/system/stats", timeout=1).json()
    st.sidebar.success("System: ONLINE")
    weights = stats.get("active_weights", {})
    if weights:
        df = pd.DataFrame(list(weights.items()), columns=["Model", "Weight"])
        fig = px.pie(df, values="Weight", names="Model", hole=0.4)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200, showlegend=False)
        st.sidebar.plotly_chart(fig, use_container_width=True)
except:
    st.sidebar.error("System: OFFLINE")

st.title("Multimodal Interface")

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(base64.b64decode(msg["image"]), width=300)
        st.markdown(msg["content"])

# FILE UPLOADER
uploaded_file = st.sidebar.file_uploader("Upload Image for Analysis", type=["png", "jpg", "jpeg"])
image_b64 = None
if uploaded_file:
    image_bytes = uploaded_file.getvalue()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    st.sidebar.image(uploaded_file, caption="Visual Input Loaded", width=200)

if prompt := st.chat_input("Input..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ Processing...")
        
        try:
            payload = {"type": "chat", "payload": prompt}
            if image_b64:
                payload["image_data"] = image_b64
                placeholder.markdown("👁️ **Visual Cortex Active...**")
            elif prompt.startswith("/run "):
                payload = {"type": "execute_code", "payload": prompt.replace("/run ", "")}
            elif prompt.startswith("/research "):
                payload = {"type": "research", "payload": prompt.replace("/research ", "")}

            res = requests.post(f"{MISO_API}/process", json=payload).json()
            
            # (Polling logic omitted for brevity in this patch, focus is on vision)
            # For Swarm tasks, use previous dashboard version logic or combine.
            # This version focuses on Sync Chat + Vision.
            
            data = res.get("data", {})
            if "response" in data:
                content = data["response"]
                if "cost" in data: content += f"\n\n*Cost: {data['cost']}*"
            elif "output" in data:
                content = f"```\n{data['output']}\n```"
            else:
                content = str(data)

            placeholder.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})

        except Exception as e:
            placeholder.error(f"Synapse Failure: {e}")
