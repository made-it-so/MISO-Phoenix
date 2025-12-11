import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit based on a string input."""
    # Pattern to extract the number from a string like "Convert X Celsius to Fahrenheit"
    # It handles integers, floats, and negative numbers.
    pattern = r"Convert\s+(-?\d+(?:\.\d+)?)\s+Celsius\s+to\s+Fahrenheit"
    
    match = re.search(pattern, input_str, re.IGNORECASE)
    
    if match:
        try:
            celsius_val = float(match.group(1))
            fahrenheit_val = (celsius_val * 9/5) + 32
            # Return a clear, formatted string with the result.
            return f"{celsius_val}°C is {fahrenheit_val:.1f}°F"
        except (ValueError, IndexError):
            return "Error: Could not parse the number from the input."
            
    return "Error: Input format not recognized."