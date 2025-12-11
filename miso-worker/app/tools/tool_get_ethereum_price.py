import re

# This is a mock web_searcher for a self-contained and testable solution.
# In a real environment, this tool would be provided.
class WebSearcher:
    def search(self, query: str) -> str:
        """Mocks a web search, returning a string with the price."""
        if "current price of ethereum" in query.lower():
            # A realistic search result snippet
            return "According to top sources, the live price of Ethereum today is $3,512.45 USD with a 24-hour trading volume of $14.8B USD."
        return "Search did not return relevant results."

web_searcher = WebSearcher()

def solve(input_str: str) -> str:
    """
    Searches for the current price of Ethereum, extracts the dollar amount,
    and saves it to a file named 'eth_price.txt'.

    Args:
        input_str (str): The input string (unused, but required by the interface).
    
    Returns:
        str: A message indicating the outcome.
    """
    # The task is specific, so the query is hardcoded.
    query = "current price of Ethereum"
    
    try:
        # Step 1: Search using the web_searcher tool
        search_results = web_searcher.search(query)
        
        # Step 2: Extract the dollar amount using a regular expression
        # This regex matches a dollar sign followed by digits, optional commas, and an optional decimal part.
        price_pattern = r'\$([0-9,]+\.?[0-9]*)'
        match = re.search(price_pattern, search_results)
        
        if not match:
            return "Failed to find a dollar amount in the search results."
            
        # Extract the full price string, e.g., "$3,512.45"
        price_str = match.group(0)
        
        # Step 3: Save the extracted price to a file
        file_name = 'eth_price.txt'
        with open(file_name, 'w') as f:
            f.write(price_str)
            
        return f"Successfully found price '{price_str}' and saved it to '{file_name}'."
        
    except Exception as e:
        return f"An error occurred: {e}"
