import os
import subprocess
import datetime
import logging

# CONFIGURATION
PROTECTED_BRANCHES = ['main', 'master', 'production']
IDENTITY_NAME = "MISO Phoenix V61"
IDENTITY_EMAIL = "bot@miso.ai"

# LOGGING SETUP
logging.basicConfig(level=logging.INFO, format='[ARCHIVIST] %(message)s')
logger = logging.getLogger("Archivist")

class GitArchivist:
    def __init__(self, repo_path="."):
        self.repo_path = repo_path
        self.ensure_gitignore()
        self.configure_identity()

    def run_cmd(self, command):
        """Executes a shell command and returns output/error."""
        try:
            result = subprocess.run(
                command, 
                cwd=self.repo_path, 
                shell=True, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {command}\nError: {e.stderr}")
            raise e

    def configure_identity(self):
        """Ensures the agent has a git identity inside the container."""
        try:
            self.run_cmd(f'git config user.name "{IDENTITY_NAME}"')
            self.run_cmd(f'git config user.email "{IDENTITY_EMAIL}"')
        except Exception as e:
            logger.warning(f"Could not configure identity: {e}")

    def ensure_gitignore(self):
        """Enforces a strict .gitignore to prevent secret leaks."""
        gitignore_path = os.path.join(self.repo_path, ".gitignore")
        required_ignores = [
            "__pycache__/",
            "*.log",
            ".env",
            "secrets/",
            "*.pem",
            ".DS_Store",
            "miso_sandbox/"
        ]
        
        existing = []
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                existing = [line.strip() for line in f.readlines()]

        with open(gitignore_path, "a") as f:
            for item in required_ignores:
                if item not in existing:
                    f.write(f"\n{item}")
                    logger.info(f"Added {item} to .gitignore")

    def get_current_branch(self):
        return self.run_cmd("git rev-parse --abbrev-ref HEAD")

    def create_evolution_branch(self):
        """Creates a unique branch for this evolution cycle."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"evolution/v61-{timestamp}"
        
        logger.info(f"Creating quarantine branch: {branch_name}")
        self.run_cmd(f"git checkout -b {branch_name}")
        return branch_name

    def sync_state(self, message="Automated evolution snapshot"):
        """Safely commits and pushes changes to a non-protected branch."""
        current_branch = self.get_current_branch()

        # GUARDRAIL: Prevent pushing to main
        if current_branch in PROTECTED_BRANCHES:
            logger.warning(f"Current branch is {current_branch} (PROTECTED). Switching to evolution branch.")
            new_branch = self.create_evolution_branch()
        else:
            new_branch = current_branch

        # STAGE
        status = self.run_cmd("git status --porcelain")
        if not status:
            logger.info("No changes to sync.")
            return

        self.run_cmd("git add .")
        
        # COMMIT
        self.run_cmd(f'git commit -m "[MISO AUTO] {message}"')
        
        # PUSH
        try:
            # We use --set-upstream just in case it's a new branch
            self.run_cmd(f"git push --set-upstream origin {new_branch}")
            logger.info(f"SUCCESS: State synced to origin/{new_branch}")
            return new_branch
        except Exception as e:
            logger.error(f"Push failed. Ensure SSH keys/Tokens are mounted. {e}")
            return None

if __name__ == "__main__":
    # Test Run
    archivist = GitArchivist()
    print("Module Loaded Successfully.")
