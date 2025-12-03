import os
import json
import logging
import google.generativeai as genai
from celery import Celery
from typing import Dict, Any

# Import Organs
from miso_project.core.research import ResearchScout
from miso_project.utils.sandbox import DockerSandbox
from miso_project.core.critic import HypercriticalLobe

# Configure Hive
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery('miso_swarm', broker=redis_url, backend=redis_url)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.swarm")

def _generate_insight(query: str, papers: list) -> str:
    """Helper: Uses Gemini to synthesize research."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key: return "Insight generation failed: Missing Credentials."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"Synthesize a brief strategic insight based on these papers regarding '{query}':\n{json.dumps(papers)}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Insight generation error: {e}"

@celery_app.task(bind=True)
def perform_research_task(self, query: str) -> Dict[str, Any]:
    """
    Background Task: Deep Research + Synthesis
    """
    logger.info(f"Drone {self.request.id}: Scouting '{query}'...")
    scout = ResearchScout()
    
    # 1. Search
    papers = scout.search_papers(query)
    
    # 2. Synthesize (The Missing Link)
    insight = _generate_insight(query, papers)
    
    return {
        "status": "complete", 
        "papers": papers, 
        "insight": insight, # <--- Dashboard looks for this!
        "source": "arxiv"
    }

@celery_app.task(bind=True)
def perform_reflex_action(self, code: str) -> Dict[str, Any]:
    # (Same as before)
    logger.info(f"Drone {self.request.id}: Executing Reflex...")
    critic = HypercriticalLobe()
    verdict = critic.critique("miso_project/utils/transient_action.py", code)
    
    if verdict["verdict"] == "FAIL":
        return {"status": "rejected", "output": f"CRITIC BLOCKED: {verdict['reason']}"}
        
    sandbox = DockerSandbox()
    result = sandbox.execute(code)
    
    return {
        "status": result["status"],
        "output": result["stdout"] or result["stderr"]
    }
