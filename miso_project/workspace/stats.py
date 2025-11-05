
def calculate_mean(l):
    """Calculates the mean of a list."""
    if not l:
        return 0.0
    return sum(l) / len(l)
