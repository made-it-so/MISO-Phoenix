from utils import safe_division_helper

def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtracts two integers."""
    return a - b

def divide(a: int, b: int) -> int:
    return safe_division_helper(a, b)
