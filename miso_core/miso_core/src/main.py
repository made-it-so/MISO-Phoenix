from src.backbone.router import ReflexRouter
from src.backbone import tools

# Initialize the Kernel
router = ReflexRouter()

# Register "Preconfigured Sequences" (Hard-coded routes)
router.register(r"calculate|sum|average", tools.calculator)
router.register(r"fetch|status|log", tools.system_status)

# Test the Reflex Arc
test_prompts = [
    "Calculate the sum of the last invoice",
    "Fetch system logs for today",
    "Write a poem about AI"  # Should fail backbone and go to cortex
]

print("--- MISO KERNEL BOOT ---")
for p in test_prompts:
    decision = router.route(p)
    print(f"Prompt: '{p}' -> Decision: {decision}")
