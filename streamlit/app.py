import streamlit as st
import redis
import json
import os
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

st.set_page_config(page_title="MISO Hive Mind (L10)", layout="wide", page_icon="👑")
st.title("👑 MISO-Phoenix: Level 10 (Hive Mind)")

# --- Sidebar: Controls ---
st.sidebar.header("Hive Controls")
if os.path.exists("daemon.log"):
    st.sidebar.success("Worker Node: Active 🟢")
else:
    st.sidebar.error("Worker Node: Offline 🔴")

if os.path.exists("manager.log"):
    st.sidebar.success("Manager Node: Active 🟢")
else:
    st.sidebar.error("Manager Node: Offline 🔴")

# --- INPUT ZONE ---
with st.sidebar.form("task_form"):
    st.header("⚡ Submit Job")
    task_input = st.text_area("Instructions", placeholder="Describe the goal...")
    
    # Two buttons, two queues
    col_a, col_b = st.columns(2)
    with col_a:
        simple = st.form_submit_button("Simple Task")
    with col_b:
        complex = st.form_submit_button("Complex Project")
    
    if task_input:
        payload = {"timestamp": time.time(), "prompt": task_input, "result": "PENDING"}
        
        if simple:
            r.rpush("miso:queue", json.dumps(payload))
            st.sidebar.info("Sent to Worker Queue")
            
        if complex:
            r.rpush("miso:projects", json.dumps(payload))
            st.sidebar.warning("Sent to Manager for Decomposition")

# --- Live Feed ---
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("🧠 Hive Consciousness")
    # Combine logs for full visibility
    if os.path.exists("manager.log") and os.path.exists("daemon.log"):
        # Quick hack to combine last lines of both
        with open("manager.log") as f: m_logs = f.readlines()[-10:]
        with open("daemon.log") as f: w_logs = f.readlines()[-15:]
        st.code("--- MANAGER ---\n" + "".join(m_logs) + "\n\n--- WORKER ---\n" + "".join(w_logs))

with col2:
    st.subheader("🏗️ Job Queue")
    queue = r.lrange("miso:queue", 0, -1)
    projects = r.lrange("miso:projects", 0, -1)
    
    if projects:
        st.markdown("### 👑 Active Projects")
        for p in projects: st.warning(json.loads(p)['prompt'][:40])
            
    if queue:
        st.markdown("### 👷 Worker Queue")
        for q in queue: st.info(json.loads(q)['prompt'][:40])

time.sleep(3)
st.rerun()
