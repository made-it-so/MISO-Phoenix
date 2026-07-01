import json
import os

def review_manifold():
    FILE = "miso_manifold.json"
    if not os.path.exists(FILE):
        print("[-] MANIFOLD EMPTY. Feed the Atomizer.")
        return

    with open(FILE, 'r') as f:
        data = json.load(f)

    rank = data.get('rank', 0.0)
    ingested = data.get('ingested_data', [])
    
    signals = [i for i in ingested if i['verdict'] == 'SIGNAL' or i['verdict'] == 'ALIVE']
    noise = [i for i in ingested if i['verdict'] == 'NOISE' or i['verdict'] == 'DEAD']

    print(f"\n--- MISO MANIFOLD STATUS [RANK: {rank}%] ---")
    print(f"[+] TOTAL BONES FOUND: {len(signals)}")
    print(f"[-] TOTAL ENTROPY PURGED: {len(noise)}")
    print("-" * 40)

    if signals:
        print("CURRENT RIGID SIGNALS:")
        for s in signals:
            print(f" > {s['file']} (VERDICT: {s['verdict']})")
    else:
        print("[!] NO SIGNAL DETECTED. The substrate is still digging.")

if __name__ == '__main__':
    review_manifold()
