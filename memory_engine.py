import os
import time
import chromadb
from chromadb.utils import embedding_functions

PERSIST_DIR = os.path.join(os.path.dirname(__file__), "memory_db")

class MemoryEngine:
    def __init__(self):
        # We use duckdb-parquet by default in modern Chroma, persistent client handles it.
        self.client = chromadb.PersistentClient(path=PERSIST_DIR)
        
        # This will download the ~80MB all-MiniLM-L6-v2 ONNX model on first use
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        self.collections = {
            "general": self.client.get_or_create_collection(
                name="prime_general_memory",
                embedding_function=self.ef
            ),
            "visual": self.client.get_or_create_collection(
                name="prime_visual_memory",
                embedding_function=self.ef
            ),
            "code": self.client.get_or_create_collection(
                name="prime_code_memory",
                embedding_function=self.ef
            )
        }

    def store(self, text: str, category: str = "general", metadata: dict = None):
        """Stores a text string into the specified long-term memory category."""
        col = self.collections.get(category, self.collections["general"])
        
        doc_id = f"mem_{category}_{int(time.time() * 1000)}"
        
        if metadata is None:
            metadata = {}
            
        metadata["timestamp"] = int(time.time())
        metadata["category"] = category
        
        col.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return doc_id

    def recall(self, query: str, category: str = "general", n_results: int = 3) -> list:
        """Retrieves memories relevant to the query from the vector DB."""
        col = self.collections.get(category, self.collections["general"])
        
        if col.count() == 0:
            return []
            
        # Do not ask for more results than exist
        n = min(n_results, col.count())
        
        results = col.query(
            query_texts=[query],
            n_results=n
        )
        
        memories = []
        if results and "documents" in results and results["documents"]:
            # Results are returned as lists of lists
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            ids = results["ids"][0]
            distances = results["distances"][0] if "distances" in results else [0]*len(docs)
            
            for d, m, i, dist in zip(docs, metas, ids, distances):
                memories.append({
                    "id": i,
                    "text": d,
                    "metadata": m,
                    "distance": dist
                })
        return memories

memory_db = MemoryEngine()
