import streamlit as st
import os

st.set_page_config(page_title="MISO COMMAND", layout="wide")

# --- CLEAN UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .sidebar .sidebar-content { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- CENTRAL COMMAND NAVIGATION ---
st.sidebar.title("🏛️ MISO COMMAND")
module = st.sidebar.selectbox("SELECT MODULE", ["Central Command", "M365 Governance", "System Vitals"])

# --- 1. CENTRAL COMMAND (THE HUB) ---
if module == "Central Command":
    st.title("🏛️ MISO CENTRAL COMMAND")
    st.markdown("---")
    st.write("### All legacy UI has been purged.")
    st.info("System is ready for incremental feature deployment.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("UI STATUS", "STERILE")
    with col2:
        st.metric("ROADMAP", "READY")

# --- 2. M365 GOVERNANCE (THE ROADMAP FEATURE) ---
elif module == "M365 Governance":
    st.title("🛡️ M365 GOVERNANCE")
    st.caption("Focus: Intelligent Justification MVP")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("🤖 Live Interrogator Feed")
        st.table([{"Status": "Waiting for Signal", "Context": "Clean Slate"}])
    with col2:
        st.subheader("📋 MVP Milestones")
        st.checkbox("API Hook (Milestone 1)", value=False)
        st.checkbox("Persona Generator (Milestone 1)", value=False)

# --- 3. SYSTEM VITALS (THE CNS) ---
elif module == "System Vitals":
    st.title("🧬 SYSTEM VITALS")
    st.write("Real-time telemetry from Proprioception Agent.")
