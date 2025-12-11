import os

ARCHITECT_PATH = "miso-worker/app/architect.py"
# We define the new logic with 8-space indentation to match the target file
ROUTING_LOGIC = """
        # GLADIATOR ROUTING
        if "CRITICAL" in task.get("payload", ""):
            from src.modules.gan.gladiator import GladiatorArena
            result = GladiatorArena().fight(prompt)
            print(f" >> GLADIATOR RESULT: {result}")
            return
"""

try:
    with open(ARCHITECT_PATH, "r") as f:
        content = f.read()

    # The new target marker that actually exists in your file
    TARGET_MARKER = 'task_id = task.get("id", "unknown")'

    if "GladiatorArena" in content:
        print("⚠️ Architect already wired.")
    elif TARGET_MARKER in content:
        # Insert routing logic BEFORE the task_id line
        # We add a newline and 8 spaces to ensure the marker stays correctly indented
        new_content = content.replace(TARGET_MARKER, ROUTING_LOGIC + "\n        " + TARGET_MARKER)
        with open(ARCHITECT_PATH, "w") as f:
            f.write(new_content)
        print("✅ SUCCESS: Architect wired to Gladiator Arena.")
    else:
        print("❌ ERROR: Could not find injection point in architect.py")
        exit(1)

except FileNotFoundError:
    print(f"❌ ERROR: Could not find {ARCHITECT_PATH}")
    exit(1)
