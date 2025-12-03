import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import json

MISO_API = "http://localhost:8000"
st.set_page_config(page_title="MISO V83", page_icon="🐝", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("🐝 MISO V83")
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

# --- MAIN CHAT ---
st.title("Hive Mind Interface")

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Command the Swarm..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ Dispatching...")
        
        try:
            # 1. PARSE & DISPATCH
            payload = {"type": "chat", "payload": prompt}
            if prompt.startswith("/run "):
                payload = {"type": "execute_code", "payload": prompt.replace("/run ", "")}
            elif prompt.startswith("/research "):
                payload = {"type": "research", "payload": prompt.replace("/research ", "")}

            res = requests.post(f"{MISO_API}/process", json=payload).json()
            
            # Extract inner data
            data = res.get("data", {})
            
            # 2. HANDLE ASYNC SWARM TASKS (THE FIX: Check inner data status)
            if data.get("status") == "queued":
                task_id = data.get("task_id")
                placeholder.markdown(f"🐝 **Swarm Deployed.** Task ID: `{task_id}`\n\n*Waiting for drone return...*")
                
                # POLLING LOOP
                final_result = None
                for _ in range(30): # Wait up to 60 seconds
                    time.sleep(2)
                    try:
                        poll_res = requests.post(f"{MISO_API}/process", json={
                            "type": "check_task", 
                            "payload": task_id
                        }).json()
                        
                        poll_data = poll_res.get("data", {})
                        if poll_data.get("status") == "complete":
                            final_result = poll_data.get("result")
                            break
                    except: pass
                
                if final_result:
                    data = final_result
                else:
                    data = {"error": "Task Timeout - Drone lost communication."}
            
            # 3. RENDER OUTPUT
            if isinstance(data, dict):
                if "insight" in data:
                    content = f"**📚 Hive Knowledge:**\n\n{data['insight']}\n\n**Sources:**"
                    for p in data.get("papers", []):
                        content += f"\n- [{p['title']}]({p['url']})"
                elif "output" in data:
                    content = f"**⚙️ Backbone Action:**\n```\n{data['output']}\n```"
                elif "response" in data:
                    content = data["response"]
                elif "error" in data:
                    content = f"❌ **Error:** {data['error']}"
                else:
                    content = json.dumps(data, indent=2)
            else:
                content = str(data)

            placeholder.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})

        except Exception as e:
            placeholder.error(f"Synapse Failure: {e}")
