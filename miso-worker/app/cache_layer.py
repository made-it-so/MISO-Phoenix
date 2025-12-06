import os
import os
import json
import logging
import numpy as np
import redis
import google.generativeai as genai

# CONFIG
REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
SIMILARITY_THRESHOLD = 0.92 # 92% match required

logger = logging.getLogger('SemanticCache')
logger.setLevel(logging.INFO)

class SemanticCache:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # Connect to Redis
        try:
            self.redis = redis.Redis(host=REDIS_HOST, port=6379, db=0, socket_connect_timeout=1)
            self.redis.ping()
            logger.info("✅ Redis Memory Bank Connected.")
        except:
            self.redis = None
            logger.warning("⚠️ Cache Offline.")

    def _get_embedding(self, text):
        """Converts text to a vector of numbers."""
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Embedding Fail: {e}")
            return None

    def _cosine_similarity(self, vec_a, vec_b):
        """Calculates how similar two thoughts are."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def check(self, prompt):
        if not self.redis: return None
        
        # 1. Embed the new prompt
        query_vec = self._get_embedding(prompt)
        if not query_vec: return None

        # 2. Linear Scan (Proof of Concept implementation)
        # In Prod, use RediSearch or Pinecone for O(log n)
        keys = self.redis.keys("cache:*:meta")
        best_score = 0
        best_response = None

        for key in keys:
            # Fetch stored vector
            data = json.loads(self.redis.get(key))
            stored_vec = data['vector']
            
            score = self._cosine_similarity(query_vec, stored_vec)
            
            if score > best_score:
                best_score = score
                best_response = data['response']

        # 3. Decision
        if best_score >= SIMILARITY_THRESHOLD:
            logger.info(f"🧠 CACHE HIT (Similarity: {best_score:.2f}). Saving Logic Cycles.")
            return best_response
        
        return None

    def store(self, prompt, response):
        if not self.redis: return
        
        vec = self._get_embedding(prompt)
        if not vec: return
        
        # Store Logic
        data = {
            "vector": vec,
            "response": response,
            "prompt": prompt
        }
        # Use hash of prompt as ID
        key_id = hash(prompt)
        self.redis.set(f"cache:{key_id}:meta", json.dumps(data), ex=3600) # 1 Hour TTL

