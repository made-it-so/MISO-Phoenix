import streamlit as st
import uuid
import json
import os
import time
from enum import Enum

# --- Configuration & MISO-specific constants ---
MISO_HUB_VERSION = "v10.4.0"
TEAM_BACKBONE_FILE = "team_backbone.json"
ARCHIVE_DIR = "miso_archives"

# --- Laminar Logic Definitions (Interpretation of Ährlund-Richter research) ---
class LaminarPhase(Enum):
    L1 = "📝 Plan: Understanding Request"
    L2 = "🔍 Plan: Decomposing Task"
    L3 = "💡 Ingest: Gathering Info"
    L4 = "🧠 Ingest: Processing Data"
    L5 = "✨ Synthesize: Generating Response"
    L6 = "🚀 Synthesize: Formulating Action"

    def to_pill(self):
        """Returns a small markdown 'pill' for display."""
        return f"<span style='background-color:#007bff; color:white; padding:2px 6px; border-radius:12px; font-size:0.7em; margin-right:5px;'>{self.value}</span>"

# --- Security Note (CRITICAL) ---
# For demonstration purposes, 'execute_code_safely' is a mock function.
# In a production MISO system, this MUST involve:
# 1. Sandboxed execution environment (e.g., separate process, container, secure sandbox library).
# 2. Strict whitelisting of allowed functions/modules.
# 3. Input validation to prevent injection attacks.
# DO NOT use exec() or eval() with arbitrary AI-generated code in a production environment.
def mock_execute_code_safely(code_string: str, proposal_id: str):
    """
    Mocks the safe execution of a code string.
    In a real MISO system, this would trigger a sandboxed execution.
    """
    st.info(f"MISO: Proposal `{proposal_id}` approved. Simulating safe execution of code:")
    st.code(code_string, language='python')
    time.sleep(1)
    st.success("MISO: Code execution simulated successfully! (No actual code ran for security demo)")
    # Here, you'd integrate with MISO's actual execution fabric (e.g., MISO_ENGINE.execute(code_string))

# --- File System Utilities ---
def load_team_backbone():
    if not os.path.exists(TEAM_BACKBONE_FILE):
        return {"strategy_log": []}
    try:
        with open(TEAM_BACKBONE_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error(f"Error decoding {TEAM_BACKBONE_FILE}. Initializing with empty data.")
        return {"strategy_log": []}

def save_team_backbone(data):
    with open(TEAM_BACKBONE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def clear_strategy_log():
    backbone = load_team_backbone()
    backbone["strategy_log"] = []
    save_team_backbone(backbone)
    st.sidebar.success("Strategy log cleared.")

def archive_strategy_log():
    backbone = load_team_backbone()
    if not backbone["strategy_log"]:
        st.sidebar.warning("No strategy log to archive.")
        return

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    archive_filename = os.path.join(ARCHIVE_DIR, f"strategy_log_archive_{timestamp}.json")

    with open(archive_filename, 'w') as f:
        json.dump({"archived_at": timestamp, "log": backbone["strategy_log"]}, f, indent=4)

    backbone["strategy_log"] = []
    save_team_backbone(backbone)
    st.sidebar.success(f"Strategy log archived to {archive_filename}")


# --- Streamlit UI Setup ---
st.set_page_config(
    page_title=f"MISO Hub {MISO_HUB_VERSION}",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for a more "Gemini-like" feel and input anchoring
st.markdown(
    """
    <style>
    /* General body font & background */
    body {
        font-family: 'Google Sans', 'Roboto', sans-serif;
        background-color: #f0f2f5; /* Light grey background */
    }
    /* Streamlit chat message styling (simulate Gemini cards) */
    .stChatMessage {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stChatMessage.st-chat-message-user {
        background-color: #e6f3ff; /* Lighter blue for user messages */
    }

    /* Input area - try to fix it at the bottom */
    /* Note: Streamlit's native st.chat_input is already at the bottom.
             True 'fixed' positioning requires more invasive CSS or custom components,
             which can interfere with Streamlit's rendering.
             We'll rely on st.chat_input's default 'bottom' behavior for now. */
    .st-chat-input-container {
        position: sticky;
        bottom: 0;
        background-color: #f0f2f5; /* Match body background */
        padding: 10px 0;
        z-index: 1000; /* Ensure it stays above other content */
        box-shadow: 0 -2px 5px rgba(0,0,0,0.05); /* Subtle shadow above input */
    }

    /* Style for the 'thinking' spinner */
    .stSpinner {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 10px 0;
    }
    /* Status Pills */
    .status-pill-container {
        margin-top: 5px;
        font-size: 0.8em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title(f"MISO Hub {MISO_HUB_VERSION}")

# --- Sidebar for chat management ---
with st.sidebar:
    st.header("MISO Controls")
    if st.button("New Chat", key="new_chat_btn"):
        st.session_state.chat_history = []
        st.session_state.proposals = {}
        st.session_state.current_uuid_counter = 0
        clear_strategy_log() # MISO-specific log clear
        st.rerun()

    if st.button("Archive Chat", key="archive_chat_btn"):
        archive_strategy_log() # MISO-specific log archive

    st.markdown("---")
    st.write("Current Session History:")
    for i, msg in enumerate(st.session_state.get('chat_history', [])):
        role_icon = "👤" if msg['role'] == 'user' else "🤖"
        st.write(f"- {role_icon} {msg['content'][:30]}...") # Show first 30 chars


# --- Initialize Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "proposals" not in st.session_state:
    st.session_state.proposals = {} # {uuid: {'code': '...', 'description': '...', 'status': 'proposed'}}
if "current_uuid_counter" not in st.session_state:
    st.session_state.current_uuid_counter = 0

# --- Display Chat History ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"], unsafe_allow_html=True)
        if "laminar_phases" in message and message["role"] == "assistant":
            phases_html = "".join([phase.to_pill() for phase in message["laminar_phases"]])
            st.markdown(f"<div class='status-pill-container'>{phases_html}</div>", unsafe_allow_html=True)

# --- User Input & AI Response ---
# Container for the input and file uploader to provide a unified look
with st.container():
    # File uploader - positioned above the chat input
    uploaded_file = st.file_uploader("Upload a file (e.g., for context)", key="file_uploader")
    if uploaded_file is not None:
        # Process the uploaded file (e.g., read content, store in session_state)
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.uploaded_file_content = uploaded_file.read().decode("utf-8")
        st.toast(f"File '{uploaded_file.name}' uploaded and ready for analysis.")
        # Optionally, you might want to automatically add this to chat history as a system message
        # or prompt the user to ask MISO to analyze it.

    # Chat input bar
    user_input = st.chat_input("Command MISO...")

    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input, "avatar": "👤"})

        # Check for approval command
        if user_input.lower().strip() == "i approve" or user_input.lower().strip().startswith("approve"):
            latest_proposal_id = None
            if st.session_state.proposals:
                # Find the latest PROPOSED proposal by checking current_uuid_counter or iterating
                for p_id in sorted(st.session_state.proposals.keys(), reverse=True):
                    if st.session_state.proposals[p_id]['status'] == 'proposed':
                        latest_proposal_id = p_id
                        break
            
            if latest_proposal_id:
                proposal = st.session_state.proposals[latest_proposal_id]
                proposal_code = proposal['code']
                
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner(f"MISO: Executing approved proposal `{latest_proposal_id}`..."):
                        # Simulate Laminar Logic for execution phase
                        laminar_phases_exec = [LaminarPhase.L6] # Execution is a form of synthesis
                        st.markdown("".join([p.to_pill() for p in laminar_phases_exec]), unsafe_allow_html=True)
                        mock_execute_code_safely(proposal_code, latest_proposal_id)
                        
                    st.session_state.proposals[latest_proposal_id]['status'] = 'executed'
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"MISO: Approved proposal `{latest_proposal_id}` executed. Status: `executed`.",
                        "avatar": "🤖",
                        "laminar_phases": laminar_phases_exec
                    })
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.warning("MISO: No pending proposal found to approve.")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": "MISO: No pending proposal found to approve.",
                        "avatar": "🤖"
                    })
            st.rerun() # Refresh to show execution result
            
        else:
            # Simulate MISO's thinking process and response generation
            with st.chat_message("assistant", avatar="🤖"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Simulate Laminar Logic progression
                laminar_phases = []
                
                with st.spinner("MISO: Thinking (L1)..."):
                    time.sleep(0.5)
                    laminar_phases.append(LaminarPhase.L1)
                    message_placeholder.markdown(f"{LaminarPhase.L1.to_pill()}", unsafe_allow_html=True)
                
                with st.spinner("MISO: Planning (L2)..."):
                    time.sleep(0.7)
                    laminar_phases.append(LaminarPhase.L2)
                    message_placeholder.markdown(f"{''.join([p.to_pill() for p in laminar_phases])}", unsafe_allow_html=True)

                if "file_name" in st.session_state:
                    with st.spinner(f"MISO: Ingesting file '{st.session_state.uploaded_file_name}' (L3)..."):
                        time.sleep(1)
                        laminar_phases.append(LaminarPhase.L3)
                        message_placeholder.markdown(f"{''.join([p.to_pill() for p in laminar_phases])}", unsafe_allow_html=True)
                        # Here MISO would process file_content
                
                with st.spinner("MISO: Analyzing & Ingesting (L3-L4)..."):
                    time.sleep(1.5)
                    laminar_phases.extend([LaminarPhase.L3, LaminarPhase.L4])
                    message_placeholder.markdown(f"{''.join([p.to_pill() for p in laminar_phases])}", unsafe_allow_html=True)

                with st.spinner("MISO: Synthesizing (L5-L6)..."):
                    time.sleep(2)
                    laminar_phases.extend([LaminarPhase.L5, LaminarPhase.L6])
                    message_placeholder.markdown(f"{''.join([p.to_pill() for p in laminar_phases])}", unsafe_allow_html=True)

                    # MISO's actual response generation
                    response_text = f"MISO: Understood your directive: '{user_input}'. "
                    if uploaded_file is not None and "uploaded_file_name" in st.session_state:
                        response_text += f"I have processed the uploaded file '{st.session_state.uploaded_file_name}'. "

                    # Simulate a "Proposal" with code
                    st.session_state.current_uuid_counter += 1
                    proposal_uuid = f"PR-{st.session_state.current_uuid_counter}-{uuid.uuid4().hex[:4]}"
                    
                    # Example of a proposed code snippet
                    proposed_code = f"""
def analyze_data_for_{user_input.replace(" ", "_").replace("'", "").lower()}(data_context):
    # This function would perform complex analysis based on your directive.
    # For instance, if you asked to 'summarize revenue reports', this would:
    # 1. Load relevant data from data_context.
    # 2. Apply financial aggregation logic.
    # 3. Generate a summary report.
    print(f"Executing analysis for: {{data_context}} related to '{user_input}'")
    result = "Simulated analysis result: Data looks good for '{user_input}'."
    return result

# Example call if approved:
# analysis_context = {{'source': 'revenue_db', 'filters': {{'year': 2023}}}}
# print(analyze_data_for_{user_input.replace(" ", "_").replace("'", "").lower()}(analysis_context))
"""
                    response_text += f"\n\nBased on my analysis, I propose the following action plan (ID: `{proposal_uuid}`):"
                    response_text += "\n\n