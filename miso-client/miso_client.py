import requests
import json
from typing import Optional, Literal

# --- FINAL MISO V1 API ENDPOINT ---
MISO_API_URL = "https://miso.stemcultivation.com/task"

class MISOClient:
    """
    The official MISO SDK for generating and submitting Persona Contracts.
    Abstracts the user away from the underlying complexity (e.g., the JSON schema).
    """
    def __init__(self, api_url: str = MISO_API_URL):
        self.api_url = api_url
    
    def submit_task(
        self,
        prompt: str,
        priority: Literal['high', 'normal'] = 'normal',
        max_cost: float = 0.50
    ) -> Optional[dict]:
        """Submits a natural language task to the MISO Persona Broker."""
        
        # Build the structured payload that the Broker expects
        payload = {
            "prompt": prompt,
            "priority": priority,
            "max_cost": max_cost
        }
        
        headers = {'Content-Type': 'application/json'}
        
        print(f"Submitting task to Broker: {self.api_url}")
        
        try:
            response = requests.post(self.api_url, data=json.dumps(payload), headers=headers)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            print(f"FATAL: Network Blocked. Cannot connect to MISO API at {self.api_url}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"ERROR: MISO Broker rejected task (Status {e.response.status_code}).")
            print(f"Response: {e.response.text}")
            return None

# --- TESTING ---
if __name__ == "__main__":
    client = MISOClient()
    
    # Test 1: Simple Task
    print("\n--- Running Simple Task Test ---")
    simple_result = client.submit_task(
        prompt="Explain the difference between IaC and CI/CD in one sentence.",
        priority="normal",
        max_cost=0.01
    )
    print(f"Simple Task Result: {simple_result}")

    # Test 2: Complex Task
    print("\n--- Running Complex Task Test ---")
    complex_result = client.submit_task(
        prompt="Analyze the statefulness vulnerabilities in the Fargate deployment model and propose a fix.",
        priority="high",
        max_cost=0.50
    )
    print(f"Complex Task Result: {complex_result}")

