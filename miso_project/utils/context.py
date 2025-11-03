import re
import os

# Regex to find import statements
IMPORT_REGEX = re.compile(r"^\s*(?:from|import)\s+([a-zA-Z0-9_.]+)", re.MULTILINE)

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

    primary_file_path = match.group(1)
    
    primary_content = _read_file_safe(primary_file_path)
    if not primary_content:
        return {}
        
    context[primary_file_path] = primary_content
    
    imports = IMPORT_REGEX.findall(primary_content)
    
    for module_name in imports:
        if module_name in ["mypy", "pytest", "os", "re", "json"]:
            continue
            
        module_path = find_module_path("workspace", module_name)
        
        if module_path and module_path not in context:
            module_content = _read_file_safe(module_path)
            if module_content:
                print(f"   -> Found related file: {module_path}")
                context[module_path] = module_content
                
    config_content = _read_file_safe("mypy.ini")
    if config_content:
        context["mypy.ini"] = config_content

    return context
