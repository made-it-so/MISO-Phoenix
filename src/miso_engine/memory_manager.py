import chromadb
from chromadb.utils import embedding_functions

class MemoryManager:
    """
    Manages the agent's long-term memory for both experiences and solutions.
    """
    def __init__(self):
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.client = chromadb.Client()
        
        self.experience_collection = self.client.get_or_create_collection(
            name="miso_experiences",
            embedding_function=self.embedding_function
        )
        self.solution_collection = self.client.get_or_create_collection(
            name="miso_solutions",
            embedding_function=self.embedding_function
        )
        
        self.exp_id_counter = 0
        self.sol_id_counter = 0

    def remember_experience(self, experience: str, metadata: dict):
        """Adds a new experience (a summary of a reasoning cycle) to memory."""
        doc_id = f"exp_{self.exp_id_counter}"
        self.experience_collection.add(documents=[experience], metadatas=[metadata], ids=[doc_id])
        self.exp_id_counter += 1

    def remember_solution(self, problem_description: str, solution_code: str):
        """Adds a new, proven solution to the memory."""
        doc_id = f"sol_{self.sol_id_counter}"
        self.solution_collection.add(
            documents=[solution_code],
            metadatas=[{"problem": problem_description}],
            ids=[doc_id]
        )
        self.sol_id_counter += 1

    def recall(self, query: str, n_results: int = 2) -> str:
        """Recalls relevant past experiences and solutions."""
        exp_results = self.experience_collection.query(query_texts=[query], n_results=n_results)
        sol_results = self.solution_collection.query(query_texts=[query], n_results=n_results)
        
        recalled = "No relevant memories found."
        
        if exp_results['documents'] and exp_results['documents'][0]:
            recalled_exp = "\n".join([f"- Past Experience: {doc}" for doc in exp_results['documents'][0]])
            recalled = f"Recalled Experiences:\n{recalled_exp}"
            
        if sol_results['documents'] and sol_results['documents'][0]:
            recalled_sol = "\n".join([f"- Past Solution for '{res['problem']}':\n```python\n{doc}\n```" for doc, res in zip(sol_results['documents'][0], sol_results['metadatas'][0])])
            if "No relevant" in recalled:
                recalled = f"Recalled Solutions:\n{recalled_sol}"
            else:
                recalled += f"\n\nRecalled Solutions:\n{recalled_sol}"
                
        return recalled

MEMORY_MANAGER = MemoryManager()
