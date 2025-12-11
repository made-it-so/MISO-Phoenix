import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit based on a string input."""
    # Regex to find the temperature in Celsius, case-insensitive
    match = re.search(r"Convert\s+(-?\d+\.?\d*)\s+Celsius\s+to\s+Fahrenheit", input_str, re.IGNORECASE)
    if not match:
        return "Invalid input format. Expected: 'Convert [number] Celsius to Fahrenheit'"

    try:
        # Extract the Celsius value and convert it to a float
        celsius = float(match.group(1))
        
        # Apply the conversion formula: F = (C * 9/5) + 32
        fahrenheit = (celsius * 9/5) + 32
        
        # Return the result as a formatted string
        return f"{celsius}°C is {fahrenheit:.2f}°F"
    except (ValueError, IndexError):
        # This handles cases where the captured group is not a valid number
        return "Error processing the temperature value."