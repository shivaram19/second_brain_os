"""Text embedding implementations.

Provides concrete embedders that implement AbstractEmbedder:
  - SentenceTransformersEmbedder: Local, fast, no API key (default)
  - MockEmbedder: Deterministic hash-based embeddings for MVP testing

The default SentenceTransformersEmbedder uses 'all-MiniLM-L6-v2'
(384-dim embeddings), which is accurate enough for semantic search
while running entirely offline.
"""
