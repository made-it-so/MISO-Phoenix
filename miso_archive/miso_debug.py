from pypdf import PdfReader
import os

target = r'C:\MISO_RESEARCH\01_Core_Axioms\Ahrlund-Richter et al Neuron 2026.pdf'

def check_visibility():
    if not os.path.exists(target):
        print(f"[-] FILE NOT FOUND: {target}")
        return

    try:
        reader = PdfReader(target)
        text = reader.pages[0].extract_text()
        if text:
            print("[+] EXTRACTION SUCCESS!")
            print(f"--- PREVIEW ---\n{text[:500]}\n---------------")
        else:
            print("[!] EXTRACTION FAILED: Page returned empty string.")
    except Exception as e:
        print(f"[X] CRITICAL ERROR: {e}")

if __name__ == '__main__':
    check_visibility()
