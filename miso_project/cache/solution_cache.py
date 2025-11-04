import json
import os

# (THE FIX: Path is relative to this file's location)
CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), "mammal_brain_cache.json")

class SolutionCache:
    def __init__(self, cache_file=CACHE_FILE_PATH):
        self.cache_file = cache_file
        self.memory = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"🧠 Mammal Cache: WARNING! Could not decode {self.cache_file}. Starting fresh.")
            return {}

    def _save(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"🧠 Mammal Cache: ERROR! Could not save cache: {e}")

    def query(self, isolated_error: str) -> list | None:
        print(f"🧠 Mammal Cache: Querying for -> {isolated_error[:200]}...") # Truncate long errors
        plan = self.memory.get(isolated_error)
        if plan:
            print("🧠 Mammal Cache: Match found.")
            return plan
        print("🧠 Mammal Cache: No match found.")
        return None

    def add(self, error_string: str, successful_plan: list, save: bool = True):
        print(f"🧠 Mammal Cache: Learning new solution for -> {error_string[:200]}...") # Truncate long errors
        self.memory[error_string] = successful_plan
        if save:
            self._save()

GLOBAL_SOLUTION_CACHE = SolutionCache()
