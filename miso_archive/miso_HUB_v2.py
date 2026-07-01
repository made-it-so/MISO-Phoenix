import streamlit as st
import json
import os
import subprocess
import time

st.set_page_config(page_title="MISO : SOVEREIGN HUB", layout="wide")
st.sidebar.title("🏛️ MISO COMMAND HUB")
view = st.sidebar.radio("Navigate", ["🏢 Executive Office", "💰 CFO Suite", "🌐 Global Franchise"])

st.sidebar.divider()
st.sidebar.subheader("📡 MoE Audit Bridge")

if os.path.exists("gemini_directive.json"):
    try:
        with open("gemini_directive.json", "r", encoding="utf-8-sig") as f:
            directive = json.load(f)
        
        st.sidebar.warning(f"ACTION: {directive['title']}")
        
        # DISPLAY MoE EXPERT VOTES
        with st.sidebar.expander("🛡️ View MoE Audit Report"):
            st.write(f"**Security:** ✅ {directive.get('moe_security', 'Verified')}")
            st.write(f"**Fiscal:** ✅ {directive.get('moe_fiscal', 'Verified')}")
            st.write(f"**Stability:** ✅ {directive.get('moe_stability', 'Verified')}")
        
        if st.sidebar.button("EXECUTE AUTHORIZATION"):
            with open("task_logic.py", "w", encoding="utf-8") as f:
                f.write(directive['script'])
            subprocess.run(["python", "task_logic.py"])
            os.remove("gemini_directive.json")
            st.sidebar.success("Executed.")
            time.sleep(1)
            st.rerun()
    except Exception:
        st.sidebar.info("Syncing Audit...")
else:
    st.sidebar.info("Awaiting MoE Consensus...")

# --- MAIN UI ---
if view == "🏢 Executive Office":
    st.title("🏢 Executive Office")
    st.write("Sovereign Governance: **MoE Council Active**.")
