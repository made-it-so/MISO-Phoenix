import subprocess
import os
import json
import re
from typing import Dict, List, Tuple, Literal

# Add project root to path to allow absolute imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, PROJECT_ROOT)

from llm import llm_client

# Define return statuses
TDD_STATUS = Literal["PASS", "FAIL"]
TDD_STAGE = Literal["mypy", "pytest", "all"]

def _run_tdd_command(command: str) -> Tuple[TDD_STATUS, str]:
    '''Helper to run a single TDD shell command.'''
    try:
        # Use shell=True to interpret the command string
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False # Do not raise exception on non-zero exit
        )
        if result.returncode == 0:
            return "PASS", result.stdout
        else:
            return "FAIL", result.stdout + result.stderr
    except Exception as e:
        return "FAIL", f"TDD command execution failed: {e}"

def check_tdd_harness(tdd_harness: Dict[str, str]) -> Tuple[TDD_STATUS, str, TDD_STAGE]:
    '''Runs all TDD checks (mypy, pytest).'''
    
    # 1. Run MyPy
    mypy_cmd = tdd_harness.get("mypy")
    if mypy_cmd:
        print("TDD: Running mypy...")
        status, output = _run_tdd_command(mypy_cmd)
        if status == "FAIL":
            print("TDD: mypy FAILED.")
            return "FAIL", output, "mypy"
    print("TDD: mypy PASSED.")

    # 2. Run Pytest
    pytest_cmd = tdd_harness.get("pytest")
    if pytest_cmd:
        print("TDD: Running pytest...")
        status, output = _run_tdd_command(pytest_cmd)
        if status == "FAIL":
            print("TDD: pytest FAILED.")
            return "FAIL", output, "pytest"
    print("TDD: pytest PASSED.")

    # If all checks passed
    return "PASS", "All TDD checks passed.", "all"

def _construct_llm_prompt(workspace_dir: str, tdd_output: str) -> str:
    '''Constructs the context prompt for the LLM.'''
    context = "## TDD FAILURE ##\\n"
    context += "The following TDD checks failed:\\n"
    context += f"```\\n{tdd_output}\\n```\\n\\n"
    context += "## CURRENT FILE CONTENTS ##\\n"
    context += "Here are the contents of the files in the workspace:\\n\\n"
    
    for root, _, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                # Get path relative to workspace dir for the LLM
                relative_path = os.path.relpath(filepath, workspace_dir)
                context += f"### File: {relative_path} ###\\n"
                try:
                    with open(filepath, 'r') as f:
                        context += f"```python\\n{f.read()}\\n```\\n\\n"
                except Exception as e:
                    context += f"[Could not read file: {e}]\\n\\n"
    
    context += "\\nYour task is to fix the code to pass the TDD tests."
    context += "You must provide your answer ONLY in the specified JSON format."
    return context

def _parse_llm_response(response_text: str) -> List[Dict[str, str]]:
    '''Parses the LLM's JSON response, handling errors.'''
    try:
        # Find the JSON block
        json_match = re.search(r'```json\\n(.*?)\\n```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Assume raw JSON if no markdown block
            json_str = response_text
        
        # Handle empty list response (escalation)
        if json_str.strip() == "[]":
            return []
            
        parsed = json.loads(json_str)
        if isinstance(parsed, list):
            return parsed
        else:
            print(f"LLM Error: Response was valid JSON but not a list: {parsed}")
            return []
    except json.JSONDecodeError:
        print(f"LLM Error: Failed to decode JSON response:\\n{response_text}")
        return []
    except Exception as e:
        print(f"LLM Error: Unknown parsing error: {e}")
        return []

def generate_fix(
    workspace_dir: str, tdd_output: str, persona: Dict
) -> List[Dict[str, str]]:
    '''
    Generates a code fix using the LLM based on TDD output.
    '''
    print(f"Brain ({persona['name']}): Generating fix for TDD failure...")
    
    # 1. Construct Persona Prompt
    persona_prompt = (
        f"You are {persona['name']}. {persona['description']}.\\n"
        "Your response MUST follow these rules:\\n"
        + "\\n".join(f"- {rule}" for rule in persona['rules'])
        + f"\\nYour response MUST be in this exact format: {persona['response_format']}"
    )
    
    # 2. Construct Context Prompt
    context_prompt = _construct_llm_prompt(workspace_dir, tdd_output)
    
    # 3. Call LLM
    response_text = llm_client.get_llm_response(
        persona_prompt, 
        context_prompt, 
        persona.get("model_provider", {})
    )
    
    # 4. Parse Response
    fix_list = _parse_llm_response(response_text)
    return fix_list
    

def apply_fix_to_workspace(
    workspace_dir: str, fix_list: List[Dict[str, str]]
):
    '''
    Writes the files from the LLM's fix list to the workspace.
    '''
    if not fix_list:
        print("Workspace: No fixes to apply.")
        return
        
    for file_fix in fix_list:
        try:
            filename = file_fix['filename']
            code = file_fix['code']
            
            # Ensure path is safe and within workspace
            filepath = os.path.abspath(os.path.join(workspace_dir, filename))
            if not filepath.startswith(os.path.abspath(workspace_dir)):
                print(f"Workspace Error: Invalid path '{filename}' is outside workspace.")
                continue
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                f.write(code)
            print(f"Workspace: Applied fix to {filename}")
            
        except KeyError:
            print(f"Workspace Error: Invalid fix object format: {file_fix}")
        except Exception as e:
            print(f"Workspace Error: Failed to write file {filename}: {e}")
