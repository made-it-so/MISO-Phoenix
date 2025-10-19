# main.py

from miso_engine.tools import TOOL_MAP, ToolError, TOOL_SIGNATURES, list_files
from miso_engine.planners import StrategistAgent, TacticianAgent
from miso_engine.personas import get_persona_council
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ExecutiveAgent:
    """The final, 'COO' architecture: A dynamic resource allocator."""
    def __init__(self, main_goal: str):
        self.main_goal = main_goal
        self.strategist = StrategistAgent()
        self.tactician = TacticianAgent()
        self.global_history = []

    def run(self, max_total_steps: int = 50):
        # --- PHASE 1: STRATEGY ---
        strategic_plan = self.strategist.create_strategic_plan(self.main_goal)
        logging.info(f"Executive Agent created a strategic plan with {len(strategic_plan)} milestones.")
        
        # --- PHASE 2: TACTICS ---
        for i, milestone in enumerate(strategic_plan):
            milestone_history = [] 
            milestone_complete = False
            
            logging.info(f"\n{'='*20}\n▶️  EXECUTIVE: Pursuing Milestone {i+1}/{len(strategic_plan)}: '{milestone}'\n{'='*20}")
            
            # --- DYNAMIC RESOURCE ALLOCATION ---
            max_steps_per_milestone = 15 # The initial budget
            steps_taken_this_milestone = 0
            stagnation_counter = 0
            previous_thoughts = []

            while steps_taken_this_milestone < max_steps_per_milestone and not milestone_complete:
                steps_taken_this_milestone += 1
                
                try:
                    project_layout = list_files()
                    tool_signatures_str = "\n".join([f"- `{sig}`" for sig in TOOL_SIGNATURES.values()])
                    
                    next_action_plan = self.tactician.get_next_action(
                        self.main_goal, milestone, milestone_history, project_layout, tool_signatures_str
                    )
                    
                    thought = next_action_plan.get('thought')
                    
                    # --- STAGNATION DETECTION ---
                    # If the agent has the same thought 3 times in a row, it's stuck.
                    if thought in previous_thoughts:
                        stagnation_counter += 1
                        logging.warning(f"Stagnation detected! Agent has repeated a thought. Count: {stagnation_counter}")
                    else:
                        stagnation_counter = 0 # Reset if progress is made
                        previous_thoughts.append(thought)
                    
                    if stagnation_counter >= 3:
                        raise ToolError("Infinite loop detected. The agent is repeating the same plan. Halting.")

                    action = next_action_plan.get('action', {})
                    tool_name = action.get('tool_name')
                    
                    if tool_name == "finish_milestone":
                        milestone_complete = True; continue

                    observation = TOOL_MAP[tool_name](**action.get('parameters', {}))
                    full_log_entry = f"Step {len(self.global_history) + 1} SUCCESS: Tool '{tool_name}'. Obs: {observation}"
                    self.global_history.append(full_log_entry)
                    milestone_history.append(full_log_entry)

                except Exception as e:
                    logging.error(f"A tactical step has failed: {e}")
                    # If an error occurs, we halt immediately instead of looping.
                    milestone_complete = False; break

                # --- PERFORMANCE REVIEW & BUDGET EXTENSION ---
                if steps_taken_this_milestone == max_steps_per_milestone - 1 and not milestone_complete:
                    if stagnation_counter < 2: # Check if the agent is still making productive, non-repetitive moves
                        logging.warning("Performance review: Milestone is complex and requires more time. Granting a budget extension.")
                        max_steps_per_milestone += 10 # Grant an extension of 10 steps
                        logging.info(f"New step limit for this milestone is now {max_steps_per_milestone}.")
            
            if not milestone_complete:
                print(f"\n--- MISO Task Halted: Failed to complete milestone '{milestone}' within the allocated budget. ---")
                return

        print("\n--- MISO Task Complete: All milestones were achieved successfully. ---")


if __name__ == "__main__":
    USER_GOAL = "My core logic is too simple. I need to upgrade myself to include a 'Persona Council' for strategic planning. To do this, I must first create the `src/miso_engine/personas.py` file, then create the `src/miso_engine/executive_tools.py` file, then modify the main `main.py` file to implement the new 'Strategy Phase' and goal stack logic, and finally run tests to verify the full system upgrade."
    
    executive = ExecutiveAgent(main_goal=USER_GOAL)
    executive.run()
