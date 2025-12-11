import re

def solve(input_str):
    """Converts Celsius to Fahrenheit based on a string input."""
    pattern = r'Convert\s+(-?\d+\.?\d*)\s+Celsius to Fahrenheit'
    match = re.search(pattern, input_str, re.IGNORECASE)
    
    if match:
        try:
            celsius = float(match.group(1))
            fahrenheit = (celsius * 9/5) + 32
            return f"{celsius}°C is {fahrenheit:.1f}°F."
        except (ValueError, IndexError):
            return "Error: Could not parse the temperature value."
    else:
        return "Error: Input format not recognized."