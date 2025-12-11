import re

file_path = "brain_functions.py"

with open(file_path, "r") as f:
    lines = f.readlines()

new_lines = []
fixed = False

for line in lines:
    # Look for the function definition, ignoring arguments/async/type hints
    if "def execute_with_arbitrage" in line:
        # Force overwrite the signature line
        new_lines.append("async def execute_with_arbitrage(prompt, image=None):\n")
        fixed = True
        print(f"FIXED LINE: {line.strip()} -> async def execute_with_arbitrage(prompt, image=None):")
    else:
        new_lines.append(line)

if fixed:
    with open(file_path, "w") as f:
        f.writelines(new_lines)
    print("SUCCESS: Function signature forced to accept images.")
else:
    print("ERROR: Could not find function definition!")

