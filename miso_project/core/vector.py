import os
import logging
from typing import List, Dict
from qdrant_client import QdrantClient

# Rigid Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.memory.vector")

class VectorHippocampus:
    """
    The Semantic Memory System.
    Stores abstract concepts (Vectors) for long-term recall.
    Uses 'fastembed' for local, zero-cost embedding generation.
    """
    
    def __init__(self):
        # We use a local persistent path to avoid network complexity
        self.db_path = "miso_memory_db"
        self.client = QdrantClient(path=self.db_path)
        self.collection_name = "research_insights"
        
        # Initialize Memory Structure (if not exists)
        self._init_synapses()

    def _init_synapses(self):
        try:
            # Check if collection exists
            if not self.client.collection_exists(self.collection_name):
                logger.info("Initializing new Memory Collection...")
                # Qdrant local handles vector config automatically with 'add'
                pass 
        except Exception as e:
            logger.error(f"Memory Init Error: {e}")

    def store_insight(self, text: str, metadata: Dict):
        """Long-Term Potentiation: Encoding a memory."""
        try:
            logger.info(f"Encoding memory: {text[:50]}...")
            self.client.add(
                collection_name=self.collection_name,
                documents=[text],
                metadata=[metadata]
            )
            logger.info("Memory consolidated.")
        except Exception as e:
            logger.error(f"Encoding Failed: {e}")

    def recall(self, query: str, limit: int = 3) -> str:
        """Associative Recall: Fetching relevant memories."""
        try:
            logger.info(f"Recalling memories for: {query}")
            results = self.client.query(
                collection_name=self.collection_name,
                query_text=query,
                limit=limit
            )
            
            if not results:
                return ""
            
            # Synthesize context
            context_block = "\n-- RELEVANT PAST MEMORIES --\n"
            for hit in results:
                # hit.metadata is the stored dict, hit.document is the text
                context_block += f"* {hit.document} (Source: {hit.metadata.get('source', 'Unknown')})\n"
            context_block += "----------------------------\n"
            return context_block
            
        except Exception as e:
            # If collection doesn't exist yet, return empty
            if "not found" in str(e): return ""
            logger.error(f"Recall Failed: {e}")
            return ""
