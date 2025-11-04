from typing import List, Union

def calculate_mean(data: List[Union[int, float]]) -> float:
    """Calculates the mean of a list of numbers."""
    return sum(data) / len(data)
