import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit based on a string input."""
    # Regex to capture integer or float numbers, including negatives.
    pattern = r"Convert\s+(-?\d+\.?\d*)\s+Celsius to Fahrenheit"
    
    # Search for the pattern, ignoring case.
    match = re.search(pattern, input_str, re.IGNORECASE)
    
    if match:
        try:
            # Extract the Celsius value (captured group 1) and convert to float.
            celsius = float(match.group(1))
            
            # Apply the conversion formula: F = C * 9/5 + 32
            fahrenheit = (celsius * 9/5) + 32
            
            # Return a formatted string with the result.
            return f"{celsius}°C is {fahrenheit:.1f}°F."
        except ValueError:
            return "Error: Invalid number found in input string."
    else:
        return "Error: Input does not match expected format."