import docker
import tarfile
import io
import time
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger("miso.backbone.sandbox")

class DockerSandbox:
    """
    The Immune System's Enforcer (V92 - Trusted Mode).
    Supports 'Trusted' execution (Network + Creds) for DevOps tasks.
    """
    
    def __init__(self, image: str = "miso-worker:latest"):
        try:
            self.client = docker.from_env()
            self.image = image
            self._pull_image_if_missing()
            self.host_path = os.getcwd()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def _pull_image_if_missing(self):
        try:
            self.client.images.get(self.image)
        except docker.errors.ImageNotFound:
            logger.info(f"Backbone: Pulling sandbox image {self.image}...")
            # If local image missing, we might fail or try to pull base
            pass

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
                timeout: int = 15, 
                memory_limit: str = "256m", 
                cpu_quota: int = 50000,
                trusted: bool = False) -> Dict[str, str]:
        
        if not self.client:
            return {"status": "error", "stdout": "", "stderr": "Docker client not initialized."}

        container = None
        try:
            # 1. Configure Environment
            env_vars = {}
            if trusted:
                # Inject Cloud Credentials for DevOps tasks
                env_vars = {
                    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
                    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
                    "AWS_SESSION_TOKEN": os.getenv("AWS_SESSION_TOKEN"),
                    "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                    "PYTHONPATH": "/app"
                }

            # 2. Configure Networking
            # If trusted, allow network. If not, strictly disable.
            network_mode = "bridge" if trusted else "none"

            # 3. Mounts
            volumes = {self.host_path: {'bind': '/app', 'mode': 'rw'}}

            # 4. Spin up
            container = self.client.containers.run(
                self.image,
                command="python execution_script.py",
                detach=True,
                network_mode=network_mode,  # <--- The Switch
                environment=env_vars,       # <--- The Keys
                mem_limit=memory_limit,
                cpu_period=100000,
                cpu_quota=cpu_quota,
                working_dir="/app",
                volumes=volumes,
                tty=False
            )

            # Write script to host volume
            script_path = os.path.join(self.host_path, "execution_script.py")
            with open(script_path, "w") as f:
                f.write(code)

            # Monitor
            start_time = time.time()
            while container.status in ['created', 'running']:
                container.reload()
                if time.time() - start_time > timeout:
                    container.kill()
                    return {"status": "timeout", "stdout": "", "stderr": "Execution timed out."}
                time.sleep(0.1)

            # Harvest
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
            if os.path.exists("execution_script.py"): os.remove("execution_script.py")
            if container:
                try: container.remove(force=True)
                except: pass
