import subprocess
import os

class ToolError(Exception):
    pass

def read_file(file_path: str) -> str:
    encodings_to_try = ['utf-8', 'utf-16', 'latin-1']
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ToolError(f"Could not read file {file_path} with tried encodings.")

def write_file(file_path: str, content: str):
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return f"Successfully wrote to {file_path}"

def patch_code(file_path: str, find_block: str, replace_with: str):
    original_content = read_file(file_path)
    if find_block not in original_content:
        raise ToolError("'find_block' not found.")
    new_content = original_content.replace(find_block, replace_with)
    write_file(file_path, new_content)
    return f"Successfully patched {file_path}."

def run_tests(test_command: str = "pytest"):
    result = subprocess.run(test_command, shell=True, capture_output=True, text=True)
    return f"Exit Code: {result.returncode}\nStdout:\n{result.stdout}\nStderr:\n{result.stderr}\n"

def list_files(directory: str = "."):
    tree = []
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in root or 'venv' in root or '.git' in root:
            continue
        level = root.replace(directory, '').count(os.sep)
        indent = ' ' * 4 * level
        tree.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            tree.append(f"{sub_indent}{f}")
    return "\n".join(tree)

def finish_milestone():
    """Signals that the current milestone is complete."""
    return "Milestone completed."

TOOL_MAP = {
    "read_file": read_file,
    "write_file": write_file,
    "patch_code": patch_code,
    "run_tests": run_tests,
    "list_files": list_files,
    "finish_milestone": finish_milestone,
}

TOOL_SIGNATURES = {
    "read_file": "read_file(file_path: str)",
    "write_file": "write_file(file_path: str, content: str)",
    "patch_code": "patch_code(file_path: str, find_block: str, replace_with: str)",
    "run_tests": "run_tests(test_command: str = 'pytest')",
    "list_files": "list_files(directory: str = '.')",
    "finish_milestone": "finish_milestone()",
}
