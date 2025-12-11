import re

def solve(input_str):
    """Extracts Celsius from a string, converts to Fahrenheit, and returns the result."""
    match = re.search(r'(-?\d+\.?\d*)', input_str)
    if match:
        try:
            celsius = float(match.group(1))
            fahrenheit = (celsius * 9/5) + 32
            return f'{celsius}°C is {fahrenheit:.1f}°F'
        except ValueError:
            return 'Error: Invalid number format.'
    return 'Error: Could not find a number to convert.'