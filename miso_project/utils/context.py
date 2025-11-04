import re
import os

IMPORT_REGEX = re.compile(r"^\s*(?:from|import)\s+([a-zA-Z0-9_.]+)", re.MULTILINE)
# (THE FIX: This path is now correct, relative to this file)
GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKSPACE_DIR = os.path.join(GIT_ROOT_DIR, "miso_project", "workspace")

def _read_file_safe(path: str) -> str | None:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def find_module_path(base_path: str, module_name: str) -> str | None:
    module_parts = module_name.split('.')
    possible_path = os.path.join(base_path, *module_parts)
    if os.path.exists(possible_path + ".py"):
        return possible_path + ".py"
    if os.path.exists(os.path.join(possible_path, "__init__.py")):
        return os.path.join(possible_path, "__init__.py")
    return None

def generate_context_for_error(isolated_error: str) -> dict:
    print(f"🔬 CONTEXT: Generating smart context for error.")
    context = {}
    match = re.search(r"([^:]+?\.py):[\d+]:", isolated_error)
    if not match:
        return {} 
    
    # (THE FIX: This logic is now correct)
    abs_file_path = match.group(1)
    if not os.path.isabs(abs_file_path):
        abs_file_path = os.path.abspath(os.path.join(GIT_ROOT_DIR, abs_file_path))

    if not abs_file_path.startswith(WORKSPACE_DIR):
        # This error is not in our workspace, ignore it
        return {}

    rel_file_path = os.path.relpath(abs_file_path, WORKSPACE_DIR)
    
    primary_content = _read_file_safe(abs_file_path)
    if not primary_content:
        return {}
    context[rel_file_path] = primary_content # Use relative path
    
    imports = IMPORT_REGEX.findall(primary_content)
    for module_name in imports:
        if module_name in ["mypy", "pytest", "os", "re", "json"]:
            continue
        
        module_path_abs = find_module_path(WORKSPACE_DIR, module_name)
        if module_path_abs:
            module_path_rel = os.path.relpath(module_path_abs, WORKSPACE_DIR)
            if module_path_rel not in context:
                module_content = _read_file_safe(module_path_abs)
                if module_content:
                    print(f"   -> Found related file: {module_path_rel}")
                    context[module_path_rel] = module_content
    return context
