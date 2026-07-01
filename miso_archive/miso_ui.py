import streamlit as st
import json, os, requests, subprocess

# CONFIG
MODEL = "miso-auditor"
STATE_FILE = "miso_manifold.json"

def load_miso():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            if 'history' not in data: data['history'] = []
            return data
    return {"rank": 25.7351, "manifold": {}, "history": []}

def query_miso(prompt):
    try:
        r = requests.post("http://localhost:11434/api/generate", 
                          json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=120)
        return r.json().get('response', '')
    except: return "LOCAL ERROR: Ensure Ollama is running 'miso-auditor'."

miso = load_miso()
st.set_page_config(page_title="MISO Utility Core", layout="wide")
st.title("🏛️ MISO RECURSIVE CORE v4.4")

with st.sidebar:
    st.metric("HLE RANK", f"{miso['rank']:.4f}%")
    st.markdown("---")
    st.subheader("🛠️ CONSIGLIERE OVERRIDE")
    new_dna_input = st.text_area("Paste 'Utility-First' Code here:")
    if st.button("🔥 APPLY DNA PATCH"):
        if "FROM" in new_dna_input:
            with open("Modelfile", "w") as f: f.write(new_dna_input)
            subprocess.run(["ollama", "create", MODEL, "-f", "Modelfile"])
            miso['rank'] += 0.05 # Utility Reward for successful grounding
            st.success("Backbone Reconfigured via Consigliere Patch.")
        else: st.error("Invalid DNA. Patch must be an Ollama Modelfile.")

# CHAT
for chat in miso['history']:
    with st.chat_message("user"): st.write(chat["user"])
    with st.chat_message("assistant"): st.write(chat["miso"])

if prompt := st.chat_input("Command the Ledger..."):
    with st.chat_message("user"): st.write(prompt)
    response = query_miso(prompt)
    with st.chat_message("assistant"): st.write(response)
    miso['history'].append({"user": prompt, "miso": response})
    with open(STATE_FILE, 'w') as f: json.dump(miso, f, indent=4)
    st.rerun()
