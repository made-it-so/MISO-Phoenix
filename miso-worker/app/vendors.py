import requests
import logging

logger = logging.getLogger(__name__)

class CloudVendor:
    def compute(self, payload, api_key):
        raise NotImplementedError

class GCPVendor(CloudVendor):
    def compute(self, payload, api_key):
        logger.info("🔌 Connecting to GCP Compute Engine...")
        # Simulating outbound call to httpbin
        url = "https://httpbin.org/post" 
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-MISO-Target": "GCP-TPU-v4"
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            # httpbin echoes our IP in 'origin'. We use this to prove connectivity.
            return f"OPTIMAL_GCP_RESULT_ID_{data.get('origin', 'UNKNOWN')[:4]}"
        except Exception as e:
            logger.error(f"❌ GCP Network Failure: {e}")
            raise

class AzureVendor(CloudVendor):
    def compute(self, payload, api_key):
        logger.info("🔌 Connecting to Azure Batch...")
        url = "https://httpbin.org/post"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            return f"OPTIMAL_AZURE_RESULT_ID_{data.get('origin', 'UNKNOWN')[:4]}"
        except Exception as e:
            logger.error(f"❌ Azure Network Failure: {e}")
            raise

def get_vendor_adapter(cloud_target):
    if cloud_target == "GCP": return GCPVendor()
    elif cloud_target == "AZURE": return AzureVendor()
    else: raise ValueError(f"Unknown Vendor: {cloud_target}")
