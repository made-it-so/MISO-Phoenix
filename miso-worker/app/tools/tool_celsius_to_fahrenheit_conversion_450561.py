import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit from a string request."""
    pattern = re.compile(r"convert\s+(-?\d+\.?\d*)\s+celsius\s+to\s+fahrenheit", re.IGNORECASE)
    match = pattern.search(input_str)
    if match:
        try:
            celsius = float(match.group(1))
            fahrenheit = (celsius * 9/5) + 32
            return f"{celsius}°C is {fahrenheit:.1f}°F."
        except (ValueError, IndexError):
            return "Error: Invalid number found in input."
    return "Error: Input does not match expected format."