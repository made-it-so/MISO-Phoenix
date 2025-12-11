import re

def solve(input_str):
    """
    Extracts a Celsius value from a string, converts it to Fahrenheit,
    and returns the result as a formatted string.
    """
    try:
        # Regex to capture a potentially negative or floating-point number
        match = re.search(r"Convert\s+(-?\d+\.?\d*)\s+Celsius\s+to\s+Fahrenheit", input_str, re.IGNORECASE)
        if not match:
            return "Error: Could not find a valid temperature to convert."

        celsius = float(match.group(1))
        fahrenheit = (celsius * 9/5) + 32
        return f"{celsius}°C is {fahrenheit:.1f}°F"

    except (ValueError, IndexError):
        return "Error: Invalid number format for temperature."
    except Exception as e:
        return f"An unexpected error occurred: {e}"