import os

ARCHITECT_PATH = "miso-worker/app/architect.py"
ROUTING_LOGIC = """
            # GLADIATOR ROUTING
            if "CRITICAL" in task.get("payload", ""):
                from src.modules.gan.gladiator import GladiatorArena
                result = GladiatorArena().fight(prompt)
                self.post_to_chat("assistant", result)
                return
"""

try:
    with open(ARCHITECT_PATH, "r") as f:
        content = f.read()

    TARGET_MARKER = 'if task.get("type") == "CHAT_COMMAND":'
    
    if "GladiatorArena" in content:
        print("⚠️ Architect already wired.")
    elif TARGET_MARKER in content:
        # Insert routing logic BEFORE the chat command check
        new_content = content.replace(TARGET_MARKER, ROUTING_LOGIC + "            " + TARGET_MARKER)
        with open(ARCHITECT_PATH, "w") as f:
            f.write(new_content)
        print("✅ SUCCESS: Architect wired to Gladiator Arena.")
    else:
        print("❌ ERROR: Could not find injection point in architect.py")
        exit(1)

except FileNotFoundError:
    print(f"❌ ERROR: Could not find {ARCHITECT_PATH}")
    exit(1)
