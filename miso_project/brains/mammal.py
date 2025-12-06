from cache.solution_cache import GLOBAL_SOLUTION_CACHE

def run_mammal_brain(isolated_error: str, file_context: dict) -> list:
    print("--- TIER 2 (Mammal 🧠) ACTIVATED ---")
    
    cached_plan = GLOBAL_SOLUTION_CACHE.query(isolated_error)
    
    if cached_plan:
        print("🧠 Mammal: Found a cached plan. Submitting for re-verification.")
        return cached_plan

    print("🧠 Mammal: No cached solution found. Escalating.")
    return []
