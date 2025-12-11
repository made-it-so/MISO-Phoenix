from duckduckgo_search import DDGS
import itertools

def solve(input_str: str) -> str:
    """
    Performs a web search using DuckDuckGo for a given query and returns the top 3 results.

    Args:
        input_str: The search query string.

    Returns:
        A formatted string containing the titles and URLs of the top 3 search results,
        or an error message if the search fails or no results are found.
    """
    try:
        # The DDGS context manager is recommended for proper session management
        with DDGS() as ddgs:
            # Fetch the top 3 search results.
            results = list(itertools.islice(ddgs.text(keywords=input_str, max_results=3), 3))

            if not results:
                return "No results found."

            # Format the results into a readable string
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get('title', 'N/A')
                url = result.get('href', 'N/A')
                formatted_results.append(f"{i}. Title: {title}\n   URL: {url}")
            
            return "\n\n".join(formatted_results)
            
    except Exception as e:
        return f"An error occurred while searching: {e}"