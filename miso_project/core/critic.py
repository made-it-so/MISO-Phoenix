import os
import ast
import logging
import json
import re
from typing import Dict, Any, List, Tuple

from miso_project.core.research import ResearchScout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.critic")

class HypercriticalLobe:
    def __init__(self, project_root="."):
        self.root = os.path.abspath(project_root)
        self.scout = ResearchScout()

    def _generate_god_view(self) -> str:
        tree = []
        for root, dirs, files in os.walk(self.root):
            if any(x in root for x in ["venv", "__pycache__", ".git"]): continue
            level = root.replace(self.root, '').count(os.sep)
            indent = ' ' * 4 * level
            tree.append(f"{indent}{os.path.basename(root)}/")
            for f in files:
                tree.append(f"{' ' * 4 * (level + 1)}{f}")
        return "\n".join(tree)

    def _check_architectural_fit(self, file_path: str, code: str) -> Tuple[bool, str]:
        if "miso_project" not in file_path and file_path not in ["main.py", "dashboard.py"]:
            return False, "ARCHITECTURAL VIOLATION: Code placed outside miso_project/"
        return True, "Architecture Sound."

    def _scan_security(self, code: str) -> List[str]:
        issues = []
        if "sk-" in code and "os.getenv" not in code: issues.append("CRITICAL: Hardcoded API Key.")
        if "eval(" in code: issues.append("CRITICAL: Use of eval() is forbidden.")
        return issues

    def _clean_query(self, raw_issue: str) -> str:
        clean = raw_issue.replace("CRITICAL:", "").replace("WARNING:", "").split("by")[0]
        clean = clean.replace("()", "").replace("_", " ")
        if "eval" in clean: return "Python security eval code injection prevention"
        if "API Key" in clean: return "Python secure API key environment variables"
        return f"Python best practices {clean.strip()}"

    def critique_and_research(self, file_path: str, code: str) -> Dict[str, Any]:
        """Reactive Check (Single File)"""
        # (Same logic as before, just ensuring it uses the updated _scan methods)
        arch_pass, arch_msg = self._check_architectural_fit(file_path, code)
        if not arch_pass:
            return {"verdict": "FAIL", "reason": arch_msg, "context": self.scout.search_papers("Python project structure")}
        
        sec_issues = self._scan_security(code)
        if sec_issues:
            query = self._clean_query(sec_issues[0])
            return {"verdict": "FAIL", "reason": sec_issues[0], "context": self.scout.search_papers(query)}
            
        return {"verdict": "PASS"}

    def audit_organism(self) -> List[Dict[str, Any]]:
        """
        PROACTIVE LOOP: Walks the entire body looking for cancer/rot.
        Returns a list of 'Actionable Insights' to be fixed.
        """
        logger.info(">>> INITIATING SYSTEM-WIDE PROACTIVE AUDIT...")
        report = []
        
        for root, dirs, files in os.walk(self.root):
            if any(x in root for x in ["venv", "__pycache__", ".git"]): continue
            
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r') as f:
                            code = f.read()
                        
                        # We run the critique quietly
                        result = self.critique_and_research(full_path, code)
                        
                        if result["verdict"] == "FAIL":
                            logger.warning(f"Audit Flag: {file} -> {result['reason']}")
                            report.append({
                                "file": full_path,
                                "issue": result["reason"],
                                "research": result.get("context", [])
                            })
                    except Exception as e:
                        logger.error(f"Audit Error on {file}: {e}")
                        
        logger.info(f"Audit Complete. Found {len(report)} issues.")
        return report

# --- VERIFICATION ---
if __name__ == "__main__":
    critic = HypercriticalLobe()
    # Create a dummy bad file to catch
    with open("miso_project/utils/audit_bait.py", "w") as f:
        f.write("x = eval('input')")
        
    report = critic.audit_organism()
    print(f"\nAudit Report Size: {len(report)}")
    if len(report) > 0:
        print(f"Caught Issue: {report[0]['issue']}")
        print(f"Suggested Paper: {report[0]['research'][0]['title']}")
    
    # Cleanup
    os.remove("miso_project/utils/audit_bait.py")
