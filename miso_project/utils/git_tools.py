import subprocess
import os
import random
import string

# --- (THE FIX: This path is now correct) ---
# This file is in 'miso_project/utils/'. We want the Git root, 'MISO-Phoenix/'.
GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _run_git_command(command: list) -> (bool, str):
    """A simple wrapper to run a git command from the repo root."""
    try:
        process = subprocess.run(
            ["git"] + command,
            capture_output=True,
            text=True,
            check=True,
            cwd=GIT_ROOT_DIR # Run all git commands from the root
        )
        return True, process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"🚨 Git command failed: {' '.join(command)}")
        print(f"   Error: {e.stderr}")
        return False, e.stderr
    except FileNotFoundError:
        print("🚨 Git command not found. Is git installed?")
        return False, "git not found"

def get_current_branch() -> str:
    success, output = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    return output if success else "main"

def create_new_branch(base_branch: str = "main") -> str | None:
    _run_git_command(["checkout", base_branch])
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    branch_name = f"feature/miso-fix-{suffix}"
    success, _ = _run_git_command(["checkout", "-b", branch_name])
    if success:
        print(f"✅ Git: Created and checked out new branch: {branch_name}")
        return branch_name
    else:
        return None

def commit_plan(plan: list, message: str, workspace_dir: str):
    print(f"✅ Git: Applying plan and committing to branch...")
    
    # 1. Apply the plan to the REAL filesystem
    try:
        for step in plan:
            op = step.get('op')
            if op == 'analysis':
                print(f"   -> 👨‍🔬 ANALYSIS: {step.get('analysis')}")
                continue
            
            # --- (THE FIX: 'workspace_dir' is now relative to GIT_ROOT_DIR) ---
            path = os.path.join(GIT_ROOT_DIR, workspace_dir, step.get('path'))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            if op == 'create_file' or op == 'modify_file':
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(step.get('content', ''))
                print(f"   -> Wrote {path}")
            elif op == 'delete_file':
                if os.path.exists(path):
                    os.remove(path)
                    print(f"   -> Deleted {path}")
    except Exception as e:
        print(f"🚨 Git: Fatal error during file application: {e}")
        return False

    # 2. Stage and Commit the changes
    _run_git_command(["add", "."])
    success, _ = _run_git_command(["commit", "-m", message])
    if success:
        print(f"   -> Committed: {message}")
    return success

def abandon_changes(original_branch: str):
    print(f"⚠️ Git: Abandoning all changes.")
    _run_git_command(["checkout", original_branch, "--force"])

def push_branch(branch_name: str):
    print(f"🚀 Git: Pushing completed work to origin...")
    success, output = _run_git_command(["push", "-u", "origin", branch_name])
    if success:
        print(f"   -> {output}")
        print(f"✅ Git: Branch {branch_name} pushed. A Pull Request is ready for review.")
    return success
