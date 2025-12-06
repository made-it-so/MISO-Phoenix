#!/bin/bash

TARGET_DIR="src/modules/gan"
TARGET_FILE="$TARGET_DIR/gladiator.py"
mkdir -p "$TARGET_DIR"

echo "Connecting Gladiator to Gemini API (With Auto-Discovery)..."

# CHUNK 1: Imports and Configuration
cat << 'EOF' > "$TARGET_FILE"
import logging
import time
import random
import ast
import os
import re
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
    """Strips markdown code fences like ```python ... ``` from LLM output."""
    pattern = r"```python\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.replace("```", "").strip()

def get_best_available_model():
    """
    Dynamically finds a working model supported by the API key.
    """
    if not API_KEY:
        return "no-key-configured"
        
    try:
        logger.info("Listing available Gemini models...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        logger.info(f"Available models: {available_models}")

        # Priority list
        priorities = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-001",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro",
            "models/gemini-pro",
            "models/gemini-1.0-pro"
        ]

        for p in priorities:
            if p in available_models:
                logger.info(f"Selected Model: {p}")
                return p
        
        # Fallback to the first available if none of our preferences match
        if available_models:
            logger.info(f"Fallback Model: {available_models[0]}")
            return available_models[0]
            
        return "gemini-pro" # Blind guess if list fails

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return "gemini-pro"
EOF

echo "Chunk 1 (Imports & Discovery) written..."

# CHUNK 2: The Gemini Builder Agent
cat << 'EOF' >> "$TARGET_FILE"
class BuilderAgent:
    """
    The Generator. Uses Google Gemini to write Python code.
    """
    def __init__(self):
        self.iteration_count = 0
        self.model_name = get_best_available_model()
        
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None

    def generate(self, context: str) -> str:
        self.iteration_count += 1
        
        if not self.model:
            return "def error(): return 'No Model Configured'"

        prompt = (
            f"Write a Python function to solve this problem: {context}. "
            "Return ONLY the raw Python code. Do not include markdown formatting or explanations."
        )

        try:
            # Generate content
            response = self.model.generate_content(prompt)
            raw_text = response.text
            
            # Clean the output (remove markdown backticks)
            clean_code = clean_code_block(raw_text)
            return clean_code

        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return f"def error_{self.iteration_count}(): return 'Generation Failed'"

    def update_weights(self, feedback: float):
        pass
EOF

echo "Chunk 2 (Builder) written..."

# CHUNK 3: The AST Critic
cat << 'EOF' >> "$TARGET_FILE"
class CriticAgent:
    """
    The Discriminator. Uses AST to validate Python syntax.
    """
    def __init__(self, model_name: str = "miso-critic-v1"):
        self.model_name = model_name

    def evaluate(self, code_snippet: str) -> float:
        try:
            ast.parse(code_snippet)
            score = 0.5
            
            # Heuristics
            if "def " in code_snippet: score += 0.2
            if "return" in code_snippet: score += 0.1
            if len(code_snippet) > 50: score += 0.1
            
            return min(score, 1.0)
        except SyntaxError as e:
            logger.warning(f"Critic rejected code: {e.msg}")
            return 0.0
        except Exception:
            return 0.0

class GladiatorArena:
    def __init__(self, builder: BuilderAgent, critic: CriticAgent):
        self.builder = builder
        self.critic = critic
        self.history: List[Dict[str, Any]] = []

    def fight(self, rounds: int = 5, problem_context: str = "sort_list") -> Dict[str, Any]:
        logger.info(f"Starting Gladiator Fight: {rounds} rounds.")
        best_solution = None
        best_score = -1.0

        for r in range(rounds):
            logger.info(f"--- Round {r+1} ---")
            candidate = self.builder.generate(problem_context)
            
            preview = candidate[:50].replace('\n', ' ') + "..."
            logger.info(f"Builder proposed: {preview}")

            score = self.critic.evaluate(candidate)
            self.builder.update_weights(score)

            self.history.append({"round": r+1, "candidate": candidate, "score": score})

            if score > best_score:
                best_score = score
                best_solution = candidate
                logger.info(f"New Champion! Score: {score:.2f}")

        return {
            "best_solution": best_solution,
            "best_score": best_score,
            "history": self.history
        }
EOF

echo "Chunk 3 (Agents) written..."

# CHUNK 4: Test Harness
cat << 'EOF' >> "$TARGET_FILE"
def run_test():
    print("Initializing MISO Gladiator (Gemini Powered)...")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is not set!")
        return

    builder = BuilderAgent()
    critic = CriticAgent()
    arena = GladiatorArena(builder, critic)
    
    # Simple problem to prove it works
    problem = "Calculate factorial of n recursively"
    
    try:
        result = arena.fight(rounds=2, problem_context=problem)
        print("\n--- Match Results ---")
        print(f"Best Score: {result['best_score']:.2f}")
        print("Best Solution generated by Gemini:")
        print("-" * 40)
        print(result['best_solution'])
        print("-" * 40)
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
    run_test()
EOF

echo "Chunk 4 (Main) written."
echo "SUCCESS: Gladiator updated with Auto-Discovery."
