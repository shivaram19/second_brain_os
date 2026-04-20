"""Mock embedder for MVP testing.

Generates deterministic, reproducible embeddings using MD5 hashing of text.
These embeddings are semantically meaningless (random based on hash seed)
but enable testing the ingestion pipeline and RAG engine without downloading
large models or requiring API keys.

Used primarily for unit tests and rapid prototyping. Production systems
should use SentenceTransformersEmbedder or a real cloud API embedder.
"""

import hashlib
import random
from typing import List

from brainos.knowledge.embedding_base import AbstractEmbedder


class MockEmbedder(AbstractEmbedder):
    """Mock embedder using deterministic hashing for reproducible embeddings.

    For MVP, uses hash of text to generate consistent but semantically-meaningless embeddings.
    TODO: Switch to real embedding API (e.g., Hugging Face, Sentence Transformers) later.
    """

    def __init__(self, dim: int = 384):
        """Initialize mock embedder.

        Args:
            dim: Embedding dimension
        """
        self.embedding_dim = dim

    def embed(self, text: str) -> List[float]:
        """Generate deterministic embedding from text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (seeded by hash of text)
        """
        # Use text hash as seed for reproducibility
        hash_obj = hashlib.md5(text.encode())
        seed = int(hash_obj.hexdigest(), 16) % (2**31)

        random.seed(seed)
        embedding = [random.gauss(0, 1) for _ in range(self.embedding_dim)]

        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        embedding = [x / (norm + 1e-8) for x in embedding]

        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts.

        Args:
            texts: Texts to embed

        Returns:
            List of embeddings
        """
        return [self.embed(text) for text in texts]

    def get_embedding_dim(self) -> int:
        """Get embedding dimensionality.

        Returns:
            Dimension of embeddings
        """
        return self.embedding_dim
