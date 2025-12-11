import re

def solve(input_str):
    """Converts Celsius to Fahrenheit from a specific string pattern."""
    pattern = re.compile(r"^Convert\s+(-?\d+\.?\d*)\s+Celsius\s+to\s+Fahrenheit$", re.IGNORECASE)
    match = pattern.search(input_str)
    if match:
        try:
            celsius = float(match.group(1))
            fahrenheit = (celsius * 9/5) + 32
            return f"{celsius}°C is {fahrenheit:.1f}°F."
        except (ValueError, IndexError):
            return "Error: Invalid number found in input."
    return None