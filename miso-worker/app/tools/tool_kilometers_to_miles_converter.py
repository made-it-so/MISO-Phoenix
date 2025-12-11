import sys
import io

def solve(input_str):
    """
    Converts a distance in kilometers to miles.
    The input string is expected to be a number representing kilometers.
    """
    try:
        # Attempt to convert the input string to a floating-point number
        kilometers = float(input_str.strip())
    except ValueError:
        # Handle cases where the input is not a valid number
        return "Error: Invalid input. Please enter a number."

    # Check if the distance is negative, which is not physically possible
    if kilometers < 0:
        return "Error: Distance cannot be negative. Please enter a non-negative number."

    # The conversion factor from kilometers to miles
    conversion_factor = 0.621371

    # Calculate the distance in miles
    miles = kilometers * conversion_factor

    # Return the result as a formatted string
    # Using .2f to round to two decimal places for readability
    return f"{kilometers} km is equal to {miles:.2f} miles."

