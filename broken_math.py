# This file contains a bug
def divide_by(a, b):
    return a / b # The bug
def calculate_mean(numbers):
    if not numbers:
        return 0
    total_sum = sum(numbers)
    return divide_by(total_sum, len(numbers)) # The trigger
