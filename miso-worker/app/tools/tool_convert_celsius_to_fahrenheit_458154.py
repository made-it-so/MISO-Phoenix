import re

def solve(input_str):
    """Converts a Celsius value from a string to Fahrenheit."""
    pattern = r"(?i)convert\s+(-?\d+\.?\d*)\s+celsius\s+to\s+fahrenheit"
    match = re.search(pattern, input_str)

    if match:
        try:
            celsius = float(match.group(1))
            fahrenheit = (celsius * 9/5) + 32
            return f"{celsius}°C is {fahrenheit:.1f}°F"
        except (ValueError, IndexError):
            return "Error: Invalid number format found."
    else:
        return "Error: Task pattern not found in input."