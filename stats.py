def calculate_median(numbers):
    """
    Calculates the median of a list of numbers.

    The median is the value separating the higher half from the lower half of a
    data sample. For a data set, it may be thought of as the "middle" value.

    Args:
        numbers (list of int or float): A list of numerical data.

    Returns:
        float or int: The median of the list.

    Raises:
        ValueError: If the input list is empty.
    """
    if not numbers:
        raise ValueError("Input list cannot be empty")

    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    mid_index = n // 2

    if n % 2 == 1:
        # Odd number of elements
        median = sorted_numbers[mid_index]
    else:
        # Even number of elements
        median = (sorted_numbers[mid_index - 1] + sorted_numbers[mid_index]) / 2

    return median
