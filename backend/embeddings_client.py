"""
Embeddings client for text vectorization
Supports both Ollama and sentence-transformers
"""
from typing import List, Union
from backend.config import get_settings


class EmbeddingsClient:
    """Client for generating text embeddings"""
    
    def __init__(self):
        self.settings = get_settings()
        self.provider = self.settings.EMBEDDING_PROVIDER
        
        if self.provider == "sentence-transformers":
            self._init_sentence_transformer()
        else:
            self._init_ollama()
    
    def _init_ollama(self):
        """Initialize Ollama embeddings"""
        from backend.llm_client import get_ollama_client
        self.client = get_ollama_client()
        self.model = self.settings.OLLAMA_EMBEDDING_MODEL
    
    def _init_sentence_transformer(self):
        """Initialize sentence-transformers"""
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(
            self.settings.SENTENCE_TRANSFORMER_MODEL
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        if self.provider == "ollama":
            return await self.client.embed(text, model=self.model)
        else:
            # sentence-transformers
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if self.provider == "ollama":
            # Ollama doesn't have batch API, process sequentially
            embeddings = []
            for text in texts:
                embedding = await self.client.embed(text, model=self.model)
                embeddings.append(embedding)
            return embeddings
        else:
            # sentence-transformers supports batch encoding
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.settings.EMBEDDING_DIMENSION


# Global embeddings client instance
_embeddings_client = None

def get_embeddings_client() -> EmbeddingsClient:
    """Get or create embeddings client instance"""
    global _embeddings_client
    if _embeddings_client is None:
        _embeddings_client = EmbeddingsClient()
    return _embeddings_client
