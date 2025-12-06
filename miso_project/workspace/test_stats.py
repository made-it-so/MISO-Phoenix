
from stats import calculate_mean
import pytest

def test_mean_happy_path():
    assert calculate_mean([1.0, 2.0, 3.0]) == 2.0

def test_mean_single_item():
    assert calculate_mean([5.0]) == 5.0

def test_mean_empty_list():
    assert calculate_mean([]) == 0.0
