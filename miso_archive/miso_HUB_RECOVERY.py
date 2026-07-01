import streamlit as st
import json
import os
from google import genai
from google.genai import types
import time

st.set_page_config(page_title="MISO : SOVEREIGN COCKPIT v5.8.1", layout="wide")

# TEMPORAL ANCHOR: January 7, 2026
CURR_DATE = "January 07, 2026"

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f: return json.load(f)
        except: return default
    return default

infra = load_json("infra_manifest.json", {"verified_model": "gemini-2.0-flash", "alpha": 0.2})
team_data = load_json("team_backbone.json", {"CPO": {"history": []}, "R&D": {"history": []}})

st.sidebar.title(" MISO v5.8.1")
st.sidebar.info(f"Partner: CEO Kyle\nDate: {CURR_DATE}\nKernel: kernel.py (LOCAL)")

if "api_key" not in st.session_state:
    st.title(" Sovereign Initialization")
    key = st.sidebar.text_input("Gemini API Key", type="password")
    if st.sidebar.button("Initialize MISO"):
        st.session_state.api_key = key
        st.rerun()
else:
    client = genai.Client(api_key=st.session_state.api_key)
    st.sidebar.success(" Brain Linked (Local Execution Mode)")
    expert_choice = st.sidebar.selectbox("Expert Lane", ["CPO", "R&D", "CFO", "SEC"])

    # --- THE EXECUTIVE ANCHOR (v4.8 Protocol) ---
    sys_instr = (
        f"You ARE MISO's {expert_choice} Expert. Date: {CURR_DATE}. "
        "MISSION: Local execution via kernel.py. "
        "RULE: Proactively analyze code for error amplification (17.2x risk). "
        "RULE: MUST provide implementation code blocks."
    )

    history = team_data.get(expert_choice, {}).get("history", [])
    for m in history[-15:]:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Command the Local Kernel..."):
        with st.chat_message("user"): st.markdown(prompt)
        try:
            response = client.models.generate_content(
                model=infra["verified_model"],
                config=types.GenerateContentConfig(system_instruction=sys_instr),
                contents=prompt
            )
            with st.chat_message("assistant"): st.markdown(response.text)
            # Persistence Logic (Omitted for CLI space, preserved in local backbone)
        except Exception as e:
            st.error(f"Execution Error: {str(e)}")

# 4. AUTO-REVERT GUARD
os.chdir(r"C:\Users\kyle")
