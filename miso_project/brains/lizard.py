import re

# (PATCHED: Regex is now more flexible)
ERROR_REGEX = re.compile(r"([^:]+):([\d+]):(?:[\d+]:)?\s*error:\s*(.*)\s*\[(.+)\]")

def _parse_mypy_error(error_string: str) -> dict:
    """Parses a standard mypy error string into a structured dictionary."""
    match = ERROR_REGEX.match(error_string)
    if not match:
        match = ERROR_REGEX.match(error_string.strip())
        if not match:
             return {"path": None, "message": error_string, "code": None}

    return {
        "path": match.group(1),
        "message": match.group(3).strip(),
        "code": match.group(4)
    }

def run_lizard_brain(isolated_error: str, file_context: dict) -> list:
    print("--- TIER 1 (Lizard 🦎) ACTIVATED ---")
    
    parsed_error = _parse_mypy_error(isolated_error)
    error_code = parsed_error.get("code")
    error_path = parsed_error.get("path")

    # --- Lizard Brain "Rulebook" ---
    
    if error_code == "duplicate-module-named":
        if error_path:
            # (PATCHED: Path logic is more robust)
            assumed_file_to_delete = error_path
            if not assumed_file_to_delete.endswith('.py'):
                 assumed_file_to_delete += ".py"
            print(f"🦎 Lizard: Matched [duplicate-module-named]. Generating delete plan for {assumed_file_to_delete}.")
            return [
                {
                    "op": "delete_file",
                    "path": assumed_file_to_delete
                }
            ]

    if error_code == "import-not-found":
        print(f"🦎 Lizard: Matched [import-not-found]. Generating mypy.ini plan.")
        
        mypy_ini_content = (
            file_context.get("mypy.ini", "") 
            + "\n[mypy]\nfollow_imports = skip\n"
        )
        
        return [
            {
                "op": "modify_file",
                "path": "mypy.ini",
                "content": mypy_ini_content
            }
        ]

    print(f"🦎 Lizard: No deterministic fix found for [{error_code}]. Escalating.")
    return []
