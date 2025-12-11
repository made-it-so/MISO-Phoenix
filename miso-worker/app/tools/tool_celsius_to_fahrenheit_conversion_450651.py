import re

def solve(input_str):
    """Extracts Celsius value, converts to Fahrenheit, and returns the result."""
    # Regex to capture the numeric value for Celsius (integer or float, positive or negative)
    match = re.search(r'Convert (-?\d+\.?\d*)\s+Celsius to Fahrenheit', input_str, re.IGNORECASE)
    
    if match:
        try:
            celsius = float(match.group(1))
            # Formula for Celsius to Fahrenheit conversion
            fahrenheit = (celsius * 9/5) + 32
            # Return a formatted string with the result, rounded to two decimal places
            return f"{celsius}°C is {fahrenheit:.2f}°F."
        except (ValueError, IndexError):
            return "Error: Invalid number found in input."
    else:
        return "Error: Input format not recognized."