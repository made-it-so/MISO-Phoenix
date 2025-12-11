import sys
import os

file_path = "brain_functions.py"

print(f"Opening {file_path}...")
with open(file_path, "r") as f:
    lines = f.readlines()

new_lines = []
signature_fixed = False

for line in lines:
    # We ignore whitespace, async keywords, or type hints. 
    # If the function name is on the line, we REPLACE the whole line.
    if "def execute_with_arbitrage" in line:
        print(f"FOUND BAD LINE: {line.strip()}")
        new_lines.append("async def execute_with_arbitrage(prompt, image=None):\n")
        print("REPLACED WITH:  async def execute_with_arbitrage(prompt, image=None):")
        signature_fixed = True
    else:
        new_lines.append(line)

if not signature_fixed:
    print("CRITICAL ERROR: Could not find function definition in file. Please check file content manually.")
    sys.exit(1)

with open(file_path, "w") as f:
    f.writelines(new_lines)

print("\nSUCCESS: Function signature forced to accept images.")
