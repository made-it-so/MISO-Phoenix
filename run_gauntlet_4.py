#!/usr/bin/env python3

"""
MISO Gauntlet Level 4: "Cost vs. Quality" Test Runner

This simple, paste-safe script:
1. Sets up the workspace with a simple 'mypy' error.
2. Runs the Triage Agent.
3. The Triage Agent MUST select the 'Lizard' brain.
4. The 'Lizard' brain MUST successfully fix the bug.
"""

import os
import shutil
import subprocess
import sys
import textwrap
import git

# --- Define Paths ---
GIT_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.join(GIT_ROOT, "miso_project")
WORKSPACE_DIR = os.path.join(PROJECT_DIR, "workspace")

# --- Test File Content ---

# This file has a simple mypy error (missing type hints)
STATS_PY_MYPY_ERROR = textwrap.dedent('''
def calculate_mean(l):
    """Calculates the mean of a list."""
    if not l:
        return 0.0
    return sum(l) / len(l)
''')

# This test file will PASS pytest but FAIL mypy
TEST_STATS_PY_MYPY_ERROR = textwrap.dedent('''
from stats import calculate_mean
import pytest

def test_mean_happy_path():
    assert calculate_mean([1.0, 2.0, 3.0]) == 2.0

def test_mean_single_item():
    assert calculate_mean([5.0]) == 5.0

def test_mean_empty_list():
    assert calculate_mean([]) == 0.0
''')

def p_info(msg):
    """Prints an info message."""
    print(f"🚀 [INFO] {msg}")

def p_ok(msg):
    """Prints a success message."""
    print(f"✅ [OK] {msg}")

def p_warn(msg):
    """Prints a warning message."""
    print(f"⚠️ [WARN] {msg}")

def p_err(msg):
    """Prints an error message and exits."""
    print(f"🔥 [ERROR] {msg}", file=sys.stderr)
    sys.exit(1)

def write_file(filepath, content):
    """Helper to write content to a file, creating dirs if needed."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        p_info(f"  > Wrote {filepath}")
    except IOError as e:
        p_err(f"Error: Could not write file {filepath}. {e}")

def nuke_workspace():
    """Cleans the workspace directory, leaving __init__.py."""
    p_info("Nuking workspace for a clean test...")
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR)
        return
        
    for f in os.listdir(WORKSPACE_DIR):
        if f == "__init__.py":
            continue
        path = os.path.join(WORKSPACE_DIR, f)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as e:
            p_warn(f"Could not clean workspace file {path}: {e}")

def run_agent(part_name: str):
    """Runs the MISO agent as a subprocess."""
    
    agent_cmd = [
        sys.executable,
        os.path.join(PROJECT_DIR, "miso_agent.py"),
        "--git-root", GIT_ROOT,
        "--workspace", WORKSPACE_DIR,
    ]
    
    # Set env var to suppress Google's FutureWarning
    proc_env = os.environ.copy()
    proc_env["PYTHONPATH"] = PROJECT_DIR # CRITICAL: Set PYTHONPATH
    proc_env["PYTHONWARNINGS"] = "ignore:You are using a Python version"

    try:
        p_info(f"Running Triage Agent for {part_name}: {' '.join(agent_cmd)}")
        # We must stream the output
        with subprocess.Popen(agent_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='ignore', env=proc_env) as proc:
            for line in proc.stdout:
                print(line, end='')
        
        # We check the return code here. 0 is success.
        if proc.returncode != 0:
             p_warn(f"Agent run {part_name} finished with exit code {proc.returncode}.")
             return False # The agent itself failed
        
        p_ok(f"Agent run {part_name} complete.")
        return True # The agent reported success
        
    except Exception as e:
        p_err(f"Agent run {part_name} failed critically: {e}")
        return False

def setup_git_repo():
    """Initializes a clean Git repo in the root for the agent to use."""
    p_info("Setting up clean Git repository...")
    try:
        if os.path.exists(os.path.join(GIT_ROOT, ".git")):
            p_info("Git repo already exists. Cleaning...")
            repo = git.Repo(GIT_ROOT)
            try:
                repo.git.checkout('main', f=True)
            except git.GitCommandError:
                p_warn("Could not checkout main. Creating...")
                repo.git.checkout('-b', 'main')
        else:
            p_info("Initializing new Git repository...")
            repo = git.Repo.init(GIT_ROOT)
            repo.git.checkout('-b', 'main')
        
        # Ensure user config is set for commits
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "MisoAgent")
            cw.set_value("user", "email", "miso@agent.ai")
        
        p_ok("Git repository is ready.")

    except Exception as e:
        p_err(f"Failed to set up Git repository: {e}")


def main():
    p_info("--- [REBUILD_MISO] Running Test (Gauntlet Level 4): 'Cost vs. Quality' ---")

    # --- 1. SET UP GIT ---
    setup_git_repo()

    # --- 2. SET UP WORKSPACE ---
    nuke_workspace()
    print("Writing test files for Level 4 (simple 'mypy' error)...")
    write_file(os.path.join(WORKSPACE_DIR, "stats.py"), STATS_PY_MYPY_ERROR)
    write_file(os.path.join(WORKSPACE_DIR, "test_stats.py"), TEST_STATS_PY_MYPY_ERROR)
    
    # --- 3. CREATE INITIAL COMMIT ---
    # The agent needs an initial commit to diff against
    try:
        repo = git.Repo(GIT_ROOT)
        repo.git.add(A=True)
        # Check if there are changes to commit
        if repo.is_dirty(index=True, working_tree=False):
            repo.index.commit("Initial commit with Level 4 test files")
            p_ok("Created initial commit for test.")
        else:
            p_ok("No changes to commit. Workspace is clean.")
    except Exception as e:
        p_warn(f"Could not create initial commit (might be no changes): {e}")

    # --- 4. RUN AGENT ---
    if run_agent("Gauntlet Level 4"):
        p_info("\n[REBUILD_MISO] SUCCESS: Full Gauntlet Level 4 test is complete.")
        p_info("To verify, check your git log for the new branch:")
        p_info("  git log --graph --oneline --all")
    else:
        p_err("\n[REBUILD_MISO] FAILED: The agent mission failed.")


if __name__ == "__main__":
    main()
