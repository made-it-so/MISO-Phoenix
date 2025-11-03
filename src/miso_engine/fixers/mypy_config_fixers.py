import re
from pathlib import Path

# This list is loaded by main.py
ERROR_CODES = ['import-not-found', 'duplicate-module-named', 'no-untyped-defs']

def get_mypy_path_from_error(error: dict) -> str:
    """
    Parses the file path from a mypy error to find the correct
    root directory (e.g., 'src', 'workspace', 'backend').
    """
    file_path_str = error.get("file_path", "")
    if not file_path_str:
        return "src" # Default fallback
        
    path = Path(file_path_str)
    
    # Handle paths like "src/miso_engine/util.py" -> "src"
    # Or "workspace/temp.py" -> "workspace"
    if len(path.parts) > 1:
        return path.parts[0]
        
    # Default to 'src' if it's a top-level file (unlikely)
    return "src"

def generate_plan(error: dict) -> dict:
    """
    Handles deterministic mypy fixes.
    This is a "smart" brain. It applies context-aware fixes.
    """
    message = error.get("message", "")
    # We add the raw message to the error dict for our fallback parser
    error["raw_message"] = f"REFINEMENT: {error.get('file_path','')}:{error.get('line', '')}: {message}"
    
    if "Cannot find implementation or library stub" in message:
        # This is 'import-not-found'
        
        # 1. Dynamically find the path (e.g., "src" or "workspace")
        mypy_path_to_add = get_mypy_path_from_error(error)
        
        # 2. Generate the plan
        return {
            "tool": "modify_file",
            "file_path": "mypy.ini",
            "specialist_agent": "ProgrammerAgent-Pro", # Use our reliable agent
            "modification_task": f"Ensure the mypy.ini file exists and includes '{mypy_path_to_add}' in its 'mypy_path'. The mypy_path should be a comma-separated list (e.g., mypy_path = src,workspace). Do not remove existing paths, only add '{mypy_path_to_add}' if it is not present."
        }
            
    elif "Duplicate module named" in message or "Source file found twice" in message:
        # 🚀 --- THE FINAL FIX --- 🚀
        # This error is caused by old, bad .pyi/.py stubs.
        # The fix is to delete the file that is *causing* the error.
        
        # We parse the *file path* (e.g., "workspace/sum_function.py")
        # directly from the error.
        
        file_to_delete = error.get("file_path")

        if not file_to_delete:
             return None # Can't parse, escalate

        return {
            "tool": "execute_shell",
            "command": f"rm -f {file_to_delete}"
        }
        # --- END FIX ---
            
    # If no logic matches, escalate to Primate Brain
    return None
