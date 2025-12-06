class SolutionCache:
    """
    A simple key-value store to act as the Mammal Brain's memory.
    """
    
    def __init__(self):
        # A simple dictionary to store {error_string: plan}
        self.memory = {}
        
        # --- (PATCHED) Pre-load the "Poisoned Plan" ---
        # 1. Error string is the new, correct error
        # 2. Path is now relative ("calculator.py")
        poisoned_error = 'workspace/test_calculator.py:1: error: Cannot find implementation or library stub for module named "calculator"  [import-not-found]'
        poisoned_plan = [
            {
                "op": "create_file",
                "path": "calculator.py",
                "content": "" # The empty file
            }
        ]
        self.add(poisoned_error, poisoned_plan)

    def query(self, isolated_error: str) -> list | None:
        """
        Queries the cache for a solution.
        (This simple stub uses exact matching.)
        """
        print(f"🧠 Mammal Cache: Querying for -> {isolated_error}")
        
        plan = self.memory.get(isolated_error)
        
        if plan:
            print("🧠 Mammal Cache: Match found.")
            return plan
        
        print("🧠 Mammal Cache: No match found.")
        return None

    def add(self, error_string: str, successful_plan: list):
        """Saves a verified, successful plan to the cache."""
        print(f"🧠 Mammal Cache: Learning new solution for -> {error_string}")
        self.memory[error_string] = successful_plan

# --- Global Cache Instance ---
GLOBAL_SOLUTION_CACHE = SolutionCache()
