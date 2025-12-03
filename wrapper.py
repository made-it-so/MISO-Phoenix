
import sys
import json

try:
    def is_palindrome(s: str) -> bool:
        """
        Checks if a string is a palindrome, ignoring case and non-alphanumeric characters.

        A string is considered a palindrome if it reads the same forwards and backwards
        after converting all characters to lowercase and removing all non-alphanumeric
        characters (letters and numbers).

        Args:
            s: The input string to check.

        Returns:
            True if the string is a palindrome, False otherwise.
        """
        # Step 1: Clean the string
        # Convert to lowercase and filter out non-alphanumeric characters.
        # A character is alphanumeric if it is a letter (a-z, A-Z) or a digit (0-9).
        cleaned_s = "".join(char for char in s if char.isalnum()).lower()

        # Step 2: Compare the cleaned string with its reverse
        # Python's slicing `[::-1]` provides an easy way to reverse a string.
        return cleaned_s == cleaned_s[::-1]

    if __name__ == "__main__":
        # Assertion 1: Simple palindrome with all lowercase alphanumeric characters
        assert is_palindrome("madam") == True, "Assertion 1 Failed: 'madam' should be a palindrome."

        # Assertion 2: Palindrome with mixed case, spaces, and punctuation
        assert is_palindrome("Race car!") == True, "Assertion 2 Failed: 'Race car!' should be a palindrome (case-insensitive, ignoring non-alphanumeric)."

        # Assertion 3: Not a palindrome
        assert is_palindrome("hello world") == False, "Assertion 3 Failed: 'hello world' should not be a palindrome."

        print("All 3 assertions passed successfully!")

        # You can uncomment and add more tests here if needed
        # assert is_palindrome("") == True, "Edge case: Empty string"
        # assert is_palindrome("a") == True, "Edge case: Single character string"
        # assert is_palindrome("A man, a plan, a canal: Panama") == True, "Complex palindrome"
        # assert is_palindrome("Python") == False, "Another non-palindrome"

    # --- TEST HARNESS ---
    pass

    print(json.dumps({'status': 'passed', 'msg': 'Tests Passed'}))
except AssertionError as e:
    print(json.dumps({'status': 'failed', 'msg': 'Assertion Failed'}))
except Exception as e:
    print(json.dumps({'status': 'error', 'msg': str(e)}))
