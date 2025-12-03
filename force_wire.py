import os

FILE = "miso-worker/app/architect.py"
ROUTING = """
        # GLADIATOR INTERCEPT
        if task.get("payload") and "CRITICAL" in task.get("payload"):
            try:
                from src.modules.gan.gladiator import GladiatorArena
                print(f"⚔️ ROUTING TO GLADIATOR: {task.get('id')}")
                result = GladiatorArena().fight(task.get("payload"))
                self.post_to_chat("assistant", result)
                return
            except Exception as e:
                print(f"GLADIATOR FAILURE: {e}")
"""

with open(FILE, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    # Inject immediately after the function definition
    if "def perform_task(self, task):" in line:
        new_lines.append(ROUTING)

with open(FILE, "w") as f:
    f.writelines(new_lines)

print("✅ SUCCESS: Routing forced at line 1 of perform_task.")
