import customtkinter as ctk
import requests
import threading
import time

API_URL = "http://127.0.0.1:8000"

class MisoClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MISO ARCHITECTURAL FORGE :: CLIENT INTERFACE")
        self.geometry("1000x600")
        ctk.set_appearance_mode("dark")

        # Top Pulse Bar
        self.status_label = ctk.CTkLabel(self, text="STATUS: INITIALIZING...", text_color="red", font=("Courier", 14, "bold"))
        self.status_label.pack(pady=10)

        # Main Layout Frames
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Chat Window
        self.chat_display = ctk.CTkTextbox(self.main_frame, width=700, font=("Courier", 13))
        self.chat_display.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.chat_display.insert("0.0", "> MISO CLIENT v1.1 INITIALIZED.\n> AWAITING COMMANDS AT THE TRANSPARENT ORACLE...\n\n")
        self.chat_display.configure(state="disabled")

        # Mutation Triage
        self.mutation_list = ctk.CTkTextbox(self.main_frame, width=250, font=("Courier", 12))
        self.mutation_list.pack(side="right", fill="y")
        
        # Input Field
        self.input_entry = ctk.CTkEntry(self, height=40, font=("Courier", 14))
        self.input_entry.pack(fill="x", padx=20, pady=20)
        self.input_entry.bind("<Return>", self.send_message)

        # Autonomic Background Threads
        threading.Thread(target=self.poll_pulse, daemon=True).start()
        threading.Thread(target=self.poll_mutations, daemon=True).start()

    def _write_chat(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text)
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def send_message(self, event):
        text = self.input_entry.get().strip()
        if not text: return
        self.input_entry.delete(0, 'end')
        self._write_chat(f"\n[YOU] {text}\n")
        threading.Thread(target=self.post_chat, args=(text,), daemon=True).start()

    def post_chat(self, text):
        try:
            # Fixed the 422 JSON validation error
            res = requests.post(f"{API_URL}/chat", json={"message": text})
            res.raise_for_status()
            reply = res.json().get("response", "")
            self.after(0, lambda: self._write_chat(f"[MISO] {reply}\n\n"))
        except Exception as e:
            # Fixed the Tkinter threading TypeError
            self.after(0, lambda e=e: self._write_chat(f"[!] SYNAPTIC ERROR: {e}\n\n"))

    def poll_pulse(self):
        while True:
            try:
                res = requests.get(f"{API_URL}/pulse")
                status = res.json().get("status", "ONLINE")
                self.after(0, lambda s=status: self.status_label.configure(text=f"STATUS: {s.upper()}", text_color="#00FF00"))
            except:
                self.after(0, lambda: self.status_label.configure(text="STATUS: SYSTEM OFFLINE", text_color="red"))
            time.sleep(5)

    def poll_mutations(self):
        while True:
            try:
                res = requests.get(f"{API_URL}/mutations/pending")
                muts = res.json().get("mutations", [])
                self.after(0, lambda m=muts: self._update_mutations(m))
            except:
                pass
            time.sleep(5)

    def _update_mutations(self, mutations):
        self.mutation_list.configure(state="normal")
        self.mutation_list.delete("0.0", "end")
        self.mutation_list.insert("end", "--- MUTATION TRIAGE ---\n\n")
        for m in mutations:
            filename = m.split('/')[-1] if '/' in m else m.split('\\')[-1]
            self.mutation_list.insert("end", f"> {filename}\n")
        self.mutation_list.configure(state="disabled")

if __name__ == "__main__":
    app = MisoClient()
    app.mainloop()