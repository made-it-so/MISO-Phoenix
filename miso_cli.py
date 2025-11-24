import os
import sys
import logging
import subprocess
import google.generativeai as genai
import json

# CONFIG
# We point to 'miso-worker' so that 'import app' works correctly
WORKER_DIR = os.path.join(os.getcwd(), "miso-worker")
sys.path.append(WORKER_DIR)

# Now we can safely import from the app package
from app.researcher import Researcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [INTERFACE] %(message)s')
logger = logging.getLogger(__name__)

def get_api_key(): return os.environ.get("GEMINI_API_KEY")

def route_intent(user_prompt):
    """
    Decides which agent handles the user's command.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    ROUTER:
    User Input: "{user_prompt}"
    
    AGENTS:
    1. RESEARCHER: Analyzes text/articles/theory. Input is usually a long text or URL.
    2. COMMANDER: Executes linux commands, creates files, installs tools.
    3. EXECUTIVE: Sets high level strategy, manages budget.
    
    OUTPUT ONE WORD: RESEARCHER, COMMANDER, or EXECUTIVE.
    """
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip().upper()
    except: return "COMMANDER"

def main():
    key = get_api_key()
    if not key:
        print("❌ SETUP ERROR: Export GEMINI_API_KEY first.")
        return

    genai.configure(api_key=key)
    
    print("\n🤖 MISO V32 INTERFACE ONLINE.")
    print("   (Type 'exit' to quit, or paste the article text to analyze it)\n")

    while True:
        try:
            user_input = input("MISO> ")
            if user_input.lower() in ['exit', 'quit']: break
            if not user_input.strip(): continue

            # 1. ROUTE
            agent = route_intent(user_input[:200]) # Route based on first 200 chars
            print(f"   ↳ Routing to: {agent}...")

            # 2. DISPATCH
            if agent == "RESEARCHER":
                r = Researcher()
                analysis = r.analyze_paper(user_input)
                print(f"\n📄 RESEARCH REPORT:\n{json.dumps(analysis, indent=2)}\n")
                
                if analysis:
                    do_it = input("   👉 Implement this recommendation? (y/n): ")
                    if do_it.lower() == 'y':
                        cmd = f"Upgrade system based on this research: {analysis['recommendation']}"
                        subprocess.run(["python3", "miso-worker/app/commander.py", cmd])

            elif agent == "COMMANDER":
                subprocess.run(["python3", "miso-worker/app/commander.py", user_input])
            
            elif agent == "EXECUTIVE":
                subprocess.run(["python3", "miso-worker/app/executive.py"])

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
