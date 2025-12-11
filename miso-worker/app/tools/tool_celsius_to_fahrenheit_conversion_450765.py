import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit based on the input string."""
    try:
        # Extract the numeric value using regex
        match = re.search(r"(-?\d+\.?\d*)", input_str)
        if not match:
            return "Error: Could not find a number in the input."

        celsius = float(match.group(1))
        
        # Apply the conversion formula: F = C * 9/5 + 32
        fahrenheit = (celsius * 9/5) + 32
        
        # Return the result in a user-friendly format
        return f"{celsius}°C is equal to {fahrenheit:.1f}°F."
    except (ValueError, IndexError):
        return "Error: Invalid input format."