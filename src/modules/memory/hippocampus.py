import chromadb
import logging
import os
import json

logger = logging.getLogger('MISO')

class Hippocampus:
    def __init__(self, persistence_path='miso_memory_db'):
        try:
            self.client = chromadb.PersistentClient(path=persistence_path)
            self.collection = self.client.get_or_create_collection(name='solution_cache')
            logger.info(f'Hippocampus: Online ({self.collection.count()} memories)')
        except Exception as e:
            logger.error(f'Hippocampus Init Failed: {e}')
            self.client = None

    def recall(self, query, threshold=0.3):
        """Returns cached code if a semantically similar problem was solved before."""
        if not self.client: return None
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=1
            )
            
            if not results['ids'][0]: return None
            
            # Check distance (lower is better in Chroma defaults usually, but depends on metric)
            # Simple check: if we have a result, return it. In prod, tune the threshold.
            # Using distances[0][0] < threshold logic if needed.
            
            code = results['documents'][0][0]
            metadata = results['metadatas'][0][0]
            logger.info(f'Hippocampus: Recall Hit! (ID: {results["ids"][0][0]})')
            return {'code': code, 'metadata': metadata}
        except Exception as e:
            logger.error(f'Recall Error: {e}')
            return None

    def memorize(self, problem, code, score):
        """Stores a successful solution."""
        if not self.client or score < 1.0: return
        
        try:
            # Create a unique ID based on the problem hash or timestamp
            mem_id = f'mem_{abs(hash(problem))}'
            
            self.collection.upsert(
                documents=[code],
                metadatas=[{'problem': problem, 'score': score}],
                ids=[mem_id]
            )
            logger.info(f'Hippocampus: Memorized solution for "{problem[:20]}..."')
        except Exception as e:
            logger.error(f'Memorize Error: {e}')