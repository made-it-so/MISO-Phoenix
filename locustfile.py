from locust import HttpUser, task, between
import random

class MisoUser(HttpUser):
    wait_time = between(1, 5)

    # We target the API running inside Docker/Localhost
    # The host is passed via command line, e.g., http://localhost:8000
    
    @task(3)
    def easy_task(self):
        # Simulating "Easy" tasks (should hit Flash)
        self.client.post("/miso/trigger", json={
            "session_id": f"USER_{random.randint(1, 1000)}",
            "description": "Tell me a joke about cloud computing",
            "api_key": "TEST_KEY" # Replace if auth is enforced
        })

    @task(1)
    def hard_task(self):
        # Simulating "Hard" tasks (should hit Pro)
        self.client.post("/miso/trigger", json={
            "session_id": f"USER_{random.randint(1, 1000)}",
            "description": "Write a secure, multi-threaded C++ kernel module for packet filtering",
            "api_key": "TEST_KEY"
        })
