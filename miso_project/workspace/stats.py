from typing import List

def calculate_mean(data: List[float]) -> float:
    """Calculates the mean of a list of numbers."""
    if not data:
        return 0.0
    return sum(data) / len(data)
