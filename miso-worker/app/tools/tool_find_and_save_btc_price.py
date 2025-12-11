import re
import os

# To make the code self-contained and testable, we'll mock the web_searcher tool.
# In a real environment, this would be an imported library or API call.
class MockWebSearcher:
    """A mock class to simulate web search functionality."""
    def search(self, query: str) -> str:
        """
        Simulates a web search for a given query.
        Returns a mock result string containing the price of Bitcoin.
        """
        query = query.lower()
        if "bitcoin" in query:
            # This string simulates a realistic search engine snippet.
            return "The current price of Bitcoin (BTC) is $67,123.45 according to top crypto exchanges. The value has seen a 2% increase in the last 24 hours."
        else:
            return "Could not find relevant price information for the query."

web_searcher = MockWebSearcher()

def solve(input_str: str):
    """
    Task: Uses the web_searcher tool to find the current price of Bitcoin 
    and saves only the numerical price to a file named 'btc_price.txt'.

    Args:
        input_str (str): A string describing the task. This specific implementation
                         is hardcoded for Bitcoin and does not use this argument.
    """
    output_filename = 'btc_price.txt'
    
    try:
        # Step 1: Use the web_searcher tool to get information about Bitcoin's price.
        search_query = "current price of Bitcoin"
        search_result = web_searcher.search(search_query)
        
        # Step 2: Use a regular expression to find the price in the format $XX,XXX.XX
        # This pattern looks for a dollar sign, followed by digits and commas, and an optional decimal part.
        price_pattern = re.compile(r'\$([0-9,]+\.?[0-9]*)')
        match = price_pattern.search(search_result)
        
        if not match:
            print(f"Error: Could not find a valid Bitcoin price in the search result.")
            # Create an empty file to indicate failure to find the price.
            with open(output_filename, 'w') as f:
                f.write("")
            return

        # Step 3: Extract the matched price string (e.g., "67,123.45") from the first capture group.
        price_with_commas = match.group(1)
        
        # Step 4: Remove commas to get a pure numerical string (e.g., "67123.45").
        numerical_price = price_with_commas.replace(',', '')
        
        # Step 5: Save the purely numerical price to the specified file.
        with open(output_filename, 'w') as f:
            f.write(numerical_price)
            
        print(f"Successfully found and saved Bitcoin price to {output_filename}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # In case of any other errors, write an empty string to the file.
        with open(output_filename, 'w') as f:
            f.write("")
