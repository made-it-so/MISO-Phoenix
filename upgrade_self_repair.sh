#!/bin/bash

TARGET_DIR="src/modules/gan"
TARGET_FILE="$TARGET_DIR/gladiator.py"
mkdir -p "$TARGET_DIR"

echo "Upgrading Gladiator with SELF-REPAIR (Feedback Loop)..."

# CHUNK 1: Setup (Same as before)
cat << 'EOF' > "$TARGET_FILE"
import logging
import time
import ast
import os
import re
import google.generativeai as genai
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def clean_code_block(text: str) -> str:
    pattern = r"```python\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    return text.replace("```", "").strip()

def get_best_available_model():
    # Fast priority list
    return "models/gemini-1.5-flash"
EOF

echo "Chunk 1 written..."

# CHUNK 2: The Builder (Now accepts Feedback!)
cat << 'EOF' >> "$TARGET_FILE"
class BuilderAgent:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel(get_best_available_model())
        except:
            self.model = None

    def generate(self, context: str, feedback: str = None) -> str:
        if not self.model: return "def error(): pass"

        # Base prompt
        prompt = (
            f"Write a Python function for: {context}.\n"
            "Return ONLY raw Python code. No markdown."
        )

        # IN-CONTEXT LEARNING: Inject the failure from the previous round
        if feedback:
            prompt += (
                f"\n\nCRITICAL: Your previous attempt failed.\n"
                f"Feedback from Tester: {feedback}\n"
                "Please fix the code to satisfy the tester."
            )
        
        try:
            response = self.model.generate_content(prompt)
            return clean_code_block(response.text)
        except Exception as e:
            return "def failed(): pass"

    def update_weights(self, feedback: float):
        pass
EOF

echo "Chunk 2 written..."

# CHUNK 3: The Critic (Returns detailed Error Logs)
cat << 'EOF' >> "$TARGET_FILE"
class CriticAgent:
    def evaluate(self, code_snippet: str, test_harness: str) -> Tuple[float, str]:
        # 1. Syntax Check
        try:
            ast.parse(code_snippet)
        except SyntaxError as e:
            msg = f"SyntaxError on line {e.lineno}: {e.msg}"
            return 0.0, msg

        # 2. Execution Sandbox
        sandbox_locals = {}
        try:
            # Load function
            exec(code_snippet, globals(), sandbox_locals)
            
            # Run tests. We assume tests use 'assert'
            exec(test_harness, globals(), sandbox_locals)
            
            return 1.0, "PASSED"

        except AssertionError as e:
            # We try to capture which test failed if possible, generally manual assert messages help
            return 0.4, "Logic Error: A unit test assertion failed."
        except Exception as e:
            return 0.1, f"Runtime Error: {type(e).__name__}: {e}"

class GladiatorArena:
    def __init__(self, builder: BuilderAgent, critic: CriticAgent):
        self.builder = builder
        self.critic = critic
        self.history = []

    def fight(self, rounds: int, problem: str, test_harness: str) -> Dict[str, Any]:
        logger.info(f"Problem: {problem}")
        best_sol = None
        best_score = -1.0
        
        # This variable carries the 'Memory' of the failure to the next round
        last_feedback = None

        for r in range(rounds):
            # Pass the previous error to the builder
            candidate = self.builder.generate(problem, last_feedback)
            
            # Get Score AND Feedback
            score, feedback_msg = self.critic.evaluate(candidate, test_harness)
            
            # Store feedback for the next loop
            last_feedback = feedback_msg
            
            preview = candidate.split('\n')[0]
            logger.info(f"Round {r+1} | Score: {score} | Feedback: {feedback_msg}")

            self.history.append({"r": r+1, "code": candidate, "score": score, "feedback": feedback_msg})

            if score > best_score:
                best_score = score
                best_sol = candidate
                if score == 1.0:
                    logger.info("Perfect solution found!")
                    break

        return {"best_sol": best_sol, "best_score": best_score}
EOF

echo "Chunk 3 written..."

# CHUNK 4: Harder Test Case (Unique Elements in Order)
cat << 'EOF' >> "$TARGET_FILE"
def run_test():
    print("Initializing MISO Self-Repair Engine...")
    if not os.getenv("GEMINI_API_KEY"):
        print("Set GEMINI_API_KEY first.")
        return

    arena = GladiatorArena(BuilderAgent(), CriticAgent())
    
    # A problem where simple 'set()' fails because it loses order
    # This often trips up LLMs on the first try if they aren't careful
    problem = "Write 'unique_ordered(lst)' to return a list of unique elements from 'lst', keeping their original order."
    
    tests = """
assert unique_ordered([1, 2, 2, 3, 1]) == [1, 2, 3]
assert unique_ordered(['a', 'b', 'a']) == ['a', 'b']
    """
    
    result = arena.fight(rounds=4, problem=problem, test_harness=tests)
    
    print("\n--- Best Solution ---")
    print(result['best_sol'])

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s')
    run_test()
EOF

echo "Chunk 4 written."
echo "SUCCESS: Self-Repair Installed."
