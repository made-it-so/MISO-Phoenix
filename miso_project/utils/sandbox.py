import docker
import tarfile
import io
import time
import logging
import os
from typing import Dict, Optional

# Rigid Logging
logger = logging.getLogger("miso.backbone.sandbox")

class DockerSandbox:
    """
    The Immune System's Enforcer (V2 - Tactile).
    Now mounts the current working directory so file changes persist.
    """
    
    def __init__(self, image: str = "python:3.11-slim"):
        try:
            self.client = docker.from_env()
            self.image = image
            self._pull_image_if_missing()
            # We map the Host's current folder to /app in the container
            self.host_path = os.getcwd()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def _pull_image_if_missing(self):
        try:
            self.client.images.get(self.image)
        except docker.errors.ImageNotFound:
            logger.info(f"Backbone: Pulling sandbox image {self.image}...")
            self.client.images.pull(self.image)

    def execute(self, 
                code: str, 
                timeout: int = 10, 
                memory_limit: str = "128m", 
                cpu_quota: int = 50000) -> Dict[str, str]:
        
        if not self.client:
            return {"status": "error", "stdout": "", "stderr": "Docker client not initialized."}

        container = None
        try:
            # PROPRIOCEPTION: Mount the host directory so files persist
            volumes = {
                self.host_path: {'bind': '/app', 'mode': 'rw'}
            }

            # Create the script file directly on the host first
            # This avoids complex tar injection issues with mounted volumes overwriting
            script_path = os.path.join(self.host_path, "execution_script.py")
            with open(script_path, "w") as f:
                f.write(code)

            # Spin up the container (The Cell)
            container = self.client.containers.run(
                self.image,
                command="python execution_script.py", # Run the mounted script
                detach=True,
                network_disabled=True, # Still airgapped network-wise
                mem_limit=memory_limit,
                cpu_period=100000,
                cpu_quota=cpu_quota,
                working_dir="/app",
                volumes=volumes, # <--- The Bridge to Reality
                tty=False
            )

            # Monitor Lifecycle
            start_time = time.time()
            while container.status in ['created', 'running']:
                container.reload()
                if time.time() - start_time > timeout:
                    container.kill()
                    return {"status": "timeout", "stdout": "", "stderr": "Execution timed out."}
                time.sleep(0.1)

            # Harvest Results
            result = container.wait()
            logs = container.logs(stdout=True, stderr=True)
            output = logs.decode('utf-8', errors='ignore')
            
            exit_code = result.get('StatusCode', 1)
            status = "success" if exit_code == 0 else "error"

            return {
                "status": status,
                "stdout": output if status == "success" else "",
                "stderr": output if status != "success" else "",
                "exit_code": str(exit_code)
            }

        except Exception as e:
            return {"status": "system_failure", "stdout": "", "stderr": str(e)}
        finally:
            # Cleanup the temporary script
            if os.path.exists("execution_script.py"):
                os.remove("execution_script.py")
            if container:
                try: container.remove(force=True)
                except: pass
