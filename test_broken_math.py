# This TDD file expects the correct behavior.
# It will fail with a ZeroDivisionError
# until MISO fixes the bug.

import pytest
from broken_math import get_average

def test_get_average_simple():
    # This test expects get_average([10, 20]) to return 15.
    # Instead, it will crash with ZeroDivisionError
    # from the buggy 'get_average' function.
    assert get_average([10, 20]) == 15

def test_get_average_empty():
    # This test will pass, as the buggy file
    # correctly handles empty lists.
    assert get_average([]) == 0

def test_get_average_single_number():
    # This test will also fail with ZeroDivisionError.
    assert get_average([5]) == 5
