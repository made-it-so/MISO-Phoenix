import logging
import argparse
import sys
import ast
import os
import re
import json
import boto3
import google.generativeai as genai
from datetime import datetime
from typing import List, Dict, Any, Tuple

# --- PATH FIX ---
if os.getcwd() not in sys.path: sys.path.append(os.getcwd())

from src.modules.safety import sandbox
from src.modules.memory.hippocampus import Hippocampus

logger = logging.getLogger('MISO')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- CONFIGURATION ---
API_KEY = os.getenv('GEMINI_API_KEY')
if API_KEY: genai.configure(api_key=API_KEY)

S3_BUCKET = 'miso-application-forge-ui-oxvkhfa8'
S3_KEY = 'status.json'
s3_client = boto3.client('s3')

# Initialize Subsystems
sandbox.build_image()
memory = Hippocampus()

def broadcast(module, status, metric, log_msg=None):
    try:
        payload = {
            'status': status, 'module': module, 'metric': metric,
            'logs': [{'time': datetime.now().strftime('%H:%M:%S'), 'type': 'INFO', 'msg': log_msg}] if log_msg else []
        }
        s3_client.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=json.dumps(payload), ContentType='application/json', ACL='public-read', CacheControl='max-age=0')
    except: pass

def clean_code_block(text: str) -> str:
    pattern = r'```python\n(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    if match: return match.group(1).strip()
    return text.replace('```', '').strip()

class BuilderAgent:
    def __init__(self):
        try: self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        except: self.model = None

    def generate(self, context: str, feedback: str = None, auto_test: bool = False) -> str:
        # 1. CHECK MEMORY FIRST (The Reflex)
        if not feedback: # Only check memory on first attempt, not during repairs
            recall = memory.recall(context)
            if recall:
                broadcast('HIPPOCAMPUS', 'RECALL', 'Cache Hit', 'Solution retrieved from Vector DB. Cost: $0.00')
                return recall['code']

        # 2. If no memory, generate (The Thought)
        if not self.model: return 'def error(): pass'
        broadcast('BUILDER', 'GENERATING', 'Thinking...', f'Generating solution for: {context[:30]}...')
        prompt = f'Write a Python function for: {context}.\nReturn raw Python code.\n'
        if auto_test: prompt += 'Include `if __name__ == "__main__":` block with 3 assertions.\n'
        if feedback: prompt += f'\nCRITICAL: Previous failed.\nFeedback: {feedback}\nFix it.'
        try:
            response = self.model.generate_content(prompt)
            return clean_code_block(response.text)
        except Exception as e:
            broadcast('BUILDER', 'ERROR', 'API Fail', str(e))
            return f'# Gen Failed: {e}'

class CriticAgent:
    def evaluate(self, code_snippet: str, external_tests: str = None) -> Tuple[float, str]:
        broadcast('CRITIC', 'REVIEWING', 'Syntax Check', 'Checking Python AST...')
        try: ast.parse(code_snippet)
        except SyntaxError as e: return 0.0, f'SyntaxError: {e.msg}'
        
        broadcast('CRITIC', 'SANDBOXING', 'Docker', 'Spinning up ephemeral container...')
        test_payload = external_tests if external_tests else 'pass'
        return sandbox.run_code(code_snippet, test_payload)

class GladiatorArena:
    def __init__(self, builder, critic):
        self.builder = builder
        self.critic = critic

    def fight(self, rounds: int, problem: str, test_harness: str = None):
        logger.info(f'Problem: {problem}')
        broadcast('ARENA', 'STARTING', 'Round 0', f'New Match: {problem}')
        best_sol = None
        best_score = -1.0
        last_feedback = None
        auto_test_mode = (test_harness is None)

        for r in range(rounds):
            cand = self.builder.generate(problem, last_feedback, auto_test=auto_test_mode)
            score, feedback = self.critic.evaluate(cand, test_harness)
            last_feedback = feedback
            status_msg = f'Round {r+1} Result: {feedback} (Score: {score})'
            logger.info(status_msg)
            broadcast('ARENA', 'FIGHTING', f'Round {r+1}/{rounds}', status_msg)
            
            if score > best_score:
                best_score = score
                best_sol = cand
                if score == 1.0: 
                    broadcast('ARENA', 'VICTORY', 'Perfect Score', 'Optimization Complete.')
                    # 3. STORE IN MEMORY
                    memory.memorize(problem, cand, score)
                    break
        return {'best_sol': best_sol, 'best_score': best_score}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('problem', nargs='?')
    parser.add_argument('--rounds', type=int, default=3)
    args = parser.parse_args()
    if not os.getenv('GEMINI_API_KEY'): print('ERROR: Set GEMINI_API_KEY'); return
    arena = GladiatorArena(BuilderAgent(), CriticAgent())
    if args.problem: res = arena.fight(rounds=args.rounds, problem=args.problem)
    else: res = arena.fight(rounds=args.rounds, problem='Write unique_ordered(l)')
    print('='*40 + '\nFINAL SOLUTION\n' + '='*40)
    print(res['best_sol'])

if __name__ == '__main__': main()