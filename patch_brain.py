import os

# Configuration
TARGET_FILE = "brain_functions.py"
FUNCTION_NAME = "execute_with_arbitrage"
NEW_SIGNATURE = "async def execute_with_arbitrage(prompt, image=None):"

def patch_brain_function():
    print(f"🔍 Looking for {TARGET_FILE}...")
    
    if not os.path.exists(TARGET_FILE):
        print(f"❌ Error: File {TARGET_FILE} not found in current directory.")
        return

    with open(TARGET_FILE, "r") as f:
        lines = f.readlines()

    new_lines = []
    found = False

    for line in lines:
        # We look for 'def function_name' to ensure we find the definition
        # We ignore what comes after 'def name' so current args don't matter
        if f"def {FUNCTION_NAME}" in line:
            
            # 1. Capture the existing indentation (spaces or tabs)
            indentation = line[:len(line) - len(line.lstrip())]
            
            # 2. Construct the new line using original indentation + new signature
            new_line = f"{indentation}{NEW_SIGNATURE}\n"
            
            new_lines.append(new_line)
            found = True
            print(f"✅ Found match.\n   Old: {line.strip()}\n   New: {new_line.strip()}")
        else:
            new_lines.append(line)

    if found:
        with open(TARGET_FILE, "w") as f:
            f.writelines(new_lines)
        print(f"🚀 Success! {TARGET_FILE} has been patched.")
    else:
        print(f"⚠️ Warning: Could not find 'def {FUNCTION_NAME}' in file.")

if __name__ == "__main__":
    patch_brain_function()
