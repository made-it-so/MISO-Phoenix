import re
from typing import Callable, Dict

class ReflexRouter:
    """
    Level 1: The Preconfigured Backbone.
    Deterministic, zero-latency routing based on 'Relevant Extreme Directions'.
    """
    def __init__(self):
        self.routes: Dict[str, Callable] = {}

    def register(self, pattern: str, tool: Callable):
        self.routes[pattern] = tool

    def route(self, prompt: str):
        """
        Scans prompt for 'Extreme Directions' (keywords that force a specific path).
        """
        for pattern, tool in self.routes.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                return {"type": "backbone", "tool": tool.__name__, "confidence": 1.0}
        return {"type": "cortex", "tool": None, "confidence": 0.0}
