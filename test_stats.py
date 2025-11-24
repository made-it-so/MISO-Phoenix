# This is the TDD test for Gauntlet 5.
# It imports a function that does not exist.

import pytest
from stats import calculate_median

def test_calculate_median_odd_list():
    assert calculate_median([1, 5, 2, 8, 3]) == 3

def test_calculate_median_even_list():
    assert calculate_median([4, 1, 3, 2]) == 2.5

def test_calculate_median_empty_list():
    assert calculate_median([]) is None
