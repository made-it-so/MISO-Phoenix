"""
Plugin Interface for Dynamic Test Prioritization
"""
class TestPrioritizerPlugin:
    def __init__(self):
        pass

    def prioritize_tests(self, test_cases):
        raise NotImplementedError('This method should be implemented by the plugin.')
