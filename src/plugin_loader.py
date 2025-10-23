```python
class PluginLoader:
    def __init__(self) -> None:
        self.plugins: list = []

    def load_plugins(self, plugin_directory: str) -> None:
        # Logic to dynamically discover and load plugins from the specified directory
        pass

    def apply_prioritization(self, tests: list[str]) -> None:
        # Logic to apply the loaded plugin's prioritization logic to the tests
        pass
```