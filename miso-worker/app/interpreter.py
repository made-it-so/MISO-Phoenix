import subprocess
import sys
import logging
import os
import google.generativeai as genai

# LOGGING TO STDOUT
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [INTERPRETER] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class CodeInterpreter:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use Flash for speed when writing simple scripts
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_code(self, task):
        prompt = f"""
        Write a Python script to solve this task: "{task}"
        
        RULES:
        1. Output ONLY raw python code. No markdown.
        2. Print the final result to stdout using print().
        3. Do not use input() or external APIs unless absolutely necessary.
        4. Keep it simple and self-contained.
        """
        try:
            response = self.model.generate_content(prompt)
            # Strip formatting
            code = response.text.replace('```python', '').replace('```', '').strip()
            return code
        except: return None

    def execute(self, task):
        code = self.generate_code(task)
        if not code: return "Failed to generate code."
        
        logger.info(f"🐍 Generated Python for: {task[:30]}...")
        
        filename = "temp_task.py"
        try:
            with open(filename, 'w') as f: f.write(code)
            
            # Run with 5 second timeout to prevent infinite loops
            result = subprocess.run(
                ["python3", filename], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            output = result.stdout.strip()
            if result.returncode != 0:
                # Capture stderr if it crashed
                output = f"Script Error: {result.stderr.strip()}"
                
            logger.info(f"   -> Output: {output[:50]}...")
            return output
            
        except subprocess.TimeoutExpired:
            return "Error: Script timed out (5s limit)."
        except Exception as e:
            return f"Execution Error: {e}"
        finally:
            if os.path.exists(filename): os.remove(filename)

if __name__ == "__main__":
    # Quick Test
    ci = CodeInterpreter()
    print("Test Result:", ci.execute("Calculate the sum of numbers from 1 to 100"))
