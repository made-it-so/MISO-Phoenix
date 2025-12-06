#!/bin/bash

TARGET_DIR="src/modules/gan"
TARGET_FILE="$TARGET_DIR/gladiator.py"
mkdir -p "$TARGET_DIR"

echo "Upgrading Gladiator to INTERACTIVE Mode (CLI Support)..."

# CHUNK 1: Imports & Config
cat << 'EOF' > "$TARGET_FILE"
import logging
import argparse
import sys
import ast
import os
import re
import google.generativeai as genai
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("MISO")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def clean_code_block(text: str) -> str:
    pattern = r"```python\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    return text.replace("```", "").strip()

def get_best_available_model():
    # Hardcoded to the version we know works for you
    return "models/gemini-2.5-flash"
EOF

# CHUNK 2: The Builder (Now handles Self-Testing)
cat << 'EOF' >> "$TARGET_FILE"
class BuilderAgent:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel(get_best_available_model())
        except:
            self.model = None

    def generate(self, context: str, feedback: str = None, auto_test: bool = False) -> str:
        if not self.model: return "def error(): pass"

        prompt = (
            f"Write a Python function for: {context}.\n"
            "Return ONLY raw Python code. No markdown.\n"
        )

        if auto_test:
            prompt += (
                "IMPORTANT: Include a `if __name__ == '__main__':` block at the end.\n"
                "Inside that block, write 3 `assert` statements to verify your function works.\n"
            )

        if feedback:
            prompt += (
                f"\n\nCRITICAL: Your previous attempt failed.\n"
                f"Feedback from Execution Engine: {feedback}\n"
                "Fix the code and Ensure tests pass."
            )
        
        try:
            response = self.model.generate_content(prompt)
            return clean_code_block(response.text)
        except Exception as e:
            return f"# Generation Failed: {e}"
EOF

# CHUNK 3: The Critic (Runs the Code's Internal Tests)
cat << 'EOF' >> "$TARGET_FILE"
class CriticAgent:
    def evaluate(self, code_snippet: str, external_tests: str = None) -> Tuple[float, str]:
        # 1. Syntax Check
        try:
            ast.parse(code_snippet)
        except SyntaxError as e:
            return 0.0, f"SyntaxError on line {e.lineno}: {e.msg}"

        # 2. Execution Sandbox
        sandbox_locals = {}
        try:
            # If external tests exist (from hardcoded demo), run those.
            # If not, we run the file as a script so its internal 'if __name__' block fires.
            
            if external_tests:
                exec(code_snippet, globals(), sandbox_locals)
                exec(external_tests, globals(), sandbox_locals)
            else:
                # Execute the code as if it were a script to trigger internal assertions
                exec(code_snippet, globals(), sandbox_locals)
            
            return 1.0, "PASSED"

        except AssertionError:
            return 0.4, "Logic Error: An assertion failed."
        except Exception as e:
            return 0.1, f"Runtime Error: {type(e).__name__}: {e}"
EOF

# CHUNK 4: Arena & CLI Main
cat << 'EOF' >> "$TARGET_FILE"
class GladiatorArena:
    def __init__(self, builder: BuilderAgent, critic: CriticAgent):
        self.builder = builder
        self.critic = critic

    def fight(self, rounds: int, problem: str, test_harness: str = None) -> Dict[str, Any]:
        logger.info(f"Problem: {problem}")
        best_sol = None
        best_score = -1.0
        last_feedback = None
        
        # If no external harness is provided, tell Builder to self-test
        auto_test_mode = (test_harness is None)

        for r in range(rounds):
            candidate = self.builder.generate(problem, last_feedback, auto_test=auto_test_mode)
            score, feedback = self.critic.evaluate(candidate, test_harness)
            last_feedback = feedback
            
            logger.info(f"Round {r+1}/{rounds} | Score: {score} | Status: {feedback}")

            if score > best_score:
                best_score = score
                best_sol = candidate
                if score == 1.0:
                    break

        return {"best_sol": best_sol, "best_score": best_score}

def main():
    parser = argparse.ArgumentParser(description="MISO Gladiator: AI Code Generator")
    parser.add_argument("problem", nargs="?", help="The coding problem to solve")
    parser.add_argument("--rounds", type=int, default=3, help="Number of GAN rounds")
    args = parser.parse_args()

    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: Set GEMINI_API_KEY environment variable.")
        return

    arena = GladiatorArena(BuilderAgent(), CriticAgent())

    if args.problem:
        # CLI Mode: User provides problem, AI generates its own tests
        result = arena.fight(rounds=args.rounds, problem=args.problem)
    else:
        # Demo Mode: Hardcoded problem with strict external verification
        print("No input provided. Running Demo Mode...")
        prob = "Write 'unique_ordered(lst)' to return unique elements preserving order."
        tests = "assert unique_ordered([1, 2, 2, 1]) == [1, 2]"
        result = arena.fight(rounds=args.rounds, problem=prob, test_harness=tests)

    print("\n" + "="*40)
    print("FINAL SOLUTION")
    print("="*40)
    print(result['best_sol'])
    print("="*40)

if __name__ == "__main__":
    main()
EOF

echo "SUCCESS: Gladiator is now Interactive."
echo "Try: python3 $TARGET_FILE 'Write a function to generate a random password'"
