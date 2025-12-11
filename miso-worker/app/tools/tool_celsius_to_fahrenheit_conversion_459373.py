import re

def solve(input_str):
    """Converts a temperature from Celsius to Fahrenheit based on the input string."""
    # Use regex to find and extract the numeric value for Celsius
    match = re.search(r"Convert (-?\d+\.?\d*) Celsius to Fahrenheit", input_str, re.IGNORECASE)
    
    if match:
        try:
            # Extract the captured group, convert it to a float
            celsius = float(match.group(1))
            # Apply the conversion formula
            fahrenheit = (celsius * 9/5) + 32
            # Return a formatted, user-friendly string
            return f"{celsius}°C is {fahrenheit:.1f}°F."
        except (ValueError, IndexError):
            return "Error: Could not parse the number from the input."
    else:
        return "Error: Input pattern not recognized."