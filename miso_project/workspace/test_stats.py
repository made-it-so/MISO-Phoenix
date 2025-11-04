from stats import calculate_mean

def test_mean():
    """Tests the calculate_mean function."""
    assert calculate_mean([1, 2, 3]) == 2.0
