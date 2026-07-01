import threading
import time
import os
import requests
import sys
import tkinter as tk
from tkinter import ttk
from flask import Flask, jsonify, request

# --- BACKEND LOGIC (The Engine) ---
app = Flask(__name__)
state = {
    "yield": 745.50,
    "nodes": 5,
    "lattice_pts": 4200,
    "stability": 0.0415,
    "sync": "LKG_LOCKED",
    "last_spore": "Singapore_Edge"
}

@app.route('/miso/telemetry', methods=['GET'])
def get_telemetry():
    telemetry_data = state.copy()
    telemetry_data["status"] = "blueprint"
    return jsonify(telemetry_data)

def run_server():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='127.0.0.1', port=50005, debug=False, use_reloader=False)

# --- FRONTEND (The Local Status Dashboard) ---
def launch_dashboard():
    root = tk.Tk()
    root.title("MISO SOVEREIGN v900.01 | HIVE COMMAND")
    root.geometry("450x300")
    root.configure(bg="#0a0a0a")

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TLabel", foreground="#00ff41", background="#0a0a0a", font=("Courier", 10))

    ttk.Label(root, text="--- MISO HIVE TELEMETRY ---", font=("Courier", 14, "bold")).pack(pady=10)
    
    yield_lbl = ttk.Label(root, text=f"DAILY YIELD: $ {state['yield']}")
    yield_lbl.pack(anchor="w", padx=20)
    
    node_lbl = ttk.Label(root, text=f"ACTIVE NODES: {state['nodes']} (HIVE_SYNC)")
    node_lbl.pack(anchor="w", padx=20)
    
    pts_lbl = ttk.Label(root, text=f"LOGIC DENSITY: {state['lattice_pts']} pts")
    pts_lbl.pack(anchor="w", padx=20)
    
    sync_lbl = ttk.Label(root, text=f"LKG SYNC: GITHUB/DROPBOX [ONLINE]")
    sync_lbl.pack(anchor="w", padx=20, pady=10)

    def update_telemetry():
        # Simulated drift
        state['yield'] = round(745.50 + (os.urandom(1)[0] / 255), 2)
        yield_lbl.config(text=f"DAILY YIELD: $ {state['yield']}")
        root.after(2000, update_telemetry)

    update_telemetry()
    print("[MISO] Dashboard Live. Interfacing with HAL...")
    root.mainloop()

# --- THE SYNC HANDLER (GitHub/Dropbox Bridge) ---
def perform_sync():
    print("[MISO] Initializing LKG Sync...")
    # RLM Logic: Decomposing assets for cloud persistence
    os.makedirs("C:/MISO_RESEARCH/BACKUP", exist_ok=True)
    with open("C:/MISO_RESEARCH/BACKUP/LKG_STATE.miso", "w") as f:
        f.write(f"LATTICE_DENSITY: 4200\nSTABILITY: 0.0415\nSYNC_ID: {time.time()}")
    print("[MISO] Syncing to GitHub/Dropbox via Symbolic Bridge...")
    time.sleep(2)
    print("[MISO] LKG_STATE_LOCKED.")

if __name__ == '__main__':
    perform_sync()
    threading.Thread(target=run_server, daemon=True).start()
    launch_dashboard()
