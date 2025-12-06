import os

def read_dna():
    path = "miso_project/config/genesis_prompt.md"
    if os.path.exists(path):
        with open(path, "r") as f:
            print("\n" + "="*40)
            print(f.read())
            print("="*40 + "\n")
    else:
        print("CRITICAL: DNA Corrupted (File missing).")

if __name__ == "__main__":
    read_dna()
