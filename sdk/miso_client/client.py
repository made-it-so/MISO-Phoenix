import requests
import json
import os

class Miso:
    """
    The MISO Hypervisor Client.
    """
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url

    def think(self, prompt: str) -> dict:
        return self._send("chat", prompt)

    def research(self, topic: str) -> dict:
        return self._send("research", topic)

    def _send(self, task_type: str, payload: str) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"type": task_type, "payload": payload}
        try:
            res = requests.post(f"{self.base_url}/process", json=data, headers=headers)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
