from typing import List, Union

def calculate_mean(data: List[Union[int, float]]) -> float:
    """Calculates the mean of a list of numbers."""
    if not data:
        return 0.0
    return sum(data) / len(data)
