import os
import ast
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.critic")

class HypercriticalLobe:
    """
    The Superego. 
    Analyzes code for Architectural Fit (Top-Down) and Security (Bottom-Up).
    """
    def __init__(self, project_root="."):
        self.root = os.path.abspath(project_root)

    def _check_architecture(self, file_path: str) -> Tuple[bool, str]:
        # Rule: Core logic must be in 'miso_project'
        if "miso_project" not in file_path and file_path not in ["main.py", "dashboard.py"]:
            return False, "VIOLATION: Code placed outside 'miso_project/' directory."
        return True, "PASS"

    def _check_security(self, code: str) -> List[str]:
        issues = []
        if "sk-" in code and "os.getenv" not in code:
            issues.append("CRITICAL: Hardcoded API Key detected.")
        if "eval(" in code or "exec(" in code:
            issues.append("CRITICAL: Use of eval/exec is forbidden.")
        if "subprocess" in code and "DockerSandbox" not in code:
            issues.append("WARNING: Direct subprocess call. Use DockerSandbox instead.")
        return issues

    def critique(self, file_path: str, code: str) -> Dict[str, str]:
        """
        Returns {'verdict': 'PASS'|'FAIL', 'reason': ...}
        """
        # 1. Top-Down Analysis
        arch_pass, arch_msg = self._check_architecture(file_path)
        if not arch_pass:
            return {"verdict": "FAIL", "reason": arch_msg}

        # 2. Bottom-Up Analysis
        issues = self._check_security(code)
        if any("CRITICAL" in i for i in issues):
            return {"verdict": "FAIL", "reason": "\n".join(issues)}
        
        return {"verdict": "PASS", "reason": "Code meets Bio-Fintech standards."}
