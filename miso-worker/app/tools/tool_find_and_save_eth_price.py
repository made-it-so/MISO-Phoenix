import re

def solve(input_str: str) -> str:
    """
    This tool uses the web_searcher to find the current price of Ethereum (ETH)
    and saves the numerical value to a file named 'eth_price.txt'.

    The web_searcher tool is expected to be provided in the execution environment.
    """
    query = "current price of Ethereum in USD"

    try:
        # Use the provided web_searcher tool to get information.
        search_results = web_searcher.search(query)

        if not search_results:
            return "Error: Web search did not return any results for the Ethereum price."

        # Use regex to find a pattern like $3,500.50 or $4000
        # This captures the numerical part of the price.
        price_pattern = re.compile(r'\$([\d,]+\.?\d*)')
        match = price_pattern.search(search_results)

        if match:
            # Extract the matched price string, e.g., "3,500.50"
            price_str = match.group(1)
            # Remove commas to store a clean number, e.g., "3500.50"
            price_value = price_str.replace(',', '')

            # Define the output file name
            output_filename = 'eth_price.txt'

            # Save the cleaned price to the file
            with open(output_filename, 'w') as f:
                f.write(price_value)

            return f"Successfully found and saved the current price of Ethereum (${price_value}) to '{output_filename}'."
        else:
            return f"Error: Could not find the price of Ethereum in the search results. Search results: {search_results[:200]}..."

    except NameError:
        return "Error: The 'web_searcher' tool is not defined or available in the environment."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
