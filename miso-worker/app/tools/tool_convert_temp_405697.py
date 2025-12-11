import re

def solve(prompt):
    """
    Extracts a Celsius temperature from a prompt, converts it to Fahrenheit,
    and returns the result as a string.
    """
    try:
        pattern = r"(?i)convert\s+(-?\d+(?:\.\d+)?)\s+celsius"
        match = re.search(pattern, prompt)

        if not match:
            return "Error: Could not find a Celsius value to convert."

        celsius_str = match.group(1)
        celsius = float(celsius_str)

        # Conversion formula: F = (C * 9/5) + 32
        fahrenheit = (celsius * 9/5) + 32

        return f"{celsius}°C is {fahrenheit:.2f}°F."

    except ValueError:
        return f"Error: Invalid number format for Celsius value found in prompt."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"