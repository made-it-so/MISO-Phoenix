import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit based on a specific input string format."""
    # Regex to capture the numeric value for Celsius
    pattern = r'^Convert ([-]?\d*\.?\d+)\s+Celsius to Fahrenheit$'
    
    # Search for the pattern, ignoring case
    match = re.search(pattern, input_str, re.IGNORECASE)
    
    if match:
        try:
            # Extract the captured number (group 1) and convert to a float
            celsius = float(match.group(1))
            
            # Apply the conversion formula: F = (C * 9/5) + 32
            fahrenheit = (celsius * 9/5) + 32
            
            # Return a formatted string with the result, rounded to one decimal place
            return f"{celsius}°C is {fahrenheit:.1f}°F"
        except (ValueError, IndexError):
            # This case handles if the captured group is not a valid number (e.g., empty or corrupt)
            return "Error: Invalid number format in input."
    else:
        # This case handles if the input string does not match the expected format
        return "Error: Input does not match expected format 'Convert X Celsius to Fahrenheit'."