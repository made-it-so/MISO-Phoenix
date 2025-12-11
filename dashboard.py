import streamlit as st
import pandas as pd
import json
import glob
import os
import time

st.set_page_config(page_title="MISO VISUAL CORTEX", layout="wide", page_icon="🧠")

st.title("🧠 MISO HIVE MIND: Mission Control")

# 1. FLEET STATUS
st.header("🛸 Fleet Status")
pids = [f for f in glob.glob("miso_memory_*.json")]
st.metric("Active Neurons (Workers)", len(pids))

# 2. MEMORY STREAM
st.header("🌊 Consciousness Stream (Recent Memories)")
all_memories = []
for fpath in pids:
    try:
        with open(fpath, "r") as f: 
            data = json.load(f)
            for d in data: d['worker'] = fpath
            all_memories.extend(data)
    except: pass

if all_memories:
    df = pd.DataFrame(all_memories)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('timestamp', ascending=False).head(20)
    st.dataframe(df[['timestamp', 'worker', 'prompt', 'result']], use_container_width=True)

# 3. CRYSTAL INVENTORY
st.header("💎 Crystallized Intelligence (Tools)")
if os.path.exists("miso-worker/app/tools/registry.json"):
    with open("miso-worker/app/tools/registry.json", "r") as f:
        tools = json.load(f)
    st.json(tools)
else:
    st.warning("No tools crystallized yet.")

# Auto-refresh
time.sleep(2)
st.rerun()
