import arxiv
import logging
from typing import List, Dict

logger = logging.getLogger("miso.core.research")

class ResearchScout:
    """
    The Auto-Didactic Sensor (V77 - Calibrated).
    Scans arXiv with Relevance Sorting to avoid 'Newest Paper' noise.
    """
    
    def __init__(self):
        self.client = arxiv.Client()

    def search_papers(self, query: str, max_results: int = 3) -> List[Dict]:
        logger.info(f"Scouting arXiv for: {query}")
        
        # CRITICAL FIX: Sort by Relevance, not Date
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        try:
            for r in self.client.results(search):
                papers.append({
                    "title": r.title,
                    "summary": r.summary[:500] + "...",
                    "url": r.pdf_url,
                    "published": str(r.published.date())
                })
            return papers
        except Exception as e:
            logger.error(f"Scout Failure: {e}")
            return [{"error": str(e)}]
