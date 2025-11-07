# This file contains a bug the Lizard brain
# is not designed to fix.

def divide_by(a, b):
    # This will cause a ZeroDivisionError if b is 0
    return a / b

def get_average(numbers):
    if not numbers:
        return 0

    # This is the "bait" bug.
    total_sum = sum(numbers)
    return divide_by(total_sum, len(numbers))
