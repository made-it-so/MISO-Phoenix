import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit based on a string input."""
    # Use regex to find the numeric Celsius value in the input string
    match = re.search(r"(-?\d+\.?\d*)", input_str)
    
    if match:
        try:
            celsius = float(match.group(1))
            # Formula for Celsius to Fahrenheit conversion
            fahrenheit = (celsius * 9/5) + 32
            return f"{celsius}°C is {fahrenheit:.1f}°F."
        except (ValueError, IndexError):
            return "Error: Invalid number found in input string."
    else:
        return "Error: Could not find a temperature to convert."