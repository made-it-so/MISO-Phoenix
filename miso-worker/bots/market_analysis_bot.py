import os
import requests
import time
import json
import sys

# --- Configuration ---
# Get your free API key from https://www.alphavantage.co/support/#api-key
# It's recommended to set this as an environment variable for security.
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
BASE_URL = 'https://www.alphavantage.co/query'

# List of stock symbols to track
SYMBOLS_TO_TRACK = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA']

# Time interval between fetches (in seconds)
# Note: The free Alpha Vantage plan has a limit of 25 requests per day.
# Set this to a high value (e.g., 3600 for 1 hour) to stay within limits.
FETCH_INTERVAL = 3600

def get_stock_quote(symbol):
    """
    Fetches the latest stock quote for a given symbol from Alpha Vantage.
    """
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol,
        'apikey': API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()

        # Alpha Vantage returns a 'Note' if the API limit is reached
        if "Note" in data:
            print(f"API Limit Reached: {data['Note']}")
            return None
            
        # Check for the actual quote data
        quote = data.get('Global Quote')
        if not quote:
            print(f"Warning: Could not retrieve quote for {symbol}. Response: {data}")
            return None
            
        return quote

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON response for {symbol}.")
        return None

def display_analysis(quote_data):
    """
    Formats and prints the stock analysis.
    """
    if not quote_data:
        return

    try:
        symbol = quote_data.get('01. symbol', 'N/A')
        price = float(quote_data.get('05. price', 0))
        change_percent_str = quote_data.get('10. change percent', '0%')
        change_percent = float(change_percent_str.replace('%', ''))
        volume = int(quote_data.get('06. volume', 0))

        print(f"--- Analysis for {symbol} ---")
        print(f"  Price: ")
        print(f"  Volume: {volume:,}")
        
        if change_percent > 0:
            print(f"  Change: +{change_percent:.2f}% (UP)")
        elif change_percent < 0:
            print(f"  Change: {change_percent:.2f}% (DOWN)")
        else:
            print("  Change: 0.00% (NO CHANGE)")
        print("-" * (20 + len(symbol)))

    except (ValueError, TypeError) as e:
        print(f"Error processing data for symbol: {e}. Raw data: {quote_data}")


def main():
    """
    Main loop to run the market analysis bot.
    """
    print("--- MISO V19: Market Analysis Bot ---")
    print(f"Tracking: {', '.join(SYMBOLS_TO_TRACK)}")
    print(f"Fetch Interval: {FETCH_INTERVAL} seconds")
    print("---------------------------------------")

    if not API_KEY:
        print("FATAL ERROR: ALPHA_VANTAGE_API_KEY environment variable not set.")
        print("Please get a key from alphavantage.co and set the variable.")
        sys.exit(1)

    while True:
        print(f"\nFetching new data at {time.ctime()}...")
        for symbol in SYMBOLS_TO_TRACK:
            quote = get_stock_quote(symbol)
            if quote:
                display_analysis(quote)
            # Short delay between individual API calls to be polite to the server
            time.sleep(2) 
        
        print(f"Sleeping for {FETCH_INTERVAL} seconds...")
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main()
