import os
import shutil
import tempfile
import subprocess

# (THE FIX: This path is now correct, relative to this file)
GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class Sandbox:
    def __init__(self, base_workspace_path: str):
        self.base_path = os.path.abspath(base_workspace_path)
        self.temp_dir = tempfile.mkdtemp()
        self.sandbox_path = os.path.join(self.temp_dir, "workspace")

    def __enter__(self):
        try:
            shutil.copytree(self.base_path, self.sandbox_path)
        except FileNotFoundError:
            os.makedirs(self.sandbox_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.temp_dir)

    def apply_plan(self, plan: list):
        for step in plan:
            op = step.get('op')
            if op == 'analysis':
                continue
            path = os.path.join(self.sandbox_path, step.get('path'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if op == 'create_file' or op == 'modify_file':
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(step.get('content', ''))
            elif op == 'delete_file':
                if os.path.exists(path):
                    os.remove(path)
            else:
                raise ValueError(f"Invalid plan operation: {op}")

    def run_command(self, command: str, cwd: str):
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=60, cwd=cwd
            )
            full_output = result.stdout + result.stderr
            return result.returncode, full_output
        except Exception as e:
            return -1, f"Command execution failed: {e}"
