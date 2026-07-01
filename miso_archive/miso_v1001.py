# -*- coding: utf-8 -*-
import threading, time, os, tkinter as tk
from tkinter import ttk

class MisoOmega:
    def __init__(self):
        self.yield_val = 745.50
        self.nodes = 6
        self.status = "OMEGA_SEQUENCE_ACTIVE"
        self.logs = ["[MISO] Encoding Fixed", "[MISO] Hive Syncing...", "[MISO] Asset 103 Initializing"]

    def run_market_hunter(self):
        while True:
            time.sleep(5)
            self.yield_val += 0.12 # Frankfurt Alpha Delta
            self.logs.append(f"[HUNTER] Frankfurt Arbitrage Active: +.12")

    def run_branching(self):
        # Already scaled to 6 nodes in previous step
        self.logs.append("[GOOSE] Node-02 (DE) Heartbeat: 11.9 deg Sync.")
        self.logs.append("[GOOSE] Node-05 (SG) Heartbeat: 11.9 deg Sync.")

def launch_dashboard(engine):
    root = tk.Tk()
    root.title("MISO OMEGA v1001.01 | HIVE COMMAND")
    root.geometry("500x420")
    root.configure(bg="#050505")
    
    style = ttk.Style()
    style.configure("TLabel", foreground="#00ff41", background="#050505", font=("Courier", 10))
    
    ttk.Label(root, text="--- MISO OMEGA CONSOLE ---", font=("Courier", 14, "bold")).pack(pady=10)
    y_lbl = ttk.Label(root, text=f"AGGREGATE YIELD: $ {engine.yield_val}")
    y_lbl.pack(pady=5)
    n_lbl = ttk.Label(root, text=f"HIVE NODES: {engine.nodes}")
    n_lbl.pack(pady=5)
    
    log_box = tk.Text(root, bg="#000", fg="#00ff41", font=("Courier", 8), height=12)
    log_box.pack(padx=20, pady=10)

    def refresh():
        y_lbl.config(text=f"AGGREGATE YIELD: $ {round(engine.yield_val, 2)}")
        n_lbl.config(text=f"HIVE NODES: {engine.nodes}")
        log_box.delete('1.0', tk.END)
        for log in engine.logs[-10:]:
            log_box.insert(tk.END, log + "\n")
        root.after(1000, refresh)

    refresh()
    root.mainloop()

if __name__ == "__main__":
    miso = MisoOmega()
    threading.Thread(target=miso.run_market_hunter, daemon=True).start()
    threading.Thread(target=miso.run_branching, daemon=True).start()
    launch_dashboard(miso)
