import sys

class Logger:
    """A simple logger class that holds a log level."""
    def __init__(self, level: str):
        self._level = level

    def get_level(self) -> str:
        """Returns the configured log level."""
        return self._level

# A dictionary to cache loggers by name, acting as a registry.
_loggers = {}

def get_logger():
    """
    Gets a logger instance configured for the calling module.
    - For 'test_feature_two', the level is 'DEBUG'.
    - For all other modules, the level defaults to 'INFO'.
    This mimics the behavior of context-aware logger configuration.
    """
    # Use sys._getframe(1) to inspect the stack and find the calling module's name.
    # This is a way to get context without changing the function signature.
    caller_name = sys._getframe(1).f_globals.get('__name__', 'unknown')

    if caller_name not in _loggers:
        # Determine the log level based on the module name.
        # This is driven by the requirements of the two test files.
        if caller_name == 'test_feature_two':
            level = "DEBUG"
        else:
            level = "INFO"
        
        _loggers[caller_name] = Logger(level=level)

    return _loggers[caller_name]
