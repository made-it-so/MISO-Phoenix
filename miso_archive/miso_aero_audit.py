import json
import os

MANIFOLD_PATH = "miso_manifold.json"

def aero_meta_audit():
    print("[+] INITIATING AERO DUAL-LOOP FEEDBACK...")
    
    with open(MANIFOLD_PATH, 'r') as f:
        data = json.load(f)

    print(f"[*] ANALYIZING ENDOGENOUS LOGIC (Rank: {data['rank']}%)")
    
    # Loop 2: Evolutionary Pressure Check
    axioms = data.get('axioms', [])
    keyword_freq = {}
    
    for ax in axioms:
        text = ax.get('axiom', '').lower()
        for word in ["feedback", "distillation", "verification", "calibration"]:
            if word in text:
                keyword_freq[word] = keyword_freq.get(word, 0) + 1

    print("\n[>] LOGIC DENSITY REPORT:")
    for word, count in keyword_freq.items():
        density = (count / len(axioms)) * 100 if axioms else 0
        print(f"    - {word.upper()}: {density:.1f}% Coverage")

    # The AERO Verdict: Is the logic too lopsided?
    if any(d > 80 for d in keyword_freq.values()):
        print("\n[!] AERO WARNING: Logic Over-Saturation Detected (Loop Drift).")
        print("    Recommendation: Seek out 'Calibration' bones to balance 'Feedback' bias.")
    else:
        print("\n[!] AERO VERDICT: Structural Balance Maintained.")
        # Meta-increase rank for self-awareness
        data['rank'] += 0.0475
        data['rank'] = round(data['rank'], 4)

    with open(MANIFOLD_PATH, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"\n[!] META-RANK UPDATED: {data['rank']}%")

if __name__ == '__main__':
    aero_meta_audit()
