import re
import os

# In a real-world scenario, 'web_searcher' would be a pre-existing, imported tool.
# For this self-contained solution, we simulate it with a class.
class WebSearcher:
    """A mock tool to simulate searching the web for information."""
    def search(self, query: str) -> str:
        """Simulates a web search and returns a string with the answer."""
        query = query.lower()
        if "current price of bitcoin" in query or "btc price" in query:
            # Returns a realistic-looking string for the price of Bitcoin.
            return "According to top market aggregators, the current price of Bitcoin (BTC) is $68,420.55 USD."
        else:
            return "No relevant price information found for the query."


def solve(input_str: str) -> str:
    """
    Task: Uses a web_searcher to find the current price of Bitcoin (BTC)
    and saves it to a file named 'btc_price.txt'.

    Args:
        input_str (str): A string describing the task. Not directly used but required by the function signature.

    Returns:
        str: A message indicating the outcome of the operation.
    """
    try:
        # Step 1: Instantiate the web searching tool.
        web_searcher = WebSearcher()

        # Step 2: Define the search query and use the tool.
        query = "current price of Bitcoin"
        search_result = web_searcher.search(query)
        print(f"Web search result: '{search_result}'")

        # Step 3: Parse the price from the search result using regex.
        # This pattern looks for a dollar sign followed by digits, commas, and an optional decimal part.
        price_pattern = r'\$\s*([\d,]+\.?\d*)'
        match = re.search(price_pattern, search_result)

        if not match:
            raise ValueError("Could not find the Bitcoin price in the web search result.")

        # Step 4: Extract the matched price and remove commas for clean storage.
        price_str = match.group(1)
        clean_price = price_str.replace(',', '')

        # Step 5: Save the clean price to the specified file.
        file_name = 'btc_price.txt'
        with open(file_name, 'w') as f:
            f.write(clean_price)

        success_message = f"Successfully found Bitcoin price (${clean_price}) and saved to '{file_name}'."
        print(success_message)
        return success_message

    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
        return error_message
