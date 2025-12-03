#!/bin/bash

TARGET_DIR="src/modules/gan"
TARGET_FILE="$TARGET_DIR/gladiator.py"
mkdir -p "$TARGET_DIR"

echo "Upgrading Gladiator to EXECUTION Phase..."

# CHUNK 1: Imports and Model Discovery (Kept from previous version)
cat << 'EOF' > "$TARGET_FILE"
import logging
import time
import random
import ast
import os
import re
import sys
import io
import traceback
import google.generativeai as genai
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    logger.warning("GEMINI_API_KEY not found. Builder will fail.")
else:
    genai.configure(api_key=API_KEY)

def clean_code_block(text: str) -> str:
    """Strips markdown code fences."""
    pattern = r"```python\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.replace("```", "").strip()

def get_best_available_model():
    """Finds best available Gemini model."""
    if not API_KEY: return "no-key"
    try:
        # Simplified discovery for speed
        priorities = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash",
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]
        # We blindly trust the priority list to save startup time
        # You can revert to full discovery if you get 404s
        return priorities[0] 
    except:
        return "gemini-pro"
EOF

echo "Chunk 1 (Setup) written..."

# CHUNK 2: The Builder (Updated Prompting)
cat << 'EOF' >> "$TARGET_FILE"
class BuilderAgent:
    def __init__(self):
        self.model_name = get_best_available_model()
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except:
            self.model = None

    def generate(self, context: str) -> str:
        if not self.model: return "def error(): pass"

        # Prompt engineering: Explicitly ask for specific function names
        prompt = (
            f"Write a Python function to solve this: {context}.\n"
            "IMPORTANT: Return ONLY the raw code. No markdown. No comments outside the function.\n"
            "Ensure the function name matches the problem requirement."
        )
        
        try:
            response = self.model.generate_content(prompt)
            return clean_code_block(response.text)
        except Exception as e:
            logger.error(f"Gen Error: {e}")
            return "def failed(): pass"

    def update_weights(self, feedback: float):
        pass
EOF

echo "Chunk 2 (Builder) written..."

# CHUNK 3: The Execution Critic (The Big Change)
cat << 'EOF' >> "$TARGET_FILE"
class CriticAgent:
    """
    Validates code by ACTUALLY RUNNING IT against unit tests.
    """
    def evaluate(self, code_snippet: str, test_harness: str) -> float:
        # 1. Syntax Check
        try:
            ast.parse(code_snippet)
        except SyntaxError as e:
            logger.warning(f"Syntax Error: {e.msg}")
            return 0.0

        # 2. Execution Sandbox
        # We create a dictionary to serve as the local memory for the code
        sandbox_locals = {}
        
        try:
            # Step A: Define the function in memory
            exec(code_snippet, globals(), sandbox_locals)
            
            # Step B: Run the tests against that memory
            # We inject the functions defined in Step A into Step B's scope
            exec(test_harness, globals(), sandbox_locals)
            
            # If we reach here, no Assertions failed!
            return 1.0

        except AssertionError:
            # Code ran, but produced wrong results
            return 0.4 
        except Exception as e:
            # Code crashed (Runtime Error, NameError, etc)
            logger.info(f"Runtime Error: {e}")
            return 0.1

class GladiatorArena:
    def __init__(self, builder: BuilderAgent, critic: CriticAgent):
        self.builder = builder
        self.critic = critic
        self.history = []

    def fight(self, rounds: int, problem: str, test_harness: str) -> Dict[str, Any]:
        logger.info(f"Problem: {problem}")
        best_sol = None
        best_score = -1.0

        for r in range(rounds):
            # Generate
            candidate = self.builder.generate(problem)
            
            # Evaluate (Pass tests too!)
            score = self.critic.evaluate(candidate, test_harness)
            
            # Log
            preview = candidate.split('\n')[0]
            logger.info(f"Round {r+1} | Score: {score} | {preview}...")
            
            self.history.append({"r": r+1, "code": candidate, "score": score})

            if score > best_score:
                best_score = score
                best_sol = candidate
                if score == 1.0:
                    logger.info("Perfect solution found! Stopping early.")
                    break # Early stopping for efficiency

        return {"best_sol": best_sol, "best_score": best_score}
EOF

echo "Chunk 3 (Critic) written..."

# CHUNK 4: Test Harness with Real Test Cases
cat << 'EOF' >> "$TARGET_FILE"
def run_test():
    print("Initializing MISO Execution Engine...")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set.")
        return

    builder = BuilderAgent()
    critic = CriticAgent()
    arena = GladiatorArena(builder, critic)
    
    # --- SCENARIO 1: Palindrome ---
    # We define the problem and the STRICT tests it must pass
    problem = "Write a function named 'is_palindrome(s)' that returns True if s is a palindrome, else False."
    
    # Python code that asserts the logic. 
    # The Critic runs this AFTER loading the builder's code.
    tests = """
assert is_palindrome('racecar') == True
assert is_palindrome('hello') == False
assert is_palindrome('A') == True
    """
    
    result = arena.fight(rounds=3, problem=problem, test_harness=tests)
    
    print("\n--- Final Result ---")
    print(f"Score: {result['best_score']}")
    print("Code:")
    print(result['best_sol'])

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s')
    run_test()
EOF

echo "Chunk 4 (Main) written."
echo "SUCCESS: Execution Critic Installed."
