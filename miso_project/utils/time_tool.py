
from datetime import datetime

def get_system_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Self-Test for Ouroboros Verification
def test_system_time_format():
    t = get_system_time()
    assert ":" in t
    assert "-" in t
