import os
import chromadb
import uuid
from chromadb.utils import embedding_functions

# --- BIOLOGICAL MEMORY ---
# "Replay of sequences underlies episodic memory formation" [Nature Neuroscience]
# This module acts as the Hippocampus, encoding experiences into stable vector storage.

class Hippocampus:
    def __init__(self):
        # Initialize persistent local vector store
        self.client = chromadb.PersistentClient(path="miso_memory_db")
        
        # Use Google's embedding model if available, otherwise default
        # (Chroma uses all-MiniLM-L6-v2 by default which is fine for local)
        self.collection = self.client.get_or_create_collection(
            name="miso_episodic_memory",
            metadata={"hnsw:space": "cosine"} # Measures semantic similarity
        )
        print("--- HIPPOCAMPUS (VECTOR MEMORY) ONLINE ---")

    def remember(self, task_description, code_solution, outcome="SUCCESS"):
        """
        Encodes a completed task into long-term memory.
        """
        memory_id = str(uuid.uuid4())
        
        self.collection.add(
            documents=[task_description], # We embed the QUESTION
            metadatas=[{"solution": code_solution, "outcome": outcome}], # We store the ANSWER
            ids=[memory_id]
        )
        return f"Memory encoded: {memory_id}"

    def recall(self, query_text, n_results=1):
        """
        Retrieves relevant past experiences.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        if not results['documents'][0]:
            return None
            
        # Return the most relevant past solution
        best_match = results['metadatas'][0][0]['solution']
        distance = results['distances'][0][0]
        
        # Biological Threshold: If memory is too vague (distance > 0.5), ignore it.
        if distance > 0.5:
            return None
            
        return best_match

if __name__ == "__main__":
    # Test the cortex
    brain = Hippocampus()
    brain.remember("Write a hello world script", "print('Hello World')")
    print(f"Recall Test: {brain.recall('coding a greeting script')}")
