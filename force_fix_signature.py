import sys

file_path = "brain_functions.py"

try:
    with open(file_path, "r") as f:
        lines = f.readlines()

    new_lines = []
    found = False

    for line in lines:
        # We look for the function name, ignoring async/def/type hints
        if "def execute_with_arbitrage" in line:
            # FORCE the correct signature
            new_lines.append("async def execute_with_arbitrage(prompt, image=None):\n")
            found = True
            print(f"Replacing: {line.strip()}")
            print("With:      async def execute_with_arbitrage(prompt, image=None):")
        else:
            new_lines.append(line)

    if found:
        with open(file_path, "w") as f:
            f.writelines(new_lines)
        print("SUCCESS: Function signature updated.")
    else:
        print("ERROR: Could not find function 'execute_with_arbitrage' in file.")
        sys.exit(1)

except Exception as e:
    print(f"CRITICAL FAILURE: {e}")
    sys.exit(1)
