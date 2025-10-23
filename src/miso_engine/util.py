import os
import re
import json
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List

def extract_json(text: str) -> Dict[str, Any] | None:
    """Extracts the first valid JSON object from a string (e.g., in markdown)."""
    # Look for JSON block in markdown
    match = re.search(r"```(json)?\n(\{.*?\})\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(2)
    else:
        # Look for the first '{' and last '}'
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1:
            # Fallback: check for single-line JSON
            match_line = re.search(r"(\{.*\})", text)
            if not match_line:
                return None
            json_str = match_line.group(1)
        else:
            json_str = text[start:end+1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Fallback for escaped strings
        try:
            return json.loads(json_str.replace('\\n', '\n').replace('\\"', '"'))
        except Exception:
            print(f"UTIL: Failed to parse JSON: {json_str}")
            return None

def run_shell(command: str, cwd: Path | str = ".") -> Tuple[bool, str, str]:
    """Runs a shell command and returns (success, stdout, stderr)."""
    try:
        # Use shlex.split to handle quoted arguments correctly
        args = shlex.split(command)

        # Set MISO_ROOT env var for subprocess
        env = os.environ.copy()
        if "MISO_ROOT" not in env:
             # Assumes this util.py is in src/miso_engine, so root is 3 levels up
             env["MISO_ROOT"] = str(Path(__file__).parent.parent.parent.resolve())

        process = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,  # 60-second timeout
            env=env
        )
        success = process.returncode == 0
        return success, process.stdout.strip(), process.stderr.strip()
    except FileNotFoundError:
        return False, "", f"Command not found: {args[0]}"
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out."
    except Exception as e:
        return False, "", f"Shell execution error: {e}"

def read_file(file_path: Path) -> str:
    """Reads a file and returns its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"ERROR: File not found at {file_path}"
    except Exception as e:
        return f"ERROR: Could not read file: {e}"

def write_file(file_path: Path, content: str):
    """Writes content to a file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"ERROR: Could not write file {file_path}: {e}")

def create_file(file_path: Path, content: str):
    """Creates a new file with content."""
    write_file(file_path, content)

def get_file_manifest(root_dir: Path) -> str:
    """Generates a JSON string of the file manifest, ignoring common junk."""
    ignore_dirs = {'.git', '__pycache__', 'venv', '.vscode', 'node_modules'}
    ignore_files = {'.gitignore', '.DS_Store'}

    manifest: List[str] = []

    for path in root_dir.rglob('*'):
        if path.is_file():
            # Check if any part of the path is in ignore_dirs
            if any(part in ignore_dirs for part in path.parts):
                continue
            # Check if the file itself is in ignore_files
            if path.name in ignore_files:
                continue

            relative_path = path.relative_to(root_dir)
            manifest.append(str(relative_path.as_posix())) # Use / separator

    return json.dumps(manifest, indent=2)
