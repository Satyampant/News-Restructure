from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    """Embedding generation service."""
    
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)
    
    def create_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def create_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()