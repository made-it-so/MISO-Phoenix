from logger import get_logger

logger = get_logger()

def test_logger_is_debug():
    assert logger.get_level() == "DEBUG"
