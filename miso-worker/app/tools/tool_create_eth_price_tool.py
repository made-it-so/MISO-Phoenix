import re
import os

# The 'web_searcher' tool is assumed to be available in the execution environment.

def solve(input_str: str) -> str:
    """
    A tool that finds the current price of Ethereum using a web search,
    extracts the numerical price, and saves it to 'eth_price.txt'.
    
    Args:
        input_str (str): This input is ignored as the query is fixed to
                         "current price of Ethereum".
    
    Returns:
        str: A message indicating the success or failure of the operation.
    """
    try:
        # This import is expected to work in the execution environment.
        from web_searcher import web_searcher

        # Step 1: Define the search query and use the web_searcher tool.
        query = "current price of Ethereum"
        search_result = web_searcher.search(query=query)

        # Step 2: Use a regular expression to find a price-like number.
        # This pattern looks for numbers with optional commas and a decimal part.
        # Example matches: 3,512.45, 3512.45, 4000
        match = re.search(r'\$?(\d{1,3}(?:,?\d{3})*(?:\.\d+)?)', search_result)

        if not match:
            return f"Error: Could not find a valid numerical price in the search result: '{search_result}'"

        # Step 3: Extract the first matched group and remove commas for a clean number.
        price_str = match.group(1)
        numerical_price = price_str.replace(',', '')

        # Step 4: Write the cleaned numerical price to the specified file.
        file_name = 'eth_price.txt'
        with open(file_name, 'w') as f:
            f.write(numerical_price)

        return f"Successfully saved Ethereum's price ({numerical_price}) to {file_name}."

    except ImportError:
        return "Error: The 'web_searcher' tool is not available in the environment."
    except Exception as e:
        return f"An unexpected error occurred: {e}"