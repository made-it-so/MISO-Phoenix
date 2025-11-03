from typing import Optional

def say_hello(name: Optional[str]) -> str:
    """Generates a greeting."""
    if name is None:
        return "Hello, World!"
    return f"Hello, {name}!"
