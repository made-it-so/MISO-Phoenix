import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit based on a string input."""
    match = re.search(r'Convert (-?\d+\.?\d*) Celsius to Fahrenheit', input_str)
    if match:
        try:
            celsius = float(match.group(1))
            fahrenheit = (celsius * 9/5) + 32
            return f'{celsius}°C is {fahrenheit:.1f}°F'
        except (ValueError, IndexError):
            return 'Error: Invalid number format found in input.'
    return 'Error: Could not parse the conversion request.'