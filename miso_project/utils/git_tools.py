import git
import re
import subprocess
from datetime import datetime

def get_repo(git_root_dir: str) -> git.Repo:
    '''
    Initializes and returns a Git.Repo object from the specified root directory.
    '''
    try:
        repo = git.Repo(git_root_dir)
        return repo
    except git.InvalidGitRepositoryError:
        print(f"Error: Path '{git_root_dir}' is not a valid Git repository.")
        exit(1)

def create_branch(repo: git.Repo, persona_name: str) -> str:
    '''
    Creates a new branch based on the persona name and a timestamp.
    '''
    # Sanitize persona name for branch
    branch_name_safe = re.sub(r'[^a-zA-Z0-9]', '-', persona_name.lower())
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    branch_name = f"miso-fix/{branch_name_safe}-{timestamp}"
    
    try:
        # Create and checkout the new branch
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        print(f"Git: Created and checked out new branch: {branch_name}")
        return branch_name
    except Exception as e:
        print(f"Error creating git branch: {e}")
        # Fallback: if branch exists, just check it out
        try:
            repo.git.checkout(branch_name)
            print(f"Git: Checked out existing branch: {branch_name}")
            return branch_name
        except git.GitCommandError as ge:
            print(f"FATAL: Could not create or checkout branch {branch_name}. {ge}")
            exit(1)

def commit_changes(repo: git.Repo, workspace_dir: str, persona_name: str) -> bool:
    '''
    Commits all changes in the workspace directory.
    '''
    try:
        # Stage all changes in the workspace.
        repo.git.add(workspace_dir)
        
        # CRITICAL FIX: Use 'git status --porcelain' for a reliable change check
        # This bypasses any potential gitpython caching issues.
        result = subprocess.run(
            ['git', 'status', '--porcelain', workspace_dir],
            capture_output=True, 
            text=True, 
            cwd=repo.working_dir
        )
        
        if not result.stdout.strip():
             print("Git: No changes staged. Nothing to commit.")
             return False

        # Create commit message
        commit_msg = f"fix(miso): AI-generated fix by {persona_name}"
        
        repo.index.commit(commit_msg)
        print(f"Git: Committed changes with message: '{commit_msg}'")
        return True
    except Exception as e:
        print(f"Error committing changes: {e}")
        return False
