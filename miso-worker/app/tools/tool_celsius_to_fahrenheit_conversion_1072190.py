import re

def solve(input_str):
    """
    Extracts a Celsius value from a string, converts it to Fahrenheit,
    and returns the result as a formatted string.
    """
    # Regex to find a (potentially negative or decimal) number in the specific input format.
    # re.IGNORECASE makes it more flexible (e.g., 'celsius' or 'Celsius').
    pattern = re.compile(r"Convert\s+(-?\d+\.?\d*)\s+Celsius\s+to\s+Fahrenheit", re.IGNORECASE)
    
    match = pattern.search(input_str)
    
    if not match:
        return "Error: Input pattern not recognized. Expected 'Convert [number] Celsius to Fahrenheit'."

    try:
        # Group 1 captures the number part of the regex.
        celsius_val = float(match.group(1))
        
        # Formula for Celsius to Fahrenheit conversion.
        fahrenheit_val = (celsius_val * 9/5) + 32
        
        # Return a clean string, avoiding unnecessary .0 for whole numbers.
        return f"{celsius_val}°C is {fahrenheit_val:g}°F."

    except (ValueError, IndexError):
        return "Error: Could not parse the number for conversion."
