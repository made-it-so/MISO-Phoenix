import time

class MISO_Module:
    """Represents a conceptual 'Registry Patch' or 'Legacy Script'."""
    def __init__(self, name, module_type, priority=5, last_updated=None,
                 redundancy_score=0.1, efficiency_score=0.9,
                 relevant_keywords=None):
        self.name = name
        self.module_type = module_type # e.g., 'knowledge_base', 'algorithm', 'config'
        self.priority = priority # Base priority (1-10, 10 being highest)
        self.last_updated = last_updated if last_updated else time.time()
        self.redundancy_score = redundancy_score # 0.0 (unique) to 1.0 (highly redundant)
        self.efficiency_score = efficiency_score # 0.0 (inefficient) to 1.0 (highly efficient)
        self.relevant_keywords = relevant_keywords if relevant_keywords else []
        self.current_processing_weight = self.priority # Dynamic weight for modulation

    def execute(self, current_context_keywords):
        """Simulates module execution based on current weight."""
        if self.current_processing_weight > 0:
            print(f"  Executing {self.name} (Type: {self.module_type}) with weight: {self.current_processing_weight:.2f}")
            # Simulate actual work based on weight
            time.sleep(1 / (self.current_processing_weight * self.efficiency_score))
            return f"Output from {self.name}"
        else:
            print(f"  {self.name} (Type: {self.module_type}) suppressed.")
            return None

class MISO_Modulation_Engine:
    def __init__(self):
        self.modules = {}

    def add_module(self, module):
        self.modules[module.name] = module

    def calculate_arousal_contrast(self, task_description, user_engagement_level):
        """
        Simulates deriving 'arousal' and 'contrast' from the current behavioral state.
        'Arousal' ~ user_engagement_level (0-10)
        'Contrast' ~ how unique/critical the task keywords are.
        """
        task_keywords = set(task_description.lower().split())
        overall_novelty_score = len(task_keywords) / 10.0 # Simplified
        
        arousal_level = user_engagement_level / 10.0 # Normalize 0-1
        contrast_level = (arousal_level + overall_novelty_score) / 2 # Simple average
        return arousal_level, contrast_level

    def apply_aca_like_gain(self, module, arousal_level, contrast_level, task_keywords):
        """
        Applies ACA-like gain control: boosts relevant modules based on arousal and contrast.
        """
        relevance_score = sum(1 for kw in task_keywords if kw in module.relevant_keywords) / len(task_keywords) if task_keywords else 0
        
        # ACA: Enhance visual encoding (processing weight)
        # Stronger boost for relevant modules under high arousal/contrast
        boost_factor = 1 + (arousal_level * contrast_level * relevance_score * 2) # Factor can go up to 3
        module.current_processing_weight = module.priority * boost_factor
        
        # Ensure a floor for processing weight even if not highly relevant, but not excessive
        module.current_processing_weight = max(module.priority * 0.5, module.current_processing_weight)
        return module.current_processing_weight

    def apply_orb_like_filtering(self, module, arousal_level, contrast_level, task_keywords):
        """
        Applies ORB-like filtering: reduces less efficient/redundant modules, especially when
        high-contrast (e.g., specific, focused task) is present.
        """
        relevance_score = sum(1 for kw in task_keywords if kw in module.relevant_keywords) / len(task_keywords) if task_keywords else 0

        # ORB: Reduces high-contrast visual encoding (processing weight)
        # Suppress redundant/inefficient modules, especially if not highly relevant AND
        # there's high "contrast" (implying a focused task where noise is detrimental).
        suppression_factor = 1 - (module.redundancy_score * (1 - module.efficiency_score) * (1 - relevance_score) * contrast_level)
        
        # Don't suppress relevant modules too much. If relevance is high, suppression is low.
        if relevance_score > 0.7: # Highly relevant, minimal suppression
            suppression_factor = max(0.9, suppression_factor) # Keep weight high
        
        module.current_processing_weight *= suppression_factor
        
        # Ensure a minimum weight to avoid complete shutdown unless explicitly warranted
        module.current_processing_weight = max(0.1, module.current_processing_weight) # Floor for suppression
        return module.current_processing_weight

    def orchestrate_modules(self, task_description, user_engagement_level):
        """Automates the modulation process."""
        print(f"\n--- Orchestrating for Task: '{task_description}' (Engagement: {user_engagement_level}/10) ---")
        arousal_level, contrast_level = self.calculate_arousal_contrast(task_description, user_engagement_level)
        task_keywords = set(task_description.lower().split())

        print(f"  Calculated Arousal: {arousal_level:.2f}, Contrast: {contrast_level:.2f}")

        # Reset weights to base priority before applying modulation for each task
        for module in self.modules.values():
            module.current_processing_weight = module.priority

        # Apply ACA-like modulation first
        for name, module in self.modules.items():
            if module.module_type != 'legacy_script': # ACA primarily for core logic
                self.apply_aca_like_gain(module, arousal_level, contrast_level, task_keywords)
                # print(f"  [ACA] {name} new weight: {module.current_processing_weight:.2f}")
        
        # Apply ORB-like modulation, potentially affecting all but focusing on 'legacy'
        for name, module in self.modules.items():
            self.apply_orb_like_filtering(module, arousal_level, contrast_level, task_keywords)
            # print(f"  [ORB] {name} final weight: {module.current_processing_weight:.2f}")

        # Execute modules based on final modulated weights
        results = {}
        sorted_modules = sorted(self.modules.values(), key=lambda m: m.current_processing_weight, reverse=True)
        print("\n  Executing modules based on modulated weights:")
        for module in sorted_modules:
            output = module.execute(task_keywords)
            if output:
                results[module.name] = output
        return results

# --- Demonstration ---
if __name__ == "__main__":
    engine = MISO_Modulation_Engine()

    # Core Registry Patches (knowledge bases, essential algorithms)
    engine.add_module(MISO_Module("CoreNLP", "knowledge_base", priority=9, relevant_keywords=["language", "nlp", "text", "understanding"]))
    engine.add_module(MISO_Module("SearchAlgorithmV2", "algorithm", priority=8, relevant_keywords=["search", "data", "retrieval", "optimize"]))
    engine.add_module(MISO_Module("SecurityPolicy", "config", priority=10, relevant_keywords=["security", "access", "policy"]))
    engine.add_module(MISO_Module("KnowledgeGraph", "knowledge_base", priority=7, relevant_keywords=["facts", "relationships", "data", "structure"]))

    # Legacy Scripts (older algorithms, less efficient data parsers)
    engine.add_module(MISO_Module("OldDataParser", "legacy_script", priority=3, redundancy_score=0.8, efficiency_score=0.4, relevant_keywords=["parse", "old_data", "format"]))
    engine.add_module(MISO_Module("LegacyReportGen", "legacy_script", priority=4, redundancy_score=0.6, efficiency_score=0.6, relevant_keywords=["report", "generate", "summary"]))
    engine.add_module(MISO_Module("BackupLogger", "legacy_script", priority=2, redundancy_score=0.9, efficiency_score=0.2, relevant_keywords=["log", "backup", "archive"]))

    # Scenario 1: High-priority, focused request (high arousal, high contrast)
    print("\n--- Scenario 1: Urgent Security Policy Check ---")
    engine.orchestrate_modules("Urgent: Check security access policies for sensitive data immediately.", user_engagement_level=9)

    # Scenario 2: General information retrieval (moderate arousal, moderate contrast)
    print("\n--- Scenario 2: Find information about data structures ---")
    engine.orchestrate_modules("Find information about advanced data structures in the knowledge base.", user_engagement_level=6)

    # Scenario 3: Routine logging task (low arousal, low contrast)
    print("\n--- Scenario 3: Perform routine backup logging ---")
    engine.orchestrate_modules("Perform routine backup logging for archives.", user_engagement_level=2)

    # Scenario 4: Request that could potentially trigger legacy scripts but should be optimized
    print("\n--- Scenario 4: Optimize data search for relationships ---")
    engine.orchestrate_modules("Optimize data search for relationships within the knowledge graph.", user_engagement_level=7)