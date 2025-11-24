import os
import requests
import json
import argparse
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ApolloClient:
    """
    A client for interacting with the Apollo.io API.
    """
    BASE_URL = "https://api.apollo.io/v1"

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Apollo API key is required.")
        self.api_key = api_key

    def search_people(self, country, industry, titles=None, page=1, per_page=25):
        """
        Searches for people (leads) based on specified criteria.

        Args:
            country (str): The target country (e.g., 'United States').
            industry (str): The target industry (e.g., 'Computer Software').
            titles (list, optional): A list of job titles to target. Defaults to a standard list.
            page (int, optional): The page number for pagination. Defaults to 1.
            per_page (int, optional): The number of results per page. Defaults to 25.

        Returns:
            dict: The JSON response from the API, or None if an error occurs.
        """
        search_url = f"{self.BASE_URL}/people/search"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

        if titles is None:
            titles = ["CEO", "Founder", "CTO", "Chief Executive Officer", "VP of Engineering", "Head of Sales"]

        payload = {
            "api_key": self.api_key,
            "page": page,
            "per_page": per_page,
            "sort_by_field": "organization_num_employees",
            "sort_ascending": False,
            "person_titles": titles,
            "organization_locations": [country],
            "organization_industries": [industry],
        }

        try:
            logging.info(f"Sending request to Apollo API for Country: {country}, Industry: {industry}")
            response = requests.post(search_url, headers=headers, json=payload)
            response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
            logging.error(f"Response body: {response.text}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error occurred: {req_err}")
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from response.")
        return None

def generate_lead_list(country, industry):
    """
    Main function to generate and save a lead list.
    """
    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key:
        logging.error("APOLLO_API_KEY environment variable not set.")
        logging.error("Please set it before running: export APOLLO_API_KEY='your_key'")
        return

    client = ApolloClient(api_key)
    data = client.search_people(country, industry)

    if data and "people" in data and data["people"]:
        leads = data["people"]
        logging.info(f"Successfully retrieved {len(leads)} leads from Apollo.io.")

        # Sanitize country and industry for filename to prevent path traversal.
        # Allow alphanumeric, spaces, and hyphens. Then replace spaces/hyphens with an underscore.
        s_country = re.sub(r'[^a-zA-Z0-9\s-]', '', country).strip()
        country_fn = re.sub(r'[\s-]+', '_', s_country).lower()

        s_industry = re.sub(r'[^a-zA-Z0-9\s-]', '', industry).strip()
        industry_fn = re.sub(r'[\s-]+', '_', s_industry).lower()

        # Ensure filename is not empty after sanitization
        if not country_fn or not industry_fn:
            logging.error("Invalid country or industry name resulting in an empty filename component after sanitization.")
            return

        output_filename = f"leads_{country_fn}_{industry_fn}.json"

        try:
            with open(output_filename, "w") as f:
                json.dump(leads, f, indent=4)
            logging.info(f"Lead list successfully saved to '{output_filename}'.")

            # Print a summary
            print("\n--- Lead Generation Summary ---")
            print(f"Country: {country}")
            print(f"Industry: {industry}")
            print(f"Leads Found: {len(leads)}")
            print(f"Saved to: {output_filename}")
            print("-----------------------------\n")

        except IOError as e:
            logging.error(f"Failed to write to file {output_filename}: {e}")
    else:
        logging.warning("No leads found for the specified criteria or an API error occurred.")

def main():
    """
    Parses command-line arguments and initiates lead generation.
    """
    parser = argparse.ArgumentParser(
        description="Market Expansion Agent: Generate lead lists using the Apollo.io API."
    )
    parser.add_argument(
        "--country",
        type=str,
        required=True,
        help="Target country for lead generation (e.g., 'Germany')."
    )
    parser.add_argument(
        "--industry",
        type=str,
        required=True,
        help="Target industry code or name (e.g., 'Computer Software', 'Information Technology and Services')."
    )
    args = parser.parse_args()

    generate_lead_list(args.country, args.industry)

if __name__ == "__main__":
    main()
