"""Sentence Transformers embedder (local, no API key).

Generates dense text embeddings using the 'all-MiniLM-L6-v2' model by default:
  - 384-dimensional embeddings
  - Fast inference on CPU
  - No external API key required
  - Good accuracy for semantic search on personal knowledge bases

This is the production default embedder used by both the ingestion pipeline
and the RAG engine. It supports efficient batch encoding for vault ingestion.
"""

from typing import List

from sentence_transformers import SentenceTransformer

from brainos.knowledge.embedding_base import AbstractEmbedder


class SentenceTransformersEmbedder(AbstractEmbedder):
    """Generate embeddings using Sentence Transformers.

    Uses 'all-MiniLM-L6-v2' by default:
    - Fast and accurate
    - 384-dim embeddings
    - Runs locally (no API key)
    - Good for semantic search
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedder.

        Args:
            model_name: Sentence Transformers model name
        """
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> List[float]:
        """Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently.

        Args:
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_tensor=False, show_progress_bar=False)
        return embeddings.tolist()

    def get_embedding_dim(self) -> int:
        """Get embedding dimensionality.

        Returns:
            Dimension of embeddings
        """
        return self.embedding_dim
