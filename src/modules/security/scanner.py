import subprocess
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='[SEC-SCANNER] %(message)s')
logger = logging.getLogger("SecurityScanner")

class SecurityScanner:
    def __init__(self, target_dir="/app"):
        self.target_dir = target_dir

    def run_scan(self):
        """Executes Trivy FS scan and returns parsed High/Critical vulns."""
        output_file = "/tmp/trivy_report.json"
        
        # Run Trivy (Quiet mode, JSON output, only High/Critical)
        cmd = f"trivy fs {self.target_dir} --format json --output {output_file} --severity HIGH,CRITICAL --scanners vuln"
        
        try:
            logger.info(f"Starting Security Scan on {self.target_dir}...")
            subprocess.run(cmd, shell=True, check=True)
            
            if not os.path.exists(output_file):
                return {"error": "Scan failed to generate report file."}

            with open(output_file, 'r') as f:
                data = json.load(f)

            # Parse Results
            vulnerabilities = []
            if "Results" in data:
                for result in data["Results"]:
                    target = result.get("Target", "Unknown")
                    for vuln in result.get("Vulnerabilities", []):
                        vulnerabilities.append({
                            "pkg": vuln.get("PkgName"),
                            "id": vuln.get("VulnerabilityID"),
                            "severity": vuln.get("Severity"),
                            "fixed_in": vuln.get("FixedVersion", "N/A"),
                            "target": target
                        })
            
            logger.info(f"Scan Complete. Found {len(vulnerabilities)} issues.")
            return {"status": "success", "count": len(vulnerabilities), "issues": vulnerabilities}

        except subprocess.CalledProcessError as e:
            logger.error(f"Trivy crash: {e}")
            return {"status": "error", "details": str(e)}
        except json.JSONDecodeError:
            return {"status": "error", "details": "Failed to parse Trivy JSON output"}

if __name__ == "__main__":
    scanner = SecurityScanner()
    print(json.dumps(scanner.run_scan(), indent=2))
