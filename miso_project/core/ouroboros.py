import git
import subprocess
import logging
import os
import shutil
from datetime import datetime

# Rigid Logging for Evolution Events
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.ouroboros")

class GitManager:
    """
    The Ouroboros Safety Valve.
    Ensures self-modifications are verified before becoming permanent.
    """
    
    def __init__(self, repo_path="."):
        self.repo_path = os.path.abspath(repo_path)
        try:
            self.repo = git.Repo(self.repo_path)
            self.main_branch = self.repo.active_branch.name
            logger.info(f"Ouroboros attached to branch: {self.main_branch}")
        except git.exc.InvalidGitRepositoryError:
            logger.error("CRITICAL: Not a valid git repository. Evolution impossible.")
            raise

    def start_evolution(self, feature_name="auto-upgrade"):
        """Creates a timeline (branch) for mutation."""
        branch_name = f"miso/{feature_name}-{int(datetime.now().timestamp())}"
        
        if self.repo.is_dirty(untracked_files=True):
            logger.warning("Repo is dirty. Stashing changes before evolution...")
            self.repo.git.stash('save', "Pre-evolution stash")
            
        current = self.repo.create_head(branch_name)
        current.checkout()
        logger.info(f"Evolution timeline started: {branch_name}")
        return branch_name

    def commit_mutation(self, file_path, content, message="Genetic modification"):
        """Writes the new code (mutation) to the branch."""
        full_path = os.path.join(self.repo_path, file_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
            
        self.repo.index.add([full_path])
        self.repo.index.commit(message)
        logger.info(f"Mutation committed: {message}")

    def verify_fitness(self, test_target=None):
        """
        Runs the immune system (pytest) with proper environment context.
        """
        target = test_target if test_target else "."
        logger.info(f"Running adversarial tests on target: {target}")
        
        # CRITICAL FIX: Inject current directory into PYTHONPATH
        # This ensures the subprocess can import 'miso_project'
        env = os.environ.copy()
        env["PYTHONPATH"] = self.repo_path + os.pathsep + env.get("PYTHONPATH", "")
        
        try:
            # -q: quiet mode, only show errors
            cmd = ["pytest", "-q", target]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                env=env,       # Inject the modified environment
                cwd=self.repo_path # Ensure we run from root
            )
            
            if result.returncode == 0:
                logger.info("FITNESS CHECK PASSED. Mutation is viable.")
                return True
            else:
                logger.error(f"FITNESS CHECK FAILED.\n{result.stderr or result.stdout}")
                return False
        except Exception as e:
            logger.error(f"Test Execution Failed: {e}")
            return False

    def complete_evolution(self, branch_name):
        """Merge the successful mutation into the main timeline."""
        try:
            self.repo.git.checkout(self.main_branch)
            self.repo.git.merge(branch_name)
            logger.info(f"Evolution Complete. Merged {branch_name} into {self.main_branch}")
            self.repo.delete_head(branch_name, force=True)
            return True
        except Exception as e:
            logger.error(f"Merge Failed: {e}")
            return False

    def abort_evolution(self, branch_name):
        """Revert the timeline."""
        logger.warning("Aborting Evolution. Reverting to stable state.")
        self.repo.git.checkout(self.main_branch)
        self.repo.git.branch("-D", branch_name)

# --- FINAL VERIFICATION PROTOCOL ---
if __name__ == "__main__":
    gm = GitManager()
    
    print("\n>>> TEST 1: SIMULATING FATAL MUTATION (Should Revert)")
    branch = gm.start_evolution("fatal-test-final")
    
    gm.commit_mutation("test_mutation_bad.py", "def broken(): return 'syntax error")
    
    if gm.verify_fitness("test_mutation_bad.py"):
        print("CRITICAL FAIL: Bad code passed tests!")
    else:
        print("SUCCESS: Bad code rejected.")
        gm.abort_evolution(branch)

    print("\n>>> TEST 2: SIMULATING VIABLE MUTATION (Should Merge)")
    branch = gm.start_evolution("viable-test-final")
    
    good_code = "def working_function(): return True"
    gm.commit_mutation("miso_project/core/new_feature.py", good_code)
    
    pass_test = "from miso_project.core.new_feature import working_function\ndef test_working(): assert working_function() is True"
    gm.commit_mutation("tests/test_new_feature_final.py", pass_test)
    
    if gm.verify_fitness("tests/test_new_feature_final.py"):
        print("SUCCESS: Good code passed.")
        gm.complete_evolution(branch)
        
        # Verification & Cleanup
        if os.path.exists("miso_project/core/new_feature.py"):
            print("VERIFIED: File merged to main branch.")
            # Manual cleanup of the test artifacts
            os.remove("miso_project/core/new_feature.py")
            os.remove("tests/test_new_feature_final.py")
            if os.path.exists("test_mutation_bad.py"): os.remove("test_mutation_bad.py")
    else:
        print("FAIL: Good code failed tests.")
        gm.abort_evolution(branch)
