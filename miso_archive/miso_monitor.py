import os, time, json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyPDF2 import PdfReader

# CONFIGURATION
MONITOR_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
INPUT_LOG = r"C:\MISO_RESEARCH\SOVEREIGN_INPUT.txt"
STATE_FILE = "miso_manifold.json"

class RecursiveAtomizer(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.pdf'):
            self.atomize(event.src_path)

    def atomize(self, file_path):
        print(f"[*] DETECTED: {os.path.basename(file_path)}")
        try:
            # 1. v1301.119 Recursive-Atomizer (Extraction)
            reader = PdfReader(file_path)
            text = "".join([p.extract_text() for p in reader.pages])
            
            # 2. Append OMEGA DIRECTIVE v1301.119
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            directive = (
                f"\n--- OMEGA DIRECTIVE v1301.119 | {timestamp} ---\n"
                f"SOURCE: {os.path.basename(file_path)}\n"
                f"ATOMIZED_CONTENT: {text[:2000]}...\n"
                f"COMMAND: Conduct Adversarial Audit against Lognormal Backbone. "
                f"Identify Poisson Noise vs. Irreversible logic. [VERDICT REQUIRED]\n"
            )
            
            with open(INPUT_LOG, "a", encoding="utf-8") as f:
                f.write(directive)
            
            print(f"[SUCCESS] Directive appended to SOVEREIGN_INPUT.txt")
        except Exception as e:
            print(f"[ERROR] Atomization failed: {e}")

if __name__ == '__main__':
    print("--- MISO MONITOR v1301.119 ACTIVE ---")
    print(f"WATCHING: {MONITOR_DIR}")
    
    observer = Observer()
    observer.schedule(RecursiveAtomizer(), MONITOR_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
