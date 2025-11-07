import sys
import os
import re
import json
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import argparse
import traceback
import time
import tempfile
import shutil
import importlib
import ast #  NEW: Abstract Syntax Tree for context

# --- FIX: ADD SRC TO SYS.PATH ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
# --- END FIX ---

# --- Import Miso Components ---
try:
    from miso_engine.agents import Agent
    from miso_engine.util import (
        read_file, write_file, create_file, get_file_manifest,
        run_shell, extract_json, query_development_logs, 
        parse_mypy_output, parse_ruff_output, logger
    )
except ImportError as e:
    print(f"ERROR: Could not import Miso components: {e}")
    print("Ensure src/miso_engine/agents.py and src/miso_engine/util.py exist.")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error importing Miso components: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- GLOBAL AGENT DICT ---
agents: Dict[str, Agent] = {}

# --- UNIFIED DETERMINISTIC PLAN VALIDATION ---
VALID_PLAN_STRUCTURES = {
    "read_file": {"required_keys": ["file_path", "specialist_agent", "analysis_task"]},
    "modify_file": {"required_keys": ["file_path", "specialist_agent", "modification_task"]},
    "create_file": {"required_keys": ["file_path", "content"]},
    "execute_shell": {"required_keys": ["command"]},
    "halt": {"required_keys": ["reason"]},
}

def validate_plan(plan: Dict[str, Any], manifest_files: List[str]) -> Tuple[bool, str]:
    """
    Deterministically checks the plan's structure AND logic.
    """
    if not isinstance(plan, dict):
        return False, f"Plan is not a valid dictionary. Got: {type(plan)}"
    tool_name = plan.get("tool")
    if not tool_name:
        return False, "Plan is missing the required 'tool' key."
    if not isinstance(tool_name, str):
        return False, f"Plan 'tool' must be a string, but got type: {type(tool_name)}. (Full plan: {plan})"
    if tool_name not in VALID_PLAN_STRUCTURES:
        return False, f"Plan specifies an unknown tool: '{tool_name}'."
    
    required_keys = VALID_PLAN_STRUCTURES[tool_name]["required_keys"]
    missing_keys = [key for key in required_keys if key not in plan]
    if missing_keys:
        return False, f"Plan with tool '{tool_name}' is missing required keys: {', '.join(missing_keys)}."
    
    if tool_name == "read_file":
        file_path = plan.get("file_path")
        if not file_path:
             return False, f"Plan with tool 'read_file' has an empty 'file_path'."
    
    return True, "Plan structure is valid."

# --- END UNIFIED DETERMINISTIC VALIDATION ---

# --- ROBUST AGENT LOOKUP ---
def get_agent_case_insensitive(agent_name: Optional[str]) -> Optional[Agent]:
    if not agent_name:
        return None
    
    if agent_name in agents:
        return agents[agent_name]
    
    for key, agent_instance in agents.items():
        if key.lower() == agent_name.lower():
            return agent_instance
            
    return None
# --- END ROBUST AGENT LOOKUP ---

#  --- PLAN EXECUTION (SANDBOX-AWARE) --- 
def execute_plan_step(plan: Dict[str, Any], project_root: Path) -> Tuple[bool, str, Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    """
    Executes a single, validated plan step *against a given project_root*.
    This project_root can be the REAL one, or a SANDBOX.
    
    Returns: (success, summary_string, structured_data, next_plan_override)
    """
    tool = plan.get("tool")
    structured_data = None 
    next_plan_override = None
    
    try:
        if tool == "read_file":
            file_path = project_root / plan["file_path"]
            content = read_file(file_path)
            if content.startswith("ERROR:"):
                return False, content, None, None
            
            specialist_agent_name = plan.get("specialist_agent")
            analyst = get_agent_case_insensitive(specialist_agent_name)
            if not analyst:
                return False, f"Specialist agent '{specialist_agent_name}' not found.", None, None
                
            analysis_prompt = f"--- FILE CONTENT ---\n{content}\n--- ANALYSIS TASK ---\n{plan['analysis_task']}\n--- RESPONSE FORMAT ---\nYou MUST respond with a JSON object containing a \"problem_statement\" key.\n"
            analysis_result_str = analyst.run(input=analysis_prompt)
            analysis_result = extract_json(analysis_result_str)
            
            if not analysis_result or "problem_statement" not in analysis_result:
                logger.warning(f"     Analyst failed to return valid JSON. Using raw output.")
                structured_data = [{"level": "note", "message": f"Analyst raw output: {analysis_result_str}"}]
                return True, "Analysis complete (raw output).", structured_data, None
                
            problem_statement = analysis_result.get('problem_statement', 'No problems found.')
            structured_data = [{"level": "note", "message": problem_statement}]
            return True, f"Analysis complete: {problem_statement[:100]}...", structured_data, None

        elif tool == "modify_file":
            file_path = project_root / plan["file_path"]
            
            #  --- "CODE-FIRST" AGENT FIX v2 ---
            # We now default to the *reliable* "Pro" programmer.
            specialist_agent_name = plan.get("specialist_agent", "ProgrammerAgent-Pro")
            programmer = get_agent_case_insensitive(specialist_agent_name) 
            # ---------------------------------
            
            if not programmer:
                return False, f"Agent '{specialist_agent_name}' not found for modify_file.", None, None
            
            logger.info(f"    Reading current content of {file_path} for {specialist_agent_name}...")
            current_content = read_file(file_path)
            
            if current_content.startswith("ERROR: File not found"):
                logger.warning(f"     File '{file_path}' not found. Treating 'modify_file' as 'create_file'.")
                current_content = "" # This is the correct logic
            elif current_content.startswith("ERROR:"):
                return False, current_content, None, None 
            
            modification_prompt = f"""--- CURRENT FILE CONTENT ---
{current_content}
--- MODIFICATION TASK ---
{plan['modification_task']}
--- RESPONSE ---
Respond with ONLY the new, full file content.
"""
            logger.info(f"    Calling {specialist_agent_name} to modify {file_path}...")
            try:
                prog_output = programmer.run(input=modification_prompt).strip()
                
                #  --- BRITTLE CHECK (FINAL FIX) ---
                # This logic is key: if the agent fails, we *don't* write the file
                # We REMOVED the 'or "{" in prog_output' check, which was brittle
                if (not prog_output 
                    or prog_output.startswith("Error:") 
                    or "client not configured" in prog_output
                    or "API returned no content" in prog_output):
                # ------------------------------------
                    logger.error(f"     {specialist_agent_name} FAILED. Output: {prog_output[:100]}...")
                    return False, f"{specialist_agent_name} failed to generate valid code: {prog_output[:100]}", None, None
                
                prog_output = re.sub(r"^```(python)?\n?", "", prog_output)
                prog_output = re.sub(r"\n?```$", "", prog_output).strip()
                
                logger.info(f"    Writing {specialist_agent_name} output to {file_path}...")
                write_file(file_path, prog_output)
                return True, f"Modification complete (via {specialist_agent_name}): {file_path}", None, None
            except Exception as e:
                logger.error(f"     Error during {specialist_agent_name} call or file write: {e}")
                traceback.print_exc()
                return False, f"Error during modification step: {e}", None, None

        elif tool == "create_file":
            file_path = project_root / plan["file_path"]
            create_file(file_path, plan["content"])
            return True, f"File created: {file_path}", None, None

        elif tool == "execute_shell":
            command = plan["command"]
            command = command.replace("$MISO_ROOT", str(project_root))
            
            logger.info(f"    Tactician executing: `{command}` in {project_root}")
            success, stdout, stderr = run_shell(command, cwd=project_root)
            output = f"{stdout}\n{stderr}".strip()
            
            if "python -m mypy" in command:
                parsed_result = parse_mypy_output(output)
                if parsed_result == "SUCCESS":
                    logger.info("     mypy check passed. No issues found.")
                    return True, "Mpy check passed. All issues resolved.", None, None
                else:
                    logger.info(f"     mypy check ran, issues found.")
                    return True, "Mpy check ran, issues found.", parsed_result, None
            elif "ruff check" in command:
                parsed_result = parse_ruff_output(output)
                if parsed_result == "SUCCESS":
                    logger.info("     ruff check passed. No issues found.")
                    return True, "Ruff check passed. All issues resolved.", None, None
                else:
                    logger.info(f"     ruff check ran, issues found.")
                    return True, "Ruff check ran, issues found.", parsed_result, None

            if success:
                return True, f"Command executed successfully. STDOUT: {stdout}", None, None
            
            logger.warning(f"     Command failed. STDOUT: {stdout} STDERR: {stderr}")
            
            # --- Ant Brain: "Missing Tool" Auto-Fix ---
            if "not found" in stderr or "No module named" in stderr:
                tool_name = ""
                if "No module named" in stderr:
                    match = re.search(r"No module named '([^']*)'", stderr)
                    if match: tool_name = match.group(1)
                elif "not found" in stderr:
                    match = re.search(r"(?:Command not found: |: command not found)(.+)", stderr)
                    if match: tool_name = shlex.split(match.group(1).strip())[0]
                
                if tool_name:
                    logger.info(f"     Ant Brain: Detected missing tool '{tool_name}'. Generating 'pip install' plan.")
                    next_plan_override = {"tool": "execute_shell", "command": f"pip install {tool_name}"}
                    return True, f"Diagnosed missing tool: {tool_name}", None, next_plan_override
            # --- End Ant Brain ---
            
            return False, f"Command failed. STDOUT: {stdout} STDERR: {stderr}", None, None

        elif tool == "halt":
             reason = plan.get("reason", "Planner requested halt.")
             logger.info(f"     PLANNER HALT: {reason}")
             return False, f"Planner requested halt: {reason}", None, None
        else:
            error_message = f"Unknown tool: {tool}"
            logger.error(f"     {error_message}")
            return False, error_message, None, None

    except Exception as e:
        logger.error(f"     CRITICAL ERROR during execution: {e}")
        traceback.print_exc()
        return False, f"Unhandled exception: {e}", None, None
# --- END: PLAN EXECUTION ---

#  --- "ELASTIC INTELLIGENCE" ARCHITECTURE --- 

# --- "Ant Brain"  (Plugin Loader) ---
DETERMINISTIC_FIXERS: Dict[str, Any] = {}

def load_fixer_plugins():
    """
    Dynamically loads "Ant Brain" fixers from the 'fixers' directory.
    This makes the "Ant Brain" scalable.
    """
    fixer_dir = Path(__file__).parent / "src/miso_engine/fixers"
    if not fixer_dir.exists():
        logger.warning("    No 'fixers' directory found. Ant Brain will be empty.")
        return
        
    for f in fixer_dir.glob("*.py"):
        if f.name == "__init__.py":
            continue
        
        module_name = f"src.miso_engine.fixers.{f.stem}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "ERROR_CODES") and hasattr(module, "generate_plan"):
                for code in module.ERROR_CODES:
                    DETERMINISTIC_FIXERS[code] = module.generate_plan
                logger.info(f"    Ant Brain: Loaded plugin '{f.name}' for codes {module.ERROR_CODES}")
            else:
                logger.warning(f"    Ant Brain: Plugin '{f.name}' is missing ERROR_CODES or generate_plan.")
        except Exception as e:
            logger.error(f"    Ant Brain: Failed to load plugin {f.name}: {e}")

def deterministic_plan_router(errors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    The "Ant Brain" v3.
    Checks the plugin dispatch table for a known error and routes to its plan.
    """
    if not errors or not isinstance(errors, list):
        return None
        
    error = errors[0]
    code = error.get("code")
    message = error.get("message", "")
    
    # Find the fixer key
    fixer_key = code or ""
    if not fixer_key:
        # Fallback for non-error-code parsers
        if "Cannot find implementation or library stub" in message: fixer_key = "import-not-found"
        elif "Duplicate module named" in message or "Source file found twice" in message: fixer_key = "duplicate-module-named"
    
    # Look up the fixer function in our loaded plugins
    fixer_function = DETERMINISTIC_FIXERS.get(fixer_key)
    
    if fixer_function:
        logger.info(f"    Ant Brain: Routing error '{fixer_key}' to plugin.")
        return fixer_function(error)

    return None # No deterministic fix found

# --- "Mammal Brain"  (Cache) ---
def load_archivist_cache() -> Dict[str, Any]:
    """v1 Archivist: Loads a simple JSON cache."""
    try:
        with open("miso_archivist_cache.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {} # No cache yet

def save_to_archivist_cache(cache: Dict[str, Any], error_key: str, plan: Dict[str, Any]):
    """v1 Archivist: Saves a successful plan to the cache."""
    cache[error_key] = plan
    with open("miso_archivist_cache.json", 'w') as f:
        json.dump(cache, f, indent=2)

def invalidate_archivist_cache(cache: Dict[str, Any], error_key: str):
    """v1 Archivist: Removes a known-bad plan from the cache."""
    if error_key in cache:
        logger.warning(f"    INVALIDATING CACHE for error: '{error_key[:50]}...'")
        del cache[error_key]
        with open("miso_archivist_cache.json", 'w') as f:
            json.dump(cache, f, indent=2)

def query_archivist(error_key: str, cache: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """v1 Mid-Brain: Checks the simple cache for a known fix."""
    return cache.get(error_key)

# --- "Lizard Brain"  (Context Isolator) ---
class ImportFinder(ast.NodeVisitor):
    """
    Uses the AST to find all imported modules.
    This is our robust "Lizard Brain" Context Isolator.
    """
    def __init__(self):
        self.imported_modules = set()
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imported_modules.add(alias.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if node.module:
            self.imported_modules.add(node.module)
        self.generic_visit(node)

def get_relevant_files_for_error(error_dict: Dict[str, Any], project_root: Path) -> List[str]:
    """
    Analyzes an error and finds all files relevant to fixing it using the AST.
    """
    relevant_files = set()
    error_file_path_str = error_dict.get("file_path")
    
    if not error_file_path_str:
        return [] # Can't do anything
        
    error_file_path = Path(error_file_path_str)
    relevant_files.add(error_file_path_str)
    
    content = read_file(project_root / error_file_path)
    if content.startswith("ERROR:"):
        return list(relevant_files)

    # 2. Add all imported files
    try:
        tree = ast.parse(content)
        finder = ImportFinder()
        finder.visit(tree)
        
        for module_name in finder.imported_modules:
            if not module_name:
                continue
            
            # Handle relative imports
            if module_name.startswith("."):
                module_path_base = (error_file_path.parent / module_name.lstrip('.'))
                py_file = module_path_base.with_suffix('.py')
                if (project_root / py_file).exists():
                    relevant_files.add(str(py_file))
            # Handle absolute imports
            else:
                parts = module_name.split('.')
                base_module_name = parts[0]
                
                # Check for sibling modules
                rel_py_file_str = str(error_file_path.parent / f"{base_module_name}.py")
                if (project_root / rel_py_file_str).exists():
                    relevant_files.add(rel_py_file_str)
                
                # Check for src/ modules
                src_py_file_str = f"src/{base_module_name}/__init__.py"
                if (project_root / src_py_file_str).exists():
                    relevant_files.add(src_py_file_str)
                    
        logger.info(f"    Lizard Brain (Isolator): Found relevant files: {relevant_files}")
        return list(relevant_files)

    except Exception as e:
        logger.warning(f"    Lizard Brain (Isolator): Failed to parse AST: {e}")
        return list(relevant_files) # Return at least the error file

# --- "Primate/Human Brain" / (TDD Sandbox) ---
def verify_plan_in_sandbox(
    plan: Dict[str, Any], 
    test_command: str, 
    error_to_fix: Dict[str, Any], # <--  Pass in the original error
    relevant_files: List[str], 
    project_root: Path
) -> bool:
    """
    Verifies a plan in a temporary sandbox.
    Returns True if the plan *resolves the specific error*.
    """
    sandbox_dir = tempfile.mkdtemp()
    sandbox_path = Path(sandbox_dir)
    logger.info(f"    VERIFY: Creating sandbox at {sandbox_dir}")
    
    original_error_message = error_to_fix.get("message", "")
    
    try:
        # 1. Copy relevant files to sandbox
        for file_str in relevant_files:
            source_path = project_root / file_str
            dest_path = sandbox_path / file_str
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path.exists():
                shutil.copy(source_path, dest_path)
            else:
                logger.warning(f"    VERIFY: Source file {source_path} not found for sandbox.")
                
        # --- Symlink venv (High-Fidelity Sandbox) ---
        venv_path = os.environ.get("VIRTUAL_ENV")
        if venv_path:
            sandbox_venv_path = sandbox_path / "venv"
            os.symlink(venv_path, sandbox_venv_path)
            logger.info(f"    VERIFY: Symlinked venv to {sandbox_venv_path}")

        # 2. Execute the plan in the sandbox
        logger.info(f"    VERIFY: Executing candidate plan in sandbox...")
        plan_success, _, _, _ = execute_plan_step(plan, sandbox_path)
        
        if not plan_success:
            logger.warning("    VERIFY: Candidate plan failed to *execute* in sandbox. Rejecting.")
            return False
            
        # 3. Run the test command in the sandbox
        logger.info(f"    VERIFY: Running test command: `{test_command}` in sandbox...")
        
        #  --- TDD FIX: We must use the REAL project root for mypy to resolve paths ---
        # But we run the command from the SANDBOX to use the modified files
        test_command_sandboxed = test_command.replace("$MISO_ROOT", str(project_root)) 
        
        test_success, test_stdout, test_stderr = run_shell(test_command_sandboxed, cwd=sandbox_path) 
        test_output = f"{test_stdout}\n{test_stderr}".strip()
        
        # 4. Check the results
        parsed_result = None
        if "mypy" in test_command:
            parsed_result = parse_mypy_output(test_output)
        elif "ruff" in test_command:
            parsed_result = parse_ruff_output(test_output)
        
        # ---  "Smart" TDD Verification ---
        if parsed_result == "SUCCESS":
            logger.info("    VERIFY:  Test PASSED (SUCCESS). Plan is VERIFIED.")
            return True
        
        if isinstance(parsed_result, list):
            # The test *failed*, but did it fix our *original* error?
            error_is_still_present = False
            for new_error in parsed_result:
                if new_error.get("message") == original_error_message:
                    error_is_still_present = True
                    break
            
            if not error_is_still_present:
                logger.info("    VERIFY:  Test PASSED (Original error is gone). Plan is VERIFIED.")
                return True
        
        # If we get here, the test failed AND the original error is still there.
        logger.warning(f"    VERIFY:  Test FAILED. Plan is REJECTED. Output: {test_output[:200]}")
        return False
        
    except Exception as e:
        logger.error(f"    VERIFY:  CRITICAL error in sandbox: {e}")
        return False
    finally:
        # 5. Clean up
        logger.info(f"    VERIFY: Cleaning up sandbox {sandbox_dir}")
        shutil.rmtree(sandbox_dir)
# --- END: TDD SANDBOX VERIFICATION ---

#  --- "ELASTIC INTELLIGENCE" ORCHESTRATOR (v4.0 - TDD-First Cache) --- 
def run_miso_system(problem_statement: str):
    """Initializes and runs the MISO V63 TDD system."""
    print(f" MISO V63 TDD System Initialized.")
    project_root = Path(os.getcwd())
    
    # ---  Load "Ant Brain" Plugins ---
    load_fixer_plugins()
    # ---

    #  --- AGENT FIX: Add new "Pro" programmer ---
    agent_names = [
        "PlannerAgent-Lite", 
        "PlannerAgent-Pro", 
        "ProgrammerAgent",
        "ProgrammerAgent-Pro", # <-- NEW AGENT
        "AuditorGeneralAgent", 
    ]
    # ---------------------------------------------
    global agents
    try:
        if not os.environ.get("GOOGLE_API_KEY"):
                print(" WARNING: No Google API key found. Human Brain will fail.")
        agents = { name: Agent(persona_name=name) for name in agent_names }
        print("    All agents initialized.")
    except Exception as e:
        print(f" CRITICAL: Failed to initialize agents: {e}. Halting.")
        traceback.print_exc()
        return

    # --- TDD State Initialization ---
    current_refinement = problem_statement
    last_error_key_for_planner = None # For stagnation
    
    plan = None # The plan to be executed this loop
    
    analysis_tool = "mypy" 
    structured_errors = None
    
    archivist_cache = load_archivist_cache()
    
    last_error_key_for_cache = None 
    plan_was_from_cache = False  
    
    #  --- "CODE-FIRST" STAGNATION FIX v3 ---
    # We now track the *plan itself* to avoid simple error key collisions
    last_deterministic_plan_json = None 
    # -----------------------------------------
    
    # Loop limit
    for i in range(1, 101):
        print(f"\n--- MISO LOOP {i} ---")
        
        # ---  TDD FIX: Define the *default* test command ---
        test_command_for_loop = f"python -m {analysis_tool} $MISO_ROOT"
        error_to_fix = {} # The specific error we are trying to fix this loop

        # --- 1. PLAN GENERATION (The Cascade) ---
        if not plan:
            
            # ---  "Analyze-First" Bootstrap ---
            if i == 1 and not structured_errors and not current_refinement.startswith("REFINEMENT:"):
                print("     INFO - Ant Brain: Loop 1. No structured errors. Forcing analysis.")
                plan = {"tool": "execute_shell", "command": test_command_for_loop}
            
            # --- 1A. ANT BRAIN (Code: Fallbacks) ---
            elif current_refinement in [
                "Previous step completed successfully. Re-running analysis.",
                "Previous plan failed validation. Re-running analysis."
            ]:
                print("     INFO - Ant Brain: Detected fallback trigger. Generating default mypy plan.")
                plan = {"tool": "execute_shell", "command": test_command_for_loop}
                structured_errors = None # Clear errors
            
            # --- 1B. LIZARD BRAIN (Code: Router) ---
            elif structured_errors:
                print(f"    INFO: Have {len(structured_errors)} structured error(s).")
                error_to_fix = structured_errors[0] # ISOLATE
                err_msg = error_to_fix.get('message', 'Unknown Error')
                err_path = error_to_fix.get('file_path', '')
                err_line = error_to_fix.get('line', '')
                current_refinement = f"REFINEMENT: {err_path}:{err_line}: {err_msg}"
                
                # ---  TDD FIX: Create ATOMIC test command ---
                if err_path:
                    test_command_for_loop = f"python -m {analysis_tool} {err_path}"
                    logger.info(f"    Atomic TDD: Test command set to: {test_command_for_loop}")

                #  --- TDD-FIRST CACHE FIX: We must clear the 'plan_was_from_cache'
                # flag *before* we try to get a new plan.
                plan_was_from_cache = False
                
                # Check "Stagnation" (Mammal Brain failure)
                # This logic is now only for *verified* cached plans that fail
                if current_refinement == last_error_key_for_cache:
                    print("     INFO - Mammal Brain: CACHE INVALIDATION. A previously *verified* plan has failed. Re-learning.")
                    invalidate_archivist_cache(archivist_cache, last_error_key_for_cache)
                
                #  --- STAGNATION FIX v3 ---
                # 1. ALWAYS try the "Code-First" router first.
                candidate_plan = deterministic_plan_router(structured_errors)
                
                if candidate_plan:
                    logger.info("    INFO - Lizard Brain: Plugin found a candidate plan.")
                    candidate_plan_json = json.dumps(candidate_plan)
                    
                    # 2. Check if this *exact plan* has already failed
                    if candidate_plan_json == last_deterministic_plan_json:
                        # We are trying to run the same "Lizard" plan that just failed.
                        print("     INFO - Lizard Brain: STAGNATION. Deterministic plan failed to fix the error. Escalating.")
                        # Do not set `plan`. Let it escalate.
                    else:
                        # This is a new deterministic plan. Use it.
                        print("     INFO - Lizard Brain: Found new deterministic plan. Applying.")
                        plan = candidate_plan
                        # We track the *plan*, not the error key
                        last_deterministic_plan_json = candidate_plan_json 
                # If `candidate_plan` is None, we just fall through to Mammal Brain.
                # --- END STAGNATION FIX ---
            
            #  --- TDD-FIRST ORCHESTRATOR REFACTOR --- 
            
            # --- 1C. MAMMAL BRAIN (Cache) ---
            if not plan:
                if not current_refinement.startswith("REFINEMENT:"):
                    # This is a fallback, not a plan to be verified
                    print(f"    INFO - Ant Brain: No plan and no errors. Forcing analysis.")
                    plan = {"tool": "execute_shell", "command": test_command_for_loop}
                else:
                    print(f"    - Pursuing Task Focus: '{current_refinement[:200]}...'")
                    cached_plan = query_archivist(current_refinement, archivist_cache)
                    
                    if cached_plan:
                        print(f"     INFO - Mammal Brain: Found cached plan. Sending to verification...")
                        plan = cached_plan # Set the *candidate* plan
                        plan_was_from_cache = True
                    
                    # --- 1D/1E. PRIMATE/HUMAN BRAINS (Escalation) ---
                    else:
                        print(f"    INFO - Primate Brain: No deterministic or cached plan. Calling local LLM.")
                        
                        # --- Get Context ---
                        relevant_files = set()
                        if structured_errors:
                             relevant_files.update(get_relevant_files_for_error(structured_errors[0], project_root))
                        
                        relevant_file_contents = {}
                        for f_path in relevant_files:
                            content = read_file(project_root / f_path)
                            if not content.startswith("ERROR:"):
                                 relevant_file_contents[f_path] = content
                        
                        plan_prompt = f"""<TEST_COMMAND>
{test_command_for_loop}
</TEST_COMMAND>
<EXPECTED_FAILURE>
{expected_failure}
</EXPECTED_FAILURE>
<RELEVANT_FILES>
{json.dumps(relevant_file_contents, indent=2)}
</RELEVANT_FILES>
"""
                        # --- End Get Context ---

                        try: # --- Try Einstein-Lite ---
                            lite_planner = get_agent_case_insensitive("PlannerAgent-Lite")
                            if not lite_planner: raise RuntimeError("PlannerAgent-Lite not found")
                            
                            plan_str = lite_planner.run(input=plan_prompt)
                            plan = extract_json(plan_str) # Set the *candidate* plan
                            
                            if not plan:
                                 raise ValueError(f"Planner-Lite returned invalid/empty JSON. Raw: {plan_str[:200]}")

                        except TimeoutError as e:
                            print(f"     Primate Brain (Einstein-Lite) FAILED: {e}. Escalating to Pro.")
                            plan = None
                        except Exception as e:
                            print(f"     Primate Brain (Einstein-Lite) FAILED: {e}. Escalating to Pro.")
                            plan = None 

                        # --- 1E. HUMAN BRAIN (Einstein-Pro) ---
                        if not plan:
                            print(f"    INFO - Human Brain: Escalating to paid LLM.")
                            
                            stagnation_warning = ""
                            if current_refinement == last_error_key_for_planner:
                                 print("     Refinement stagnated. Retrying with warning.")
                                 stagnation_warning = "\n\n<STAGNATION_WARNING>WARNING: Your previous plan failed. You MUST NOT generate the same plan again.</STAGNATION_WARNING>"
                            
                            tool_hint = """
<TOOL_HINT>
IMPORTANT: If you generate a "modify_file" plan, you MUST set the "specialist_agent" key to "ProgrammerAgent-Pro".
</TOOL_HINT>
"""
                            plan_prompt_pro = f"{plan_prompt}\n{tool_hint}\n{stagnation_warning}\n" 
                            
                            try:
                                pro_planner = get_agent_case_insensitive("PlannerAgent-Pro")
                                if not pro_planner: raise RuntimeError("PlannerAgent-Pro not found")
                                
                                plan_str = pro_planner.run(input=plan_prompt_pro)
                                if "429" in plan_str or "quota" in plan_str.lower():
                                    raise Exception("API Quota Error: 429")
                                plan = extract_json(plan_str) # Set the *candidate* plan
                                if not plan: 
                                    raise ValueError(f"Planner-Pro returned invalid/empty JSON. Raw: {plan_str[:200]}")

                            except Exception as e:
                                print(f"     Planner-Pro failed: {e}. Halting loop.")
                                traceback.print_exc()
                                plan = None 
                                continue
            
            # ---  TDD-FIRST VERIFICATION BLOCK ---
            # All non-Lizard-Brain plans MUST be verified.
            # This block now handles Mammal, Primate, AND Human brains.
            
            if plan and plan.get("tool") not in ["execute_shell", "halt"] and not deterministic_plan_router([error_to_fix]):
                # (We skip verification for shell commands and Lizard-Brain plans)
                
                print(f"    INFO - TDD Sandbox: Verifying candidate plan from {'Mammal' if plan_was_from_cache else 'Primate/Human'} Brain...")
                
                # We need relevant_files *again* in case we loaded from cache
                relevant_files = set()
                if structured_errors:
                        relevant_files.update(get_relevant_files_for_error(structured_errors[0], project_root))

                is_verified = verify_plan_in_sandbox(plan, test_command_for_loop, error_to_fix, list(relevant_files), project_root)
                
                if not is_verified:
                    print(f"     INFO - TDD Sandbox: Plan FAILED verification. Discarding.")
                    if plan_was_from_cache:
                        print("     INFO - Mammal Brain: Cached plan FAILED verification. INVALIDATING.")
                        invalidate_archivist_cache(archivist_cache, current_refinement)
                    
                    last_error_key_for_planner = current_refinement # Mark stagnation for planner
                    plan = None # Clear the bad plan
                    continue # Go to the next loop (which will escalate)
                
                else:
                    print(f"     INFO - TDD Sandbox: Plan VERIFIED.")
                    if not plan_was_from_cache:
                        print("     INFO - Mammal Brain: Promoting new plan to cache.")
                        save_to_archivist_cache(archivist_cache, current_refinement, plan)
                    # Set the key to track if this *verified* plan fails later
                    last_error_key_for_cache = current_refinement

            # --- END: TDD-FIRST VERIFICATION BLOCK ---

        
        # --- 2. Plan Validation (Structure Check) ---
        if not plan:
            logger.error("    FATAL: Plan is None after generation phase. This should not happen.")
            current_refinement = "Previous plan failed validation. Re-running analysis."
            continue

        manifest_files = json.loads(get_file_manifest(project_root))
        is_valid, reason = validate_plan(plan, manifest_files) 
        
        if not is_valid:
            print(f"     PLAN FAILED VALIDATION: {reason}.")
            print(f"    Forcing re-analysis...")
            current_refinement = "Previous plan failed validation. Re-running analysis."
            plan = None
            structured_errors = None
            continue
            
        print("     Plan passed all deterministic validation.")
        
        # --- 3. Plan Execution (COMMIT) ---
        task_succeeded, exec_summary, structured_errors, next_plan_override = execute_plan_step(plan, project_root)
        
        if next_plan_override:
            print(f"     INFO - Ant Brain: Execution override. Setting next plan.")
            plan = next_plan_override
            current_refinement = f"Deterministic fix: {exec_summary}"
            continue

        if not task_succeeded:
            if "Planner requested halt" in exec_summary:
                print(f"     Planner requested halt. Halting loop.")
            else:
                print(f"     Task failed during execution ({exec_summary}). Halting loop.")
            break

        # --- 4. Post-Execution Refinement ---
        print("\n    --- Analyzing Results ---")
        if structured_errors and isinstance(structured_errors, list):
            # We have structured errors from mypy/ruff
            err = structured_errors[0]
            current_refinement = f"REFINEMENT: {err.get('file_path', '')}:{err.get('line', '')}: {err.get('message', 'Complex error')}"
        else:
            # No structured data == SUCCESS
            print(f"     Simple task step complete: {exec_summary}")
            current_refinement = "Previous step completed successfully. Re-running analysis."
        
        plan = None # Clear plan for next loop
        
        # --- COOLDOWN ---
        print("\n    ...cooling down for 3 seconds to respect rate limits...")
        time.sleep(3)
        # --- END COOLDOWN ---

# --- Main Execution Block ---
def main():
    parser = argparse.ArgumentParser(description="MISO V63 TDD System")
    parser.add_argument("--prompt-file", type=str, help="Path to a file containing the prompt.")
    args = parser.parse_args()
    
    if args.prompt_file:
        print(f" Reading prompt from file: {args.prompt_file}")
        try:
            with open(args.prompt_file, 'r', encoding='utf-8') as f: problem_statement = f.read().strip()
            if not problem_statement: print(" Error: Prompt file is empty."); return
            run_miso_system(problem_statement)
            print("\n MISO Task Concluded (File Mode).")
        except FileNotFoundError:
            #  --- TYPO FIX ---
            print(f" Error: Prompt file not found: '{args.prompt_file}'")
            # ------------------
        except Exception as e: print(f"\n CRITICAL FILE MODE ERROR: {e}"); traceback.print_exc()
    else:
        main_interactive_shell()


def main_interactive_shell():
    """Runs the MISO TDD interactive shell."""
    print(" MISO V63 TDD System Initialized.")
    print("    Enter task or 'exit'.")
    
    while True:
        print("\n" + "="*80)
        try:
            problem_statement = input("[MISO Task]: ")
            if problem_statement.lower() == 'exit': print(" MISO Shutting Down."); break
            if not problem_statement: continue
            
            run_miso_system(problem_statement)

        except KeyboardInterrupt: print("\n MISO Shutting Down."); break
        except Exception as e: print(f"\n SHELL ERROR: {e}"); traceback.print_exc(); print("Restarting...")
        print("\n MISO Task Concluded.")

if __name__ == "__main__":
    main()
