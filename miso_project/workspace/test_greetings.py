from greetings import say_hello

def test_say_hello():
    """Tests the say_hello function."""
    assert say_hello("MISO") == "Hello, MISO!"

def test_say_hello_default():
    """Tests the default greeting."""
    assert say_hello(None) == "Hello, World!"
