def solve(input_str: str) -> str:
    """
    Reads Bitcoin and Ethereum prices from 'btc_price.txt' and 'eth_price.txt',
    calculates the ratio (BTC price / ETH price), and saves a formatted
    report string to 'crypto_ratio.txt'.
    """
    btc_price_file = 'btc_price.txt'
    eth_price_file = 'eth_price.txt'
    output_file = 'crypto_ratio.txt'

    try:
        # Read the Bitcoin price from its file
        with open(btc_price_file, 'r') as f:
            btc_price_str = f.read().strip()
        btc_price = float(btc_price_str)

        # Read the Ethereum price from its file
        with open(eth_price_file, 'r') as f:
            eth_price_str = f.read().strip()
        eth_price = float(eth_price_str)

        # Ensure ETH price is not zero to avoid division errors
        if eth_price == 0:
            return "Error: Ethereum price is zero, cannot calculate ratio."

        # Calculate how many ETH are equal to 1 BTC
        ratio = btc_price / eth_price

        # Format the final report string
        report = f"1 BTC = {ratio:.2f} ETH"

        # Write the report to the output file
        with open(output_file, 'w') as f:
            f.write(report)
            
        return f"Successfully saved report to '{output_file}'."

    except FileNotFoundError as e:
        # Handle cases where one of the price files is missing
        return f"Error: Price file not found: {e.filename}"
    except ValueError:
        # Handle cases where file content is not a valid number
        return "Error: Invalid number format in price file(s)."
    except Exception as e:
        # Catch any other unexpected errors
        return f"An unexpected error occurred: {e}"