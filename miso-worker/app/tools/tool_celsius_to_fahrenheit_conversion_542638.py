import re

def solve(input_str):
    """
    Converts a temperature from Celsius to Fahrenheit if the input string
    matches the expected format.
    """
    pattern = r"Convert\s+(-?\d+\.?\d*)\s+Celsius\s+to\s+Fahrenheit"
    match = re.search(pattern, input_str, re.IGNORECASE)

    if match:
        try:
            celsius = float(match.group(1))
            fahrenheit = (celsius * 9/5) + 32
            return f"{celsius}°C is {fahrenheit:.1f}°F."
        except (ValueError, IndexError):
            return "Error: Invalid number found in the input string."
    else:
        return "Error: Input does not match the required format."