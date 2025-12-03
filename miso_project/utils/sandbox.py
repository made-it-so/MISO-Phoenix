import docker
import tarfile
import io
import time
import logging
from typing import Dict, Optional

# Rigid Logging
logger = logging.getLogger("miso.backbone.sandbox")

class DockerSandbox:
    """
    The Immune System's Enforcer.
    Executes untrusted code in a strictly isolated, ephemeral Docker container.
    """
    
    def __init__(self, image: str = "python:3.11-slim"):
        try:
            self.client = docker.from_env()
            self.image = image
            self._pull_image_if_missing()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            # We don't raise here to allow Cortex boot, but sandbox will fail if called
            self.client = None

    def _pull_image_if_missing(self):
        try:
            self.client.images.get(self.image)
        except docker.errors.ImageNotFound:
            logger.info(f"Backbone: Pulling sandbox image {self.image}...")
            self.client.images.pull(self.image)

    def _create_context_tar(self, code: str, filename: str = "script.py") -> bytes:
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            data = code.encode('utf-8')
            tar_info = tarfile.TarInfo(name=filename)
            tar_info.size = len(data)
            tar_info.mtime = time.time()
            tar.addfile(tarinfo=tar_info, fileobj=io.BytesIO(data))
        tar_stream.seek(0)
        return tar_stream.read()

    def execute(self, 
                code: str, 
                timeout: int = 10, 
                memory_limit: str = "128m", 
                cpu_quota: int = 50000) -> Dict[str, str]:
        
        if not self.client:
            return {"status": "error", "stdout": "", "stderr": "Docker client not initialized."}

        container = None
        try:
            # Spin up the container (The Cell)
            container = self.client.containers.run(
                self.image,
                command="python /app/script.py",
                detach=True,
                network_disabled=True,
                mem_limit=memory_limit,
                cpu_period=100000,
                cpu_quota=cpu_quota,
                working_dir="/app",
                tty=False
            )

            # Inject Code
            container.put_archive("/app", self._create_context_tar(code))

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
            if container:
                try: container.remove(force=True)
                except: pass
