import sys, os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from miso_engine.agents import Agent
from miso_engine.planners import MisoPlanner

class ExecutiveAgent:
    def __init__(self, main_goal):
        self.main_goal = main_goal
        self.architect = Agent(persona_name='ArchitectAgent')
        print("✅ ExecutiveAgent initialized successfully.")

    def run(self):
        print(f"\n▶️  Delegating to Architect for a plan...")
        plan = self.architect.run(input=f"Create a plan for: {self.main_goal}")
        print(f"✅ Architect Plan Received:\n{plan}")

if __name__ == "__main__":
    main_goal = "Generate a design document."
    try:
        executive = ExecutiveAgent(main_goal)
        executive.run()
        print("\n🏁 MISO Task Concluded.")
    except Exception as e:
        print(f"\n❌ A critical error occurred: {e}")
