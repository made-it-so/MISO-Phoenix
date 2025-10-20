import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from miso_engine.agents import Agent
from miso_engine.planners import MisoPlanner
import json

class ExecutiveAgent:
    def __init__(self, main_goal):
        self.main_goal = main_goal
        self.architect = Agent(persona_name='ArchitectAgent')
        # This is the definitive list of what the MISO system can actually DO.
        self.available_tools = [
            "read_file(filename)",
            "write_file(filename, content)",
            "execute_shell(command)",
            "delegate_to_specialist(specialist_name, prompt)"
        ]
        print("✅ ExecutiveAgent initialized successfully.")
        print(f"   Goal: {self.main_goal}")

    def run(self):
        print("\n▶️  Delegating to Architect for an ACTIONABLE plan...")
        
        # The prompt is now grounded with the list of available tools.
        prompt = f"""
Goal: {self.main_goal}

Available Tools:
{json.dumps(self.available_tools, indent=2)}

Based on the goal and the tools you have, create a step-by-step JSON plan.
"""
        
        plan_str = self.architect.run(input=prompt)
        
        print(f"✅ Architect's Actionable Plan Received:\n{plan_str}")

if __name__ == "__main__":
    main_goal = "Generate a definitive design document for the MISO system itself, based on the contents of 'main.py' and 'src/miso_engine/personas.py'."
    try:
        executive = ExecutiveAgent(main_goal)
        executive.run()
        print("\n🏁 MISO Task Concluded.")
    except Exception as e:
        print(f"\n❌ A critical system error occurred: {e}")
